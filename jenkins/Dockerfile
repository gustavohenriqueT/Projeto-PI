# Usar uma imagem base oficial do Jenkins LTS com JDK 17 (recomendado)
FROM jenkins/jenkins:lts-jdk17

# Mudar para o usuário root para instalar pacotes de sistema
USER root

# Instalar dependências necessárias para Docker CLI e Docker Compose
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    software-properties-common && \
    rm -rf /var/lib/apt/lists/*

# Adicionar o repositório oficial do Docker e instalar Docker CLI
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
    $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

# Instalar Docker Compose V2 (plugin)
RUN apt-get update && \
    apt-get install -y docker-compose-plugin && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Voltar para o usuário jenkins padrão da imagem
USER jenkins