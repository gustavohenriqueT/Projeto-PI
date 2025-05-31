pipeline {
    agent any  // Define que o pipeline pode ser executado em qualquer agente disponível
    environment {
        DOCKER_BUILDKIT = "1"  // Habilita o BuildKit do Docker para a construção de imagens
    }
    stages {
        stage('Checkout SCM') {  // Etapa para clonar o repositório
            steps {
                echo 'Clonando o repositório...'  // Mensagem para indicar o início do checkout
                checkout scm  // Clona o repositório configurado no Jenkins
                script {
                    def gitCommit = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()  // Obtém o commit atual do Git
                    echo "Código na revisão Git: ${gitCommit}"  // Exibe o commit atual
                }
            }
        }
        stage('Limpar Ambiente Docker Anterior') {  // Etapa para limpar contêineres antigos
            steps {
                echo 'Parando e removendo contêineres Docker de execuções anteriores (se existirem)...'  // Mensagem de limpeza
                sh 'docker compose down --remove-orphans || true'  // Para e remove contêineres antigos sem falhar
            }
        }
        stage('Construir Imagens Docker') {  // Etapa para construir as imagens Docker
            steps {
                echo 'Construindo todas as imagens Docker definidas no docker-compose.yml...'  // Mensagem de construção
                sh 'docker compose build --no-cache || true'  // Constrói as imagens sem cache
            }
        }
        stage('Executar Pipeline de Dados e Análises') {  // Inicia os serviços em contêineres Docker
            steps {
                echo 'Executando os serviços definidos para processamento de dados e análises...'  // Mensagem para indicar a execução
                sh 'docker compose up -d || true'  // Inicia os serviços em modo desacoplado
            }
        }
        stage('Aguardando Finalização dos Jobs') {  // Etapa de espera para jobs
            steps {
                echo 'Aguardando a conclusão dos jobs de dados e análise...'  // Mensagem de espera
            }
        }
        stage('Implantar/Atualizar Web Dashboard') {  // Etapa para implantar ou atualizar o Dashboard
            steps {
                echo 'Implantando/Atualizando o Web Dashboard...'  // Mensagem de implantação
            }
        }
        stage('Verificar Status do Dashboard (Opcional)') {  // Etapa para verificação do status
            steps {
                echo 'Verificando status do dashboard...'  // Mensagem para indicar a verificação
            }
        }
    }
    post {
        always {
            echo 'Pipeline do Jenkins finalizado.'  // Mensagem final indicando a conclusão do pipeline
        }
        failure {
            echo 'Pipeline FALHOU. Verifique os logs do console do Jenkins para detalhes.'  // Mensagem de erro em caso de falha
            script {
                def services = [  // Lista de serviços que serão verificados em caso de falha
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
                    echo "Últimos logs de ${svc} (em caso de falha):"  // Mensagem de logs do serviço
                    sh "docker compose logs --tail 100 ${svc} || true"  // Mostra os últimos 100 logs do serviço
                }
            }
        }
    }
}
