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
                echo 'Running tests...'
                sh '''
                    set -eu
                    mkdir -p test-results
                    . .venv-ci/bin/activate
                    python -m pytest --junitxml=test-results/pytest.xml
                '''
            }
        }

        stage('Package'){
            steps{
                echo 'Archiving the build and test artifacts...'
                archiveArtifacts artifacts: 'requirements.lock, pyproject.toml, test-results/pytest.xml', allowEmptyArchive: false
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
    }

    post{
        always{
            junit allowEmptyResults: true, testResults: 'test-results/pytest.xml'
        }
    }
}

