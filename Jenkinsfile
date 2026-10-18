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
                        -v trivy-cache:/root/.cache \
                        aquasec/trivy:0.74.0 image \
                        --db-repository ghcr.io/aquasecurity/trivy-db:2 \
                        --db-repository public.ecr.aws/aquasecurity/trivy-db:2 \
                        --image-src docker \
                        --scanners vuln \
                        --severity HIGH,CRITICAL \
                        --ignore-unfixed \
                        --exit-code 1 \
                        --timeout 15m \
                        --no-progress \
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

        stage('Update GitOps Release') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'github-gitops-writer',
                        usernameVariable: 'GIT_USERNAME',
                        passwordVariable: 'GIT_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu
                        set +x

                        gitops_dir="$WORKSPACE/gitops-worktree"
                        askpass="$WORKSPACE/gitops-askpass.sh"

                        cleanup() {
                            rm -rf "$gitops_dir"
                            rm -f "$askpass"
                        }
                        trap cleanup EXIT

                        cat > "$askpass" <<'EOF'
#!/bin/sh
case "$1" in
    *Username*) printf '%s\\n' "$GIT_USERNAME" ;;
    *Password*) printf '%s\\n' "$GIT_TOKEN" ;;
esac
EOF
                        chmod 700 "$askpass"
                        export GIT_ASKPASS="$askpass"
                        export GIT_TERMINAL_PROMPT=0

                        git clone --depth 1 --branch main \
                            https://github.com/equaan/local-guide-booking-gitops.git \
                            "$gitops_dir"

                        cd "$gitops_dir"

                        values_file="apps/local-guide-booking/values.yaml"
                        test -f "$values_file"

                        if ! grep -qE \
                            '^[[:space:]]*repository:[[:space:]]*equaan/local-guide-booking[[:space:]]*$' \
                            "$values_file"; then
                            echo "Expected Local Guide Booking image repository was not found."
                            exit 1
                        fi

                        sed -i \
                            "s|^\\([[:space:]]*tag:[[:space:]]*\\).*|\\1${IMAGE_TAG}|" \
                            "$values_file"

                        grep -qE \
                            "^[[:space:]]*tag:[[:space:]]*${IMAGE_TAG}$" \
                            "$values_file"

                        git config user.name "Jenkins CI"
                        git config user.email "jenkins@local-guide-booking.invalid"

                        if git diff --quiet -- "$values_file"; then
                            echo "GitOps chart already uses ${IMAGE_REF}."
                            exit 0
                        fi

                        git add "$values_file"
                        git commit -m "deploy: local-guide-booking ${IMAGE_TAG}"
                        git push origin main
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

