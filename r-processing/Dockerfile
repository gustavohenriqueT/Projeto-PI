FROM rocker/tidyverse:4.3.0

# Instala dependências do sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    libudunits2-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia e instala pacotes R
COPY requirements.R .
RUN Rscript requirements.R

# Copia o script de análise 
COPY analysis.R .

CMD ["Rscript", "analysis.R"]