pipeline{

    agent any

    parameters {
        string(name: 'APP_ENV', defaultValue: 'dev', description: 'The target environment for the application pipeline')
    }


    stages{

        stage('Checkout'){
            steps{
                // Checks out source code from the configured source control management (SCM)
                checkout scm
            }
        }

        stage('Build') {
            steps {
                echo "The selected application environment is: ${params.APP_ENV}"
                echo 'Creating virtual environment and installing dependencies...'
                sh '''
                    set -eu
                    python3 -m venv .venv-ci
                    . .venv-ci/bin/activate
                    python3 -m pip install --upgrade pip
                    pip install -r requirements-dev.txt
                '''
            }
        }
        
        stage('Test'){
            steps{
                script{
                    echo 'Running tests and collecting coverage metrics...'
                    sh '''
                        set -eu
                        mkdir -p test-results
                        . .venv-ci/bin/activate

                        #Run tests, output JUnit XML, and calculate coverage for the app directory
                        python -m pytest --cov=app --cov-report=xml:coverage.xml --junitxml=test-results/pytest.xml
                    '''
                }
            }
        }

        stage('E2E Testing'){
            steps{
                echo 'Launching a temporary Flask app and running the Selenium E2E suite...'
                sh '''
                    set -eu
                    . .venv-ci/bin/activate
                    mkdir -p test-results

                    e2e_database="$WORKSPACE/ci-e2e.db"
                    rm -f "$e2e_database"
                    export APP_ENV=dev
                    export DATABASE_URL="sqlite:///$e2e_database"
                    rm -rf test-artifacts

                    python -m flask --app wsgi db upgrade
                    python -m gunicorn --bind 0.0.0.0:8000 --workers 1 wsgi:app \
                        > test-results/e2e-app.log 2>&1 &
                    flask_pid=$!

                    cleanup() {
                        if kill -0 "$flask_pid" 2>/dev/null; then
                            kill "$flask_pid"
                            wait "$flask_pid" || true
                        fi
                    }
                    trap cleanup EXIT

                    for attempt in $(seq 1 20); do
                        if python -c 'from urllib.request import urlopen; urlopen("http://localhost:8000/health", timeout=1)' >/dev/null 2>&1; then
                            break
                        fi
                        if [ "$attempt" -eq 20 ]; then
                            cat test-results/e2e-app.log
                            exit 1
                        fi
                        sleep 1
                    done

                    BASE_URL=http://jenkins:8000 \
                    SELENIUM_REMOTE_URL=http://selenium-chrome:4444/wd/hub \
                    E2E_HEADLESS=1 \
                    python -m pytest -m e2e --junitxml=test-results/e2e-pytest.xml
                '''
            }
        }

        stage('SonarQube Analysis'){
            steps{
                script{
                    echo "Executing SonarQube Scanner Code Analysis..."

                    //1. Resolve the scanner path from global Tool configuration
                    def scannerHome = tool name: 'sonar-scanner', type: 'hudson.plugins.sonar.SonarRunnerInstallation'

                    //2. Inject URL and Token from System Configuration, runnning analysis from the tool path
                    withSonarQubeEnv('sonarqube-local'){
                        sh """
                            set -eu
                            # Run the tool version flag check first to output into console logs
                            "${scannerHome}/bin/sonar-scanner" --version

                            # Execute code scanner (automatically reads sonar-project.properties)
                            "${scannerHome}/bin/sonar-scanner"
                        """
                    }
                }
            }
        }

        stage('SonarQube Quality Gate'){
            options{
                // Applies a 10 min timeout so Jenkins won't hang indefinitely if networking breaks
                timeout(time:10, unit:'MINUTES')
            }
            steps{
                echo 'Waiting for SonarQube Quality Gate webhook status report...'

                waitForQualityGate abortPipeline: true
                echo 'SonarQube Quality Gate passed.'
            }
        }

        stage('Build Container Image') {
            steps {
                script {
                    def gitSha = sh(
                        script: 'git rev-parse --short=12 HEAD',
                        returnStdout: true
                    ).trim()

                    env.IMAGE_TAG = "v0.1.0-${env.BUILD_NUMBER}-${gitSha}"
                    env.IMAGE_REF = "equaan/local-guide-booking:${env.IMAGE_TAG}"

                    echo "Building immutable image: ${env.IMAGE_REF}"

                    sh '''
                        set -eu
                        docker build --pull -t "$IMAGE_REF" .
                        docker image inspect "$IMAGE_REF" --format '{{.Id}}'
                    '''
                }
            }
        }

        stage('Trivy Image Scan') {
            steps {
                echo "Scanning ${env.IMAGE_REF} for fixable HIGH and CRITICAL vulnerabilities..."

                sh '''
                    set -eu
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock:ro \
                        aquasec/trivy:0.74.0 image \
                        --image-src docker \
                        --scanners vuln \
                        --severity HIGH,CRITICAL \
                        --ignore-unfixed \
                        --exit-code 1 \
                        "$IMAGE_REF"
                '''
            }
        }

        stage('Push Container Image') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-local-guide-booking',
                        usernameVariable: 'DOCKERHUB_USERNAME',
                        passwordVariable: 'DOCKERHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu
                        trap 'docker logout || true' EXIT

                        printf '%s' "$DOCKERHUB_TOKEN" | \
                            docker login --username "$DOCKERHUB_USERNAME" --password-stdin

                        docker push "$IMAGE_REF"
                    '''
                }
            }
        }

        stage('Package'){
            steps{
                echo 'Archiving the build and test artifacts...'
                archiveArtifacts artifacts: 'requirements.lock, pyproject.toml, sonar-project.properties', allowEmptyArchive: false
            }
        }     
    }

    post{
        always{
            junit allowEmptyResults: true, testResults: 'test-results/*.xml'
            archiveArtifacts artifacts: 'test-results/*.xml,test-results/e2e-app.log,coverage.xml,test-artifacts/*.png', allowEmptyArchive: true
        }
    }
}

