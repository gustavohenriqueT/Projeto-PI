pipeline {
    agent any

    stages {
        stage('Clean Docker Environment') {
            steps {
                script {
                    echo 'Stopping and removing existing Docker containers (excluding Jenkins)...'
                    // Usar bat para Windows e caminho completo do docker-compose
                    bat '"C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker-compose.exe" down --remove-orphans || exit 0'
                }
            }
        }
        
        stage('Build and Run Docker Compose Services') {
            steps {
                script {
                    echo 'Building and starting Docker Compose services...'
                    bat '"C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker-compose.exe" up -d --build postgres'
                    
                    echo 'Waiting for postgres to be healthy...'
                    // Espera com timeout para evitar loops infinitos
                    bat 'for /l %%x in (1,1,30) do ( "C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker-compose.exe" exec -T postgres pg_isready -U admin -d transport_db && exit /b 0 || ping -n 2 127.0.0.1>nul ) && exit /b 1'
                    
                    echo 'Starting other services...'
                    bat '"C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker-compose.exe" up -d --build --force-recreate data-generator r-processing data-warehouse spark-master spark-worker web-dashboard'

                    echo 'Waiting for data-generator to complete...'
                    bat '"C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker-compose.exe" wait data-generator'

                    echo 'Waiting for r-processing to complete...'
                    bat '"C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker-compose.exe" wait r-processing'

                    echo 'Waiting for data-warehouse to complete...'
                    bat '"C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker-compose.exe" wait data-warehouse'
                }
            }
        }
        
        stage('Run Spark Analysis') {
            steps {
                script {
                    echo 'Running Spark Analysis scripts...'
                    bat '"C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker-compose.exe" exec -T spark-master /opt/bitnami/spark/bin/spark-submit /app/spark_analysis.py'
                    bat '"C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker-compose.exe" exec -T spark-master /opt/bitnami/spark/bin/spark-submit /app/clustering.py'
                }
            }
        }
        
        stage('Check Web Dashboard Status') {
            steps {
                script {
                    echo 'Waiting for Web Dashboard to be fully ready...'
                    sleep 30
                    echo 'Checking if Web Dashboard is accessible...'
                    bat '"C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker-compose.exe" exec -T web-dashboard curl -f http://localhost:5000'
                }
            }
        }
        
        stage('Show Final Docker Logs (Optional)') {
            steps {
                script {
                    echo 'Showing logs for key services...'
                    bat '"C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker-compose.exe" logs --tail 50 data-generator r-processing data-warehouse web-dashboard'
                }
            }
        }
    }
    
    post {
        always {
            echo 'Pipeline finished.'
        }
        failure {
            echo 'Pipeline failed. Check logs for details.'
            script {
                bat '"C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker-compose.exe" logs --tail 200 > pipeline_failure_logs.txt || exit 0'
                archiveArtifacts artifacts: 'pipeline_failure_logs.txt', fingerprint: true
            }
        }
    }
}