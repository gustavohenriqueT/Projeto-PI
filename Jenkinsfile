pipeline {
    agent any // Ou um agente específico se você tiver configurações mais complexas

    environment {

    }

    stages {
        stage('Checkout SCM') {
            steps {
                echo 'Baixando código do repositório...'
                // O Jenkins geralmente clona o repositório automaticamente quando configurado para "Pipeline script from SCM"
                script {
                    def commit = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
                    echo "Código na revisão Git: ${commit}"
                }
            }
        }

        stage('Limpar Ambiente Docker Anterior') {
            steps {
                echo 'Parando e removendo contêineres Docker de execuções anteriores (se existirem)...'
                // Usar || true para evitar que o pipeline falhe se não houver nada para parar/remover
                sh 'docker-compose down --remove-orphans || true'
            }
        }

        stage('Construir Imagens Docker') {
            steps {
                echo 'Construindo todas as imagens Docker definidas no docker-compose.yml...'
                // --no-cache pode ser útil para garantir que tudo seja reconstruído do zero,
                // mas pode tornar o build mais lento. Remova se preferir usar o cache do Docker.
                sh 'docker-compose build --no-cache'
            }
        }

        stage('Executar Pipeline de Dados e Análises') {
            steps {
                echo 'Iniciando serviços de dados e análise em segundo plano...'
                // Sobe os serviços na ordem definida pelas dependências no docker-compose.yml
                // O -d executa em modo detached (background)
                sh 'docker-compose up -d postgres data-generator r-processing data-warehouse hadoop-simulations clustering-analysis spark-master spark-worker spark-submit-job'
                
                echo 'Aguardando a conclusão dos jobs de dados e análise...'
.   
                echo "Pipeline de dados e análises iniciado. O dashboard dependerá da conclusão deles."
            }
        }
        
        stage('Implantar/Atualizar Web Dashboard') {
            steps {
                echo 'Iniciando/Atualizando o serviço Web Dashboard...'
                // Garante que a dashboard seja iniciado ou recriado se necessário,
                // após seus serviços dependentes terem completado (conforme docker-compose.yml)
                sh 'docker-compose up -d web-dashboard'
                
                // Adicionar uma pequena pausa para dar tempo ao dashboard iniciar completamente
                echo 'Aguardando o dashboard iniciar...'
                sleep(time: 20, unit: 'SECONDS')
            }
        }

        stage('Verificar Status do Dashboard (Opcional)') {
            steps {
                echo 'Verificando se o dashboard está acessível...'

                sh 'curl --fail --silent http://web-dashboard:5000 || curl --fail --silent http://localhost:5000 || echo "Dashboard não acessível ou teste falhou"'
                echo "Verificação do dashboard concluída (verifique a saída do curl acima)."
            }
        }
    }

    post {
        always {
            echo 'Pipeline do Jenkins finalizado.'
            
        }
        success {
            echo 'Pipeline concluído com SUCESSO!'
        }
        failure {
            echo 'Pipeline FALHOU. Verifique os logs do console do Jenkins para detalhes.'
            // Mostrar logs dos serviços que podem ter falhado
            script {
                def servicesToCheck = ['data-generator', 'r-processing', 'data-warehouse', 'hadoop-simulations', 'clustering-analysis', 'spark-submit-job', 'web-dashboard']
                servicesToCheck.each { service ->
                    try {
                        echo "Últimos logs de ${service} (em caso de falha):"
                        sh "docker-compose logs --tail 150 ${service} || true"
                    } catch (any) {
                        echo "Não foi possível obter logs de ${service}."
                    }
                }
            }
        }
    }
}