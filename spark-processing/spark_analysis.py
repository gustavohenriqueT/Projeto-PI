import numpy as np
import matplotlib.pyplot as plt
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import DecisionTreeClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator, BinaryClassificationEvaluator
from pyspark.ml.classification import DecisionTreeClassificationModel
import os # Adicionado para lidar com caminhos de arquivo local

# Criar uma sessão Spark
spark = SparkSession.builder.appName("Modelo_Transito").master("local[*]").getOrCreate()

# Importando o csv processado pelo R
# Caminho dentro do container Spark
csv_path = "/data/transport_dataL.csv" # O volume './data' está montado como '/data' no Spark
df = spark.read.csv(csv_path, header=True, inferSchema=True)

# Verificando se o DataFrame está vazio após a leitura
if df.count() == 0:
    print(f"Erro: O arquivo {csv_path} está vazio ou não pôde ser lido. Verifique o processamento R.")
    spark.stop()
    exit(1)

# Registrando o df como uma tabela temporária chamada "trânsito"
df.createOrReplaceTempView("transito")

# Filtrando a tabela df para exibir apenas as viagens em horário de pico utilizando SQL
print("Consultando as viagens presentes apenas nos horários de pico")
df_sql = spark.sql("SELECT * FROM transito WHERE `horario_pico` = 1") # Coluna 'horario_pico' é minúscula após R
df_sql.show(5)

# Determinando as colunas numéricas do modelo como colunas features
colunas_features = [
    "tempo_viagem_minutos", # Coluna 'tempo_viagem_minutos' é minúscula após R
    "hora",                 # Coluna 'hora' é minúscula após R
    "latitude",             # Coluna 'latitude' é minúscula após R
    "longitude"             # Coluna 'longitude' é minúscula após R
]

# Classificação: prever se é horário de pico ou não
# Certificar-se de que as colunas existem e não são nulas
df_clt = df.select(*colunas_features, "horario_pico").dropna()
assember_clf = VectorAssembler(inputCols=colunas_features, outputCol="features")
df_clt = assember_clf.transform(df_clt).withColumnRenamed("horario_pico", "label")

# Treina o modelo de Árvore de Decisão
clf = DecisionTreeClassifier(labelCol="label", featuresCol="features")
modelo_clf = clf.fit(df_clt)

# Fazer precisões
previsoes_clf = modelo_clf.transform(df_clt)

# Avaliar a acurácia do modelo
avaliador_clf = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="accuracy")
acuracia = avaliador_clf.evaluate(previsoes_clf)
print(f"Acurácia: {acuracia: .2%}")

# Mostrar exemplos de previsão do modelo
print("Exemplos de previsões do modelo:")
previsoes_clf.select("features", "label", "prediction").show(5, truncate=False)

# Medir a importância relativa de cada variável (feature) usada para treinar o modelo
importancia = modelo_clf.featureImportances
importancia_array = importancia.toArray()

# Gerando gráficos com barras horizontais demonstrando a importância de cada features
plt.figure(figsize=(10, 6))
plt.barh(colunas_features, importancia_array)
plt.xlabel("Importância")
plt.ylabel("Características")
plt.title("Importância das Características")
plt.savefig("/data/feature_importances.png") # Salva o gráfico no volume compartilhado
plt.close() # Fecha a figura para liberar memória
print("Gráfico de Importância das Características salvo em /data/feature_importances.png")

# Dividindo o df em 80% para treino e 20% para teste
# Garantir que o dataset balanceado tenha dados
if df_clt.filter("label = 1").count() == 0 or df_clt.filter("label = 0").count() == 0:
    print("Aviso: Dados insuficientes para balanceamento de classes. Treinando com dataset original.")
    train_data, test_data = df_clt.randomSplit([0.8, 0.2], seed=42)
else:
    # Número de registros da classe 1
    n_positivos = df_clt.filter("label = 1").count()
    # Amostra da classe 0 do mesmo tamanho que a classe 1 (ajustar a proporção se necessário)
    # O divisor 35691 parece ser um número mágico, talvez baseado no seu dataset Colab.
    # É melhor calcular a proporção dinamicamente ou usar um oversampling/undersampling adequado.
    # Por simplicidade, vamos usar 1 como divisor se for um caso binário e balanceado.
    # Se for para undersample da classe 0, precisa da proporção de n_positivos / total_negativos

    # Correção para o balanceamento:
    n_negativos = df_clt.filter("label = 0").count()
    if n_negativos > 0:
        sample_fraction_negativos = n_positivos / n_negativos
    else:
        sample_fraction_negativos = 1.0 # Evita divisao por zero, mas implica que nao havera negativos se n_negativos for 0

    df_negativos = df_clt.filter("label = 0").sample(False, sample_fraction_negativos, seed=42)
    df_positivos = df_clt.filter("label = 1")
    df_balanceado = df_positivos.unionAll(df_negativos) # Use unionAll para evitar distinct que pode ser lento

    # Continue com o treino normalmente
    train_data, test_data = df_balanceado.randomSplit([0.8, 0.2], seed=42)


# Treina com os dados de treino
modelo_ist = clf.fit(train_data)

# Avalia com os dados de teste
previsoes_clf = modelo_ist.transform(test_data)
acuracia_clf = avaliador_clf.evaluate(previsoes_clf)
print(f"Acurácia do modelo IST: {acuracia_clf:.2%}")

avaliador_auc = BinaryClassificationEvaluator(labelCol="label", rawPredictionCol="rawPrediction", metricName="areaUnderROC")
auc = avaliador_auc.evaluate(previsoes_clf)
print(f"AUC (Área sob a curva ROC): {auc:.2%}")

# Avalia com os dados de teste (já feito acima, mas mantido para clareza se quiser métricas separadas do treino/teste split)
previsoes_teste = modelo_clf.transform(test_data)
acuracia_teste = avaliador_clf.evaluate(previsoes_teste)
print(f"Acurácia nos dados de teste: {acuracia_teste: .2%}")

# Salva o modelo treinado para a computação distribuída
# O caminho deve ser um diretório acessível e vazio ou ser sobrescrito
model_path = "/data/modelo_treinado_transito" # Salva no volume compartilhado
modelo_clf.write().overwrite().save(model_path)
print(f"Modelo salvo em: {model_path}")

# Simulando a execução em outro local (carregando o modelo salvo)
# Carregar o modelo salvo
modelo_carregado = DecisionTreeClassificationModel.load(model_path)

# Fazer previsões
previsoes_carregada = modelo_carregado.transform(df_clt)

# Avaliar a acurácia
acuracia_carregada = avaliador_clf.evaluate(previsoes_carregada)
print(f"Acurácia do modelo carregado: {acuracia_carregada:.2%}")

# Encerrar o Spark
spark.stop()
print("Spark Session encerrada.")