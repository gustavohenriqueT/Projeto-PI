library(DBI)
library(dplyr)

con <- dbConnect(
  RPostgres::Postgres(),
  dbname = "transport_db",
  host = "postgres",
  user = "admin",
  password = "password"
)

# Análise estatística
dados <- dbGetQuery(con, "SELECT * FROM transport_stats")

print("Média de passageiros por linha:")
print(dados)

# Visualização (salvar em arquivo se necessário)
png("/data/r_plot.png")
barplot(dados$avg_passengers, names.arg = dados$line)
dev.off()