FROM rocker/tidyverse:4.3.0
WORKDIR /app
COPY requirements.R .
RUN Rscript requirements.R
COPY analysis.R .
CMD ["Rscript", "analysis.R"]