# Usar imagem base do Jenkins com JDK 17
FROM jenkins/jenkins:lts-jdk17

USER root

# Instalar dependências básicas
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    software-properties-common \
    sudo

# Adicionar chave GPG e repositório oficial do Docker
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
    https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
    > /etc/apt/sources.list.d/docker.list

# Instalar Docker CLI e Docker Compose plugin
RUN apt-get update && apt-get install -y \
    docker-ce-cli \
    docker-compose-plugin && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ✅ Criar o grupo docker (se não existir) e adicionar o usuário jenkins
RUN groupadd -f docker && usermod -aG docker jenkins

USER jenkins
