FROM bitnami/spark:3.4
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN curl -L https://jdbc.postgresql.org/download/postgresql-42.6.0.jar -o /opt/bitnami/spark/jars/postgresql-jdbc.jar
COPY . .