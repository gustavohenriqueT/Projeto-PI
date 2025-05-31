# Projeto: Análise de Dados de Transporte Público

## Equipe

| Nome Completo | RA | Função |
|--------------|------|----------------|
| Geovana Neuberger Sorg | 22001825 | Membro da equipe |
| Fernando Pagliarini Furlanetto | 22000293 | Membro da equipe |
| Gustavo Henrique Tomaz da Silva | 22001161 | Scrum Master (SM) |
| Lucas de Oliveira Barreiro | 22000100 | Product Owner (PO) |
| Diogo Alves Daloca | 24001784 | Membro da equipe |

## Descrição do Projeto

Este projeto tem como objetivo analisar grandes volumes de dados sobre o transporte público de uma cidade, utilizando técnicas de Big Data para identificar padrões de uso, horários de pico, eficiência das rotas e possíveis melhorias no sistema.

Utilizando Python, R, Postgree e Docker, processaremos de dados simulado para criar visualizações e relatórios que possam auxiliar na tomada de decisões.

## Principais Funcionalidades

### Coleta de Dados:
- Dataset simulado

### Armazenamento e Processamento:
- Utilização do Postgree para armazenar grandes volumes de dados não estruturados.
- Tratamento e análise de dados com Python e R.
- Implementação de pipelines automatizados com Ansible e Docker.
- Aplicação de técnicas de Big Data para identificar padrões.

### Visualização e Relatórios:
- Gráficos interativos para demonstrar horários de pico e eficiência das rotas.
- Identificação de pontos de congestionamento e atrasos recorrentes.
- Sugestões de otimização com base nos dados coletados.

## Funções e Responsabilidades

### Scrum Master (SM) - Gustavo Henrique Tomaz da Silva
- Líder e facilitador do grupo
- Atribuição de papéis e responsabilidades
- Definição de datas para reuniões internas
- Manutenção do repositório GitHub junto com o PO

### Product Owner (PO) - Lucas de Oliveira Barreiro
- Criação e manutenção do cronograma de entregas (Trello, Jira, Notion, GitHub Projects)
- Acompanhamento do progresso do time
- Manutenção do repositório GitHub junto com o SM

## Tecnologias Utilizadas

### Linguagens de Programação:
- Python
- R

### Banco de Dados:
- PostgreSQL

### Ferramentas de Big Data:
- Pandas
- Apache Spark
- Flask

### Ferramentas de Gerenciamento e Automatização:
- Jekins
- Docker

### Visualização de Dados:
- Matplotlib
- Seaborn
- ggplot2

## 🚀 Como Instalar e Executar o Projeto

Este projeto utiliza **Docker** e **Docker Compose** para orquestrar diversos serviços de forma consistente.

### ✅ Pré-requisitos

Antes de começar, instale:

- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/)
- Editor de código (VS Code, Sublime, etc.)
- Navegador Web (Chrome, Firefox, etc.)

---

### 📁 1. Clonar o Repositório

```bash
git clone https://github.com/gustavohenriqueT/Projeto-PI.git
cd Projeto-PI
```

---

### 🔐 2. Variáveis de Ambiente (Opcional)

Se necessário, crie um arquivo `.env` na raiz do projeto para configurar variáveis sensíveis. Neste projeto, credenciais padrão estão no `docker-compose.yml` apenas para desenvolvimento.

---

### 🏗️ 3. Construir e Iniciar os Serviços

Execute na raiz do projeto:

```bash
docker-compose up --build -d
```

- `--build`: Reconstrói as imagens.
- `-d`: Executa os serviços em segundo plano.

---

### 🌐 4. Acessar os Serviços

| Serviço                  | URL/Info                                      |
|--------------------------|-----------------------------------------------|
| **Dashboard Dash**       | [http://localhost:5000](http://localhost:5000) |
| **Spark Master UI**      | [http://localhost:8081](http://localhost:8081) |
| **PostgreSQL**           | `localhost:5432` (DB: `transport_db`, User: `admin`, Pass: `password`) |
| **Jenkins**              | [http://localhost:18080](http://localhost:18080) |
| **Grafana**              | [http://localhost:3000](http://localhost:3000) <br> Login: `admin` / `admin` |

---

### 📄 5. Ver Logs dos Contêineres

Logs de um serviço específico:

```bash
docker-compose logs -f <nome_do_servico>
```

Logs de todos os serviços:

```bash
docker-compose logs -f
```

---

### 🛑 6. Parar os Serviços

```bash
docker-compose down
```

Remover volumes (apaga dados persistentes):

```bash
docker-compose down -v
```

---

### 🧠 Estrutura do Pipeline de Dados

1. `postgres` inicia.
2. `data-generator` gera `transport_data.csv`.
3. `r-processing` processa e gera `transport_dataL.csv`.
4. Paralelamente:
   - `data-warehouse` popula o PostgreSQL.
   - `hadoop-simulations` roda simulações.
   - `clustering-analysis` realiza clusterizações.
5. `spark-submit-job` executa análises com Spark.
6. `web-dashboard` exibe resultados.
7. `jenkins` e `grafana` rodam como serviços independentes.

---

