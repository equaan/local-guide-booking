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

        stage('Package'){
            steps{
                echo 'Archiving the build and test artifacts...'
                archiveArtifacts artifacts: 'requirements.lock, pyproject.toml, sonar-project.properties', allowEmptyArchive: false
            }
        }

        stage('Cluster Check'){
            steps{
                echo 'Checking cluster namespace status...'

                withCredentials([file(credentialsId: 'kubeconfig-docker-desktop', variable: 'KUBECONFIG')]) {
                    sh '''
                        set -eu
                        kubectl --kubeconfig="$KUBECONFIG" -n lgb-dev get namespace lgb-dev
                    '''
                }
            }
        }


        stage('Deploy'){
            steps{
                echo "Processing deployment manifests for APP_ENV=${params.APP_ENV}..."
                withCredentials([file(credentialsId: 'kubeconfig-docker-desktop', variable: 'KUBECONFIG')]){
                script{
                    // Determine replica count dynamically based on the parameter input
                    def replicas = (params.APP_ENV == 'dev') ? '1' : '2'
                    echo "Configuring deployment scaling to: ${replicas} replica(s)"

                    sh """
                        set -eu
                        # Replace placeholder with calculated count and apply manifest
                        sed "s/__REPLICAS__/${replicas}/g" deployment.yml > deployment-generated.yml
                        kubectl --kubeconfig="\$KUBECONFIG" apply -f deployment-generated.yml

                    
                        rm -f deployment-generated.yml
                    """
                }
            }
            }
        }

        stage('Rollout Verification'){
            steps{
                echo "Verifying deployment health status..."
                withCredentials([file(credentialsId: 'kubeconfig-docker-desktop', variable: 'KUBECONFIG')]) {
                    sh '''
                        set -eu
                        # The pipeline block will explicitly wait for active containers to pass probes
                        kubectl --kubeconfig="$KUBECONFIG" -n lgb-dev rollout status deployment/local-guide-booking --timeout=90s
                    '''
                }
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

