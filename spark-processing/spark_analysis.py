# Importando as bibliotecas necessárias para o projeto
import numpy as np
import matplotlib.pyplot as plt
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import DecisionTreeClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator


#Criar uma sessão Spark
spark = SparkSession.builder.appName("Modelo_Trânsito").master("local[*]").getOrCreate()

# Importando o csv armazenado no Drive
df = spark.read.csv("/app/data/transport_dataL.csv", header = True, inferSchema= True)

# Registrando o df como uma tabela temporária chamada "trânsito"
df.createOrReplaceTempView("transito")

# Filtrando a tabela df para exibir apenas as viagens em horário de pico utilizando SQL
print("Consultando as viagens presentes apenas nos horários de pico")
df_sql = spark.sql("SELECT * FROM transito WHERE `Horario_Pico` = 1")
df_sql.show(5)

# Determinando as colunas numéricas do modelo como colunas features
colunas_features = [
    # "Numero_Passageiros",
    "Tempo_Viagem_Minutos",
    "Hora",
    "Latitude",
    "Longitude"
]

#Classificação: prever se é horário de pico ou não
df_clt = df.select(*colunas_features, "Horario_Pico").dropna()
assember_clf = VectorAssembler(inputCols=colunas_features, outputCol="features")
df_clt = assember_clf.transform(df_clt).withColumnRenamed("Horario_Pico", "label")

#Treina o modelo de Árvore de Decisão
clf = DecisionTreeClassifier(labelCol="label", featuresCol="features")
modelo_clf = clf.fit(df_clt)

# # ⚠️ Passo 3 – Se estiver tentando prever um valor contínuo (como "Tempo_Viagem_Minutos"), você precisa de um modelo de regressão, não de classificação:

# from pyspark.ml.regression import DecisionTreeRegressor

# reg = DecisionTreeRegressor(labelCol="label", featuresCol="features")
# modelo_clf = reg.fit(df_clt)

#Fazer precisões
previsoes_clf = modelo_clf.transform(df_clt)

#Avaliar a acurácia do modelo
avaliador_clf = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="accuracy")
acuracia = avaliador_clf.evaluate(previsoes_clf)
print(f"Acurácia: {acuracia: .2%}")

from os import truncate
# Mostrar exeplos de previsão do modelo
print("Exemplos de previsões do modelo:")
previsoes_clf.select("features", "label", "prediction").show(5, truncate = False)

# Medir a importância relativa de cada variável (feature) usada para treinar o modelo
importancia = modelo_clf.featureImportances
importancia_array = importancia.toArray()

# Gerando gráficos com barras horizontais demonstrando a importância de cada features
plt.figure(figsize=(10, 6))
plt.barh(colunas_features, importancia_array)
plt.xlabel("Importância")
plt.ylabel("Características")
plt.title("Importância das Características")
plt.show()

# Dividindo o df em 80% para treino e 20% para teste

# Número de registros da classe 1
n_positivos = df_clt.filter("label = 1").count()

# Amostra da classe 0 do mesmo tamanho que a classe 1
df_negativos = df_clt.filter("label = 0").sample(False, n_positivos / 35691, seed=42)
df_positivos = df_clt.filter("label = 1")

# Dataset balanceado
df_balanceado = df_positivos.union(df_negativos)

# Continue com o treino normalmente
train_data, test_data = df_balanceado.randomSplit([0.8, 0.2], seed=42)

train_data, test_data = df_clt.randomSplit([0.8,0.2], seed=42)

#treina com os dados de treino
modelo_ist = clf.fit(train_data)

# df_clt.groupBy("label").count().show()
# df.select("Hora", "Horario_Pico").distinct().orderBy("Hora").show(50)
importancia = modelo_clf.featureImportances
importancia_array = importancia.toArray()

#avalia com os dados de teste
# previsoes_clf = modelo_clf.transform(test_data)
previsoes_clf = modelo_ist.transform(test_data)  # modelo_ist foi treinado só com train_data
acuracia_clf = avaliador_clf.evaluate(previsoes_clf)
print(f"Acurácia do modelo IST: {acuracia_clf:.2%}")

from pyspark.ml.evaluation import BinaryClassificationEvaluator

avaliador_auc = BinaryClassificationEvaluator(labelCol="label", rawPredictionCol="rawPrediction", metricName="areaUnderROC")
auc = avaliador_auc.evaluate(previsoes_clf)
print(f"AUC (Área sob a curva ROC): {auc:.2%}")

# Avalia com os dados de teste
previsoes_teste = modelo_clf.transform(test_data)
acuracia_teste = avaliador_clf.evaluate(previsoes_teste)
print(f"Acurácia nos dados de teste: {acuracia_teste: .2%}")

# Salva o modelo treinado para a computação distribuída
modelo_clf.write().overwrite().save("/content/drive/MyDrive/Colab Notebooks/modelo_treinado_transito")

#Simulando a execução em outro local
from pyspark.ml.classification import DecisionTreeClassificationModel

# Carregar o modelo salvo
modelo_carregado = DecisionTreeClassificationModel.load("/content/drive/MyDrive/Colab Notebooks/modelo_treinado_transito")

# Fazer previsões
previsoes_carregada = modelo_carregado.transform(df_clt)

# Avaliar a acurácia
acuracia_carregada = avaliador_clf.evaluate(previsoes_carregada)
print(f"Acurácia: {acuracia_carregada:.2%}")

# Encerrar o Spark
spark.stop()

# Em geral, a minha compreensão sobre Spark e sua utilidade foi aprimorada. No entanto, por conta de o nosso modelo apresentar overfit, não consegui atingir 100% do entendimento sobre o assunto.
# Acredito que esse overfit aconteceu pelo fato de o nosso dataset apresentar apenas 5.000 linhas.
# Irei fazer os ajustes necessário para que o nosso dataset atinja 25.000 linhas.
# E, após isso, refazer a utilização do Spark e revisar as apresentações das acurácias em cada etapa para obter mais conclusões e conhecimento sobre o assunto