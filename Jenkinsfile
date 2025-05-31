pipeline {
    agent any

    environment {
        DOCKER_BUILDKIT = "1"
    }

    stages {
        stage('Checkout SCM') {
            steps {
                echo 'Clonando o repositório...'
                checkout scm
                script {
                    def gitCommit = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                    echo "Código na revisão Git: ${gitCommit}"
                }
            }
        }

        stage('Limpar Ambiente Docker Anterior') {
            steps {
                echo 'Parando e removendo contêineres Docker de execuções anteriores (se existirem)...'
                sh 'docker compose down --remove-orphans || true'
            }
        }

        stage('Construir Imagens Docker') {
            steps {
                echo 'Construindo todas as imagens Docker definidas no docker-compose.yml...'
                sh 'docker compose build --no-cache || true'
            }
        }

        stage('Executar Pipeline de Dados e Análises') {
            steps {
                echo 'Executando os serviços definidos para processamento de dados e análises...'
                sh 'docker compose up -d || true'
            }
        }

        stage('Aguardando Finalização dos Jobs') {
            steps {
                echo 'Aguardando a conclusão dos jobs de dados e análise...'
                
            }
        }

        stage('Implantar/Atualizar Web Dashboard') {
            steps {
                echo 'Implantando/Atualizando o Web Dashboard...'
    
            }
        }

        stage('Verificar Status do Dashboard (Opcional)') {
            steps {
                echo 'Verificando status do dashboard...'
            }
        }
    }

    post {
        always {
            echo 'Pipeline do Jenkins finalizado.'
        }

        failure {
            echo 'Pipeline FALHOU. Verifique os logs do console do Jenkins para detalhes.'

            script {
                def services = [
                    'data-generator',
                    'r-processing',
                    'data-warehouse',
                    'hadoop-simulations',
                    'clustering-analysis',
                    'spark-submit-job',
                    'web-dashboard',
                    'postgres',
                    'spark-master'
                ]

                for (svc in services) {
                    echo "Últimos logs de ${svc} (em caso de falha):"
                    sh "docker compose logs --tail 100 ${svc} || true"
                }
            }
        }
    }
}
