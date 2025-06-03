# Análise e Limpeza de Dados de Transporte Público

# 1. Instalação e Carregamento de Pacotes --------------------------------------
if (!require("pacman")) install.packages("pacman")
pacman::p_load(
  dplyr, # Manipulação de dados
  lubridate, # Trabalhar com datas
  stringr, # Manipulação de strings
  ggplot2, # Visualização de dados
  scales, # Formatação de escalas
  tidyr, # Dados tidy
  DescTools # Ferramentas descritivas
)

# 2. Configuração de Caminhos -------------------------------------------------
caminho_entrada <- "/app/data/transport_data.csv"
caminho_saida <- "/app/data/transport_dataL.csv"
caminho_graficos <- "/app/web-dashboard/assets/graficos.png"

# 3. Leitura dos Dados --------------------------------------------------------
cat("\n[1/7] Lendo arquivo de dados...\n")
dados <- read.csv(
  file = caminho_entrada,
  header = TRUE,
  sep = ",",
  stringsAsFactors = FALSE,
  encoding = "UTF-8"
)

# Verificação inicial
cat("Dimensões iniciais:", dim(dados), "\n")
cat("Colunas:", names(dados), "\n")

# 4. Padronização de Colunas --------------------------------------------------
cat("\n[2/7] Padronizando nomes de colunas...\n")
colnames(dados) <- colnames(dados) %>%
  tolower() %>%
  str_replace_all(" ", "_")

# 5. Limpeza e Transformação --------------------------------------------------
cat("\n[3/7] Realizando limpeza inicial...\n")
dados <- dados %>%
  mutate(
    # Padronização de texto
    id_veiculo = str_to_lower(str_trim(id_veiculo)),
    linha = str_to_lower(str_trim(linha)),
    situacao = str_to_lower(str_trim(situacao)),

    # Conversão de tipos
    data_hora = parse_date_time(data_hora, orders = c("ymd HMS", "ymd HM", "dmy HMS", "dmy HM")),
    numero_passageiros = as.integer(numero_passageiros),

    # Tratamento de valores inválidos
    numero_passageiros = ifelse(numero_passageiros < 0, NA, numero_passageiros)
  ) %>%
  # Remoção de NAs
  filter(!is.na(numero_passageiros)) %>%
  drop_na()

# 6. Tratamento de Outliers ---------------------------------------------------
cat("\n[4/7] Tratando outliers...\n")

# Função auxiliar para detecção de outliers
remove_outliers <- function(x) {
  q <- quantile(x, probs = c(0.25, 0.75), na.rm = TRUE)
  iqr <- q[2] - q[1]
  limites <- c(q[1] - 1.5 * iqr, q[2] + 1.5 * iqr)
  x >= limites[1] & x <= limites[2]
}

# Função para winsorização
winsorizar <- function(x, probs = c(0.01, 0.99)) {
  quantiles <- quantile(x, probs = probs, na.rm = TRUE)
  x[x < quantiles[1]] <- quantiles[1]
  x[x > quantiles[2]] <- quantiles[2]
  x
}

# Aplicação das funções
dados <- dados %>%
  filter(
    remove_outliers(as.numeric(tempo_viagem_minutos)),
    remove_outliers(as.numeric(numero_passageiros))
  ) %>%
  mutate(
    numero_passageiros = winsorizar(numero_passageiros),
    tempo_viagem_minutos = winsorizar(tempo_viagem_minutos),
    hora = winsorizar(hora)
  ) %>%
  # Filtro geográfico do Brasil
  filter(
    between(latitude, -34, 5),
    between(longitude, -74, -34)
  )

# 7. Análise Exploratória -----------------------------------------------------
cat("\n[5/7] Gerando análises exploratórias...\n")

# Gráficos
png(caminho_graficos, width = 1000, height = 500)
par(mfrow = c(1, 2))
boxplot(dados$tempo_viagem_minutos,
  main = "Tempo de Viagem (minutos)\nApós Tratamento",
  col = "skyblue",
  ylab = "Minutos"
)
boxplot(dados$numero_passageiros,
  main = "Número de Passageiros\nApós Tratamento",
  col = "lightgreen",
  ylab = "Quantidade"
)
dev.off()

# Sumário estatístico
cat("\nResumo estatístico final:\n")
print(summary(dados))

# 8. Exportação dos Dados -----------------------------------------------------
cat("\n[6/7] Salvando dados processados...\n")
write.csv(
  dados,
  file = caminho_saida,
  row.names = FALSE,
  fileEncoding = "UTF-8"
)

# 9. Mensagem Final -----------------------------------------------------------
cat("\n[7/7] Processamento concluído com sucesso!\n")
cat("----------------------------------------\n")
cat("Arquivo de saída:", caminho_saida, "\n")
cat("Gráficos salvos em:", caminho_graficos, "\n")
cat("Linhas processadas:", nrow(dados), "\n")
cat("Colunas processadas:", ncol(dados), "\n")
cat("----------------------------------------\n")

# Limpeza final
rm(list = ls())
gc()
