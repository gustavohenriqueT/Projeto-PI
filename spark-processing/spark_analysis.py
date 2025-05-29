import numpy as np
import matplotlib
matplotlib.use('Agg') # Usar backend não interativo para matplotlib em scripts
import matplotlib.pyplot as plt
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import DecisionTreeClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator, BinaryClassificationEvaluator
from pyspark.ml.classification import DecisionTreeClassificationModel
import os 
import json # Adicionado para salvar métricas

# Criar uma sessão Spark
spark = SparkSession.builder.appName("Modelo_Transito_Classificacao").master("local[*]").getOrCreate()

# Importando o csv processado pelo R
csv_path = "/data/transport_dataL.csv" 
df = spark.read.csv(csv_path, header=True, inferSchema=True)

if df.count() == 0:
    print(f"ERRO: Arquivo de entrada '{csv_path}' está vazio ou não pôde ser lido. Verifique o processamento R.")
    spark.stop()
    exit(1)

df.createOrReplaceTempView("transito")

print("Amostra dos dados carregados para Spark:")
df.show(5, truncate=False)

colunas_features = [
    "tempo_viagem_minutos", 
    "hora",                 
    "latitude",             
    "longitude"             
]
# Verificar se as colunas existem
for col_check in colunas_features + ["horario_pico"]:
    if col_check not in df.columns:
        print(f"ERRO: Coluna '{col_check}' esperada não encontrada no DataFrame. Colunas disponíveis: {df.columns}")
        spark.stop()
        exit(1)

df_clt = df.select(*colunas_features, "horario_pico").dropna()
if df_clt.count() == 0:
    print("ERRO: DataFrame para classificação ficou vazio após dropna. Verifique os dados de entrada.")
    spark.stop()
    exit(1)

assember_clf = VectorAssembler(inputCols=colunas_features, outputCol="features")
df_clt = assember_clf.transform(df_clt).withColumnRenamed("horario_pico", "label")

# Modelo treinado com todos os dados (para importância das features)
print("Treinando modelo de classificação com todos os dados (para feature importance)...")
clf_all_data = DecisionTreeClassifier(labelCol="label", featuresCol="features", seed=42)
modelo_clf_all_data = clf_all_data.fit(df_clt)
previsoes_clf_treino_completo = modelo_clf_all_data.transform(df_clt) 

avaliador_multi = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="accuracy")
acuracia_treino_completo = avaliador_multi.evaluate(previsoes_clf_treino_completo) 
print(f"Acurácia (treino com todos os dados): {acuracia_treino_completo:.2%}")

print("Exemplos de previsões do modelo (treino com todos os dados):")
previsoes_clf_treino_completo.select("features", "label", "prediction").show(5, truncate=False)

importancia = modelo_clf_all_data.featureImportances
importancia_array = importancia.toArray()

plt.figure(figsize=(10, 6))
plt.barh(colunas_features, importancia_array)
plt.xlabel("Importância")
plt.ylabel("Características")
plt.title("Importância das Características (Modelo Treinado com Todos os Dados)")
OUTPUT_FEATURE_IMPORTANCE_PATH = "/data/feature_importances.png" 
try:
    plt.savefig(OUTPUT_FEATURE_IMPORTANCE_PATH) 
    plt.close() 
    print(f"Gráfico de Importância das Características salvo em {OUTPUT_FEATURE_IMPORTANCE_PATH}")
except Exception as e:
    print(f"Erro ao salvar gráfico de importância: {e}")


# Divisão treino/teste e balanceamento
train_data, test_data = None, None 
acuracia_teste_balanceado = "N/A" 
auc_teste_balanceado = "N/A" 

n_positivos = df_clt.filter("label = 1").count()
n_negativos = df_clt.filter("label = 0").count()

if n_positivos == 0 or n_negativos == 0:
    print("AVISO: Dados insuficientes para balanceamento de classes (uma ou ambas as classes têm 0 registros).")
    print("Prosseguindo com divisão treino/teste no dataset original desbalanceado, se tiver dados suficientes.")
    if df_clt.count() >= 2: 
         train_data, test_data = df_clt.randomSplit([0.8, 0.2], seed=42)
    else:
        print("ERRO: Não há dados suficientes em df_clt para dividir em treino/teste.")
else:
    print(f"Balanceando classes: {n_positivos} positivos, {n_negativos} negativos.")
    df_positivos = df_clt.filter("label = 1")
    df_negativos = df_clt.filter("label = 0")

    df_balanceado = None
    if n_negativos > n_positivos: 
        sample_fraction = n_positivos / n_negativos
        df_negativos_amostrados = df_negativos.sample(False, sample_fraction, seed=42)
        df_balanceado = df_positivos.unionAll(df_negativos_amostrados)
        print(f"Realizado undersampling da classe negativa. Fração: {sample_fraction:.4f}")
    elif n_positivos > n_negativos and n_negativos > 0 : 
        ratio = int(n_positivos / n_negativos) 
        df_oversampled_negatives = df_negativos
        for _ in range(1, ratio):
             df_oversampled_negatives = df_oversampled_negatives.unionAll(df_negativos)
        df_balanceado = df_positivos.unionAll(df_oversampled_negatives.limit(n_positivos)) 
        print(f"Realizado oversampling (aproximado) da classe negativa.")
    else: 
        df_balanceado = df_clt
        print("Classes já parecem balanceadas ou não foi possível realizar oversampling/undersampling.")

    if df_balanceado and df_balanceado.count() > 0: # Checa se df_balanceado não é None e tem dados
        print(f"Dataset após tentativa de balanceamento: {df_balanceado.count()} registros.")
        train_data, test_data = df_balanceado.randomSplit([0.8, 0.2], seed=42)
    else:
        print("ERRO: Dataset ficou vazio ou não foi possível balancear. Usando split original se possível.")
        if df_clt.count() >=2:
             train_data, test_data = df_clt.randomSplit([0.8, 0.2], seed=42) # Fallback


modelo_final_para_salvar = modelo_clf_all_data 

if train_data and test_data and train_data.count() > 0 and test_data.count() > 0:
    print(f"Treinando modelo com dados de treino (após balanceamento/split): {train_data.count()} registros")
    clf_balanceado = DecisionTreeClassifier(labelCol="label", featuresCol="features", seed=123) 
    modelo_treinado = clf_balanceado.fit(train_data)
    modelo_final_para_salvar = modelo_treinado 
    
    print(f"Avaliando com dados de teste (após balanceamento/split): {test_data.count()} registros")
    previsoes_teste = modelo_treinado.transform(test_data)
    
    acuracia_teste_balanceado = avaliador_multi.evaluate(previsoes_teste)
    print(f"Acurácia (teste com dados balanceados/divididos): {acuracia_teste_balanceado:.2%}")

    distinct_predictions = previsoes_teste.select("prediction").distinct().count()
    if distinct_predictions > 1:
        avaliador_auc = BinaryClassificationEvaluator(labelCol="label", rawPredictionCol="rawPrediction", metricName="areaUnderROC")
        auc_teste_balanceado = avaliador_auc.evaluate(previsoes_teste)
        print(f"AUC (teste com dados balanceados/divididos): {auc_teste_balanceado:.2%}")
    else:
        print("AUC não calculado: modelo prevê apenas uma classe nos dados de teste.")
        auc_teste_balanceado = "N/A (predição unária)"
else:
    print("AVISO: Divisão treino/teste resultou em dataset(s) vazio(s) ou o balanceamento falhou. Algumas métricas de teste não serão calculadas.")


MODEL_PATH = "/data/modelo_classificacao_horario_pico_dt" 
try:
    modelo_final_para_salvar.write().overwrite().save(MODEL_PATH)
    print(f"Modelo de classificação salvo em: {MODEL_PATH}")
except Exception as e:
    print(f"Erro ao salvar modelo de classificação: {e}")

acuracia_carregada = "N/A"
try:
    modelo_carregado = DecisionTreeClassificationModel.load(MODEL_PATH)
    if test_data and test_data.count() > 0:
        previsoes_carregada = modelo_carregado.transform(test_data) 
        acuracia_carregada = avaliador_multi.evaluate(previsoes_carregada)
        print(f"Acurácia do modelo carregado (no mesmo conjunto de teste): {acuracia_carregada:.2%}")
    else:
        print("Modelo carregado, mas não há dados de teste para avaliar.")
except Exception as e:
    print(f"Erro ao carregar ou testar o modelo salvo: {e}")

metrics_to_save = {
    "acuracia_treino_completo_desbalanceado": acuracia_treino_completo if isinstance(acuracia_treino_completo, float) else "N/A",
    "acuracia_teste_balanceado_ou_split": acuracia_teste_balanceado if isinstance(acuracia_teste_balanceado, float) else "N/A",
    "auc_teste_balanceado_ou_split": auc_teste_balanceado if isinstance(auc_teste_balanceado, float) else auc_teste_balanceado, # Mantém string "N/A..."
    "acuracia_modelo_carregado_no_teste": acuracia_carregada if isinstance(acuracia_carregada, float) else "N/A"
}

OUTPUT_METRICS_JSON_PATH = "/data/ml_classification_metrics.json"
try:
    with open(OUTPUT_METRICS_JSON_PATH, 'w') as f:
        json.dump(metrics_to_save, f, indent=4)
    print(f"Métricas de Classificação salvas em: {OUTPUT_METRICS_JSON_PATH}")
except Exception as e:
    print(f"Erro ao salvar métricas de classificação em JSON: {e}")

spark.stop()
print("Spark Session encerrada.")