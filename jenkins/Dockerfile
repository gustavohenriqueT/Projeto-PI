# Use a imagem oficial do Jenkins LTS
FROM jenkins/jenkins:lts-jdk11

# Mudar para o usuário root para instalar o git e configurar
USER root

# Instalar Git e jq (jq é útil para pipelines do Jenkins com Docker)
RUN apt-get update \
    && apt-get install -y --no-install-recommends git jq \
    && rm -rf /var/lib/apt/lists/*

# Voltar para o usuário jenkins
USER jenkins

# Copiar plugins customizados (se houver)
# COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
# RUN /usr/local/bin/install-plugins.sh < /usr/share/jenkins/ref/plugins.txt

# Definir a porta padrão do Jenkins
EXPOSE 8080
EXPOSE 50000

# Comando padrão para iniciar o Jenkins
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/jenkins.sh"]