pipeline {
    agent any // Roda em qualquer agente Jenkins disponível

    // environment { // Removido ou comente se não for usar variáveis de ambiente globais
        // Se precisar de variáveis de ambiente, defina-as aqui:
        // Exemplo:
        // DOCKER_COMPOSE_VERSION = "2.27.0"
    // }

    stages {
        stage('Checkout SCM') {
            steps {
                echo 'Clonando o repositório...'
                // O Jenkins já clona o repositório automaticamente se configurado para "Pipeline script from SCM"
                script {
                    def commit = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
                    echo "Código na revisão Git: ${commit}"
                }
            }
        }

        stage('Limpar Ambiente Docker Anterior') {
            steps {
                echo 'Parando e removendo contêineres Docker de execuções anteriores (se existirem)...'
                sh 'docker-compose down --remove-orphans || true'
            }
        }

        stage('Construir Imagens Docker') {
            steps {
                echo 'Construindo todas as imagens Docker definidas no docker-compose.yml...'
                sh 'docker-compose build --no-cache'
            }
        }

        stage('Executar Pipeline de Dados e Análises') {
            steps {
                script { // <--- Adicionar bloco script aqui
                    echo 'Iniciando serviços de dados e análise em segundo plano...'
                    sh 'docker-compose up -d postgres data-generator r-processing data-warehouse hadoop-simulations clustering-analysis spark-master spark-worker spark-submit-job'
                    
                    echo 'Aguardando conclusão dos jobs de dados e análise...' // <--- Esta linha agora está dentro do script
                    // A orquestração principal da espera é feita pelo depends_on do docker-compose
                    // para o serviço web-dashboard. Não é estritamente necessário esperar aqui no Jenkinsfile
                    // se as dependências do docker-compose estiverem corretas para o dashboard.
                    echo "Pipeline de dados e análises iniciado."
                }
            }
        }
        
        stage('Implantar/Atualizar Web Dashboard') {
            steps {
                script { // <--- Adicionar bloco script aqui
                    echo 'Iniciando/Atualizando o serviço Web Dashboard...'
                    sh 'docker-compose up -d web-dashboard'
                    
                    echo 'Aguardando o dashboard iniciar...'
                    sleep(time: 20, unit: 'SECONDS') 
                }
            }
        }

        stage('Verificar Status do Dashboard (Opcional)') {
            steps {
                script { // <--- Adicionar bloco script aqui
                    echo 'Verificando se o dashboard está acessível...'
                    // Tenta acessar via nome do serviço (se o Jenkins estiver na mesma rede Docker)
                    // ou localhost (se o Jenkins estiver acessando as portas mapeadas no host)
                    sh 'curl --fail --silent http://web-dashboard:5000 || curl --fail --silent http://localhost:5000 || echo "WARN: Dashboard não acessível ou teste de curl falhou."'
                    echo "Verificação do dashboard concluída."
                }
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
            script {
                def servicesToCheck = ['data-generator', 'r-processing', 'data-warehouse', 'hadoop-simulations', 'clustering-analysis', 'spark-submit-job', 'web-dashboard', 'postgres', 'spark-master']
                servicesToCheck.each { service ->
                    try {
                        echo "Últimos logs de ${service} (em caso de falha):"
                        sh "docker-compose logs --tail 100 ${service} || true"
                    } catch (any) {
                        echo "Não foi possível obter logs de ${service}."
                    }
                }
            }
        }
    }
}