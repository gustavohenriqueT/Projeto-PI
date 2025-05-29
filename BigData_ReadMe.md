# 📊 Análise Preditiva e Descritiva do Transporte Público

## ✅ Descrição do Projeto

Este projeto visa analisar dados de transporte público para prever horários de pico, identificar padrões no fluxo de passageiros e oferecer insights para a melhoria do sistema de transporte.

O pipeline do projeto foi construído com foco em integração de dados, pré-processamento eficiente e aplicação de modelos de Machine Learning, além de visualizações interativas para suporte a decisões.

---

## 🚀 Tecnologias Utilizadas

- **Pandas** e **NumPy**: manipulação e análise de dados.
- **Seaborn** e **Plotly**: visualizações interativas e estáticas.
- **SQLite**: Data Warehouse (DW).
- **Google Drive**: Data Lake, para armazenamento intermediário.
- **scikit-learn**: modelagem preditiva e clusterização.
- **NLTK**: técnicas de Processamento de Linguagem Natural (PLN).
- **Spark** e **Hadoop**: processamento distribuído e escalável.

---

## 🗄️ Arquitetura de Dados

- **Data Lake**: armazenamento bruto dos datasets no Google Drive.
- **ETL**: pipeline de extração, transformação e carga com `pandas` e `sqlite3`.
- **Data Warehouse**: modelo estrela com:
  - Tabelas dimensão: `dim_linha`, `dim_onibus`
  - Tabela fato: `fato_transito`
- **Visualização do esquema**: grafo interativo representando os relacionamentos.

---

## 🛠️ Processamento de Linguagem Natural (PLN)

O PLN foi essencial para tratar informações derivadas de atributos textuais.

**Etapas aplicadas**:
- **Tokenização**: separação dos textos em palavras individuais.
- **Remoção de Stopwords**: eliminação de termos irrelevantes.
- **Vetorização com TF-IDF**: conversão do texto em vetores numéricos.
- **Análise de padrões**: investigação das relações ocultas entre atributos concatenados.

---

## 🤖 Modelagem de Machine Learning

### ✅ Modelos aplicados

- **Random Forest**  
  Modelo supervisionado para classificar horários de pico, baseado em:
  - Hora
  - Número de Passageiros
  - Tempo de Viagem  
  ✅ *Boa acurácia, eficiente para previsão.*

- **KMeans**  
  Clusterização não supervisionada para análise exploratória.

---

## ⚠️ Limitações da Aprendizagem Não Supervisionada

- O **Silhouette Score** apresentou valores baixos ou negativos.
- Indica ausência de estrutura clara para agrupamentos.
- Dados e atributos não permitiram segmentação eficaz.

**Decisões tomadas**:
- ✅ Foco em modelos supervisionados (ex: Random Forest).
- ❌ Clusterização não ofereceu insights práticos.
- 🚫 KMeans mostrou desempenho insatisfatório para o problema.

---

## 🗃️ Integração Big Data

- **Apache Spark**: processamento paralelo e escalável.
- **Hadoop**: armazenamento distribuído e manipulação de dados robustos.

➡️ Permitiu manipular grandes volumes com alta performance.

---

## 📊 Consultas OLAP e Visualizações

Consultas OLAP interativas com filtros dinâmicos e gráficos automáticos:

- 📊 Gráfico de barras: comparação entre dimensões e média de passageiros.
- 🧭 Gráfico de dispersão 3D: Hora × Tempo de Viagem × Situação.
- 📈 Histograma: distribuição do número de passageiros.
- 🌐 Gráfico interativo de clusters (Plotly).

Consultas realizadas diretamente no Data Warehouse.

---

## ✅ Conclusões

- Pipeline robusto de integração e análise de dados.
- Visualizações interativas para decisões mais embasadas.
- Aplicação prática de PLN e aprendizado supervisionado.
- Arquitetura escalável com Spark e Hadoop.
- ✅ Modelos supervisionados foram mais eficazes do que não supervisionados.

---

## 📌 Próximos Passos

- Refinar a **detecção de anomalias** com algoritmos supervisionados.
- Explorar modelos de **séries temporais** (ex: ARIMA, Prophet).
- Implementar **dashboards em tempo real** com:
  - Apache Superset
  - Power BI 
