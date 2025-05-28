import pandas as pd
import numpy as np
import os
import json
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, davies_bouldin_score
import hdbscan

# Caminhos
CSV_PATH_INPUT = '/data/transport_dataL.csv'
OUTPUT_IMAGE_PATH_PCA = '/data/hdbscan_clusters_pca.png'
OUTPUT_METRICS_PATH = '/data/clustering_metrics.json'
OUTPUT_CLUSTERED_DATA_SAMPLE_PATH = '/data/clustered_data_sample.csv' 

print("--- Iniciando Análise de Clusterização ---")

try:
    if not os.path.exists(CSV_PATH_INPUT):
        print(f"ERRO: Arquivo de entrada '{CSV_PATH_INPUT}' não encontrado.")
        exit(1)
    
    df_original = pd.read_csv(CSV_PATH_INPUT)
    print(f"Dados carregados de '{CSV_PATH_INPUT}'. Shape original: {df_original.shape}")

    if df_original.empty:
        print("ERRO: DataFrame original está vazio.")
        exit(1)
    
    # Selecionar colunas relevantes para clusterização (todas devem ser numéricas ou pré-processadas para tal)
    # Exemplo: latitude, longitude, numero_passageiros, tempo_viagem_minutos, hora
    # Certifique-se que os nomes estão corretos e em minúsculas
    features_to_cluster = ['latitude', 'longitude', 'numero_passageiros', 'tempo_viagem_minutos', 'hora']
    
    # Verificar se as colunas existem
    missing_cols = [col for col in features_to_cluster if col not in df_original.columns]
    if missing_cols:
        print(f"ERRO: As seguintes colunas para clusterização não foram encontradas: {missing_cols}")
        print(f"Colunas disponíveis: {df_original.columns.tolist()}")
        exit(1)
        
    df_for_clustering = df_original[features_to_cluster].copy()
    
    # Pré-processamento: Imputação de NaNs e Padronização
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')), 
        ('scaler', StandardScaler()) 
    ])

    print("Aplicando pré-processamento nas features selecionadas...")
    x_preprocessed = numeric_transformer.fit_transform(df_for_clustering)

    if x_preprocessed.shape[0] == 0:
        print("ERRO: Dados pré-processados resultaram em um array vazio.")
        exit(1)
    print(f"Shape dos dados pré-processados: {x_preprocessed.shape}")

    print("Executando HDBSCAN...")
    min_cluster_size = max(15, int(len(x_preprocessed) * 0.005)) 
    min_samples = max(5, int(min_cluster_size * 0.1))        
    print(f"Parâmetros HDBSCAN: min_cluster_size={min_cluster_size}, min_samples={min_samples}")

    clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, min_samples=min_samples, gen_min_span_tree=True, metric='euclidean')
    labels = clusterer.fit_predict(x_preprocessed)
    df_original['cluster_label_hdbscan'] = labels

    n_clusters_found = len(set(labels)) - (1 if -1 in labels else 0) 
    n_outliers = list(labels).count(-1)
    print(f"HDBSCAN - Número de clusters encontrados: {n_clusters_found}")
    print(f"HDBSCAN - Número de outliers (-1): {n_outliers}")

    silhouette_avg, davies_bouldin = "N/A", "N/A"
    mask_clustered_points = labels != -1
    num_clustered_points = np.sum(mask_clustered_points)

    if n_clusters_found > 1 and num_clustered_points > n_clusters_found : 
        try:
            silhouette_avg = silhouette_score(x_preprocessed[mask_clustered_points], labels[mask_clustered_points])
            print(f"HDBSCAN - Silhouette Score: {silhouette_avg:.4f}")
        except ValueError as e: print(f"HDBSCAN - Não foi possível calcular Silhouette Score: {e}")
        try:
            davies_bouldin = davies_bouldin_score(x_preprocessed[mask_clustered_points], labels[mask_clustered_points])
            print(f"HDBSCAN - Davies-Bouldin Score: {davies_bouldin:.4f}")
        except ValueError as e: print(f"HDBSCAN - Não foi possível calcular Davies-Bouldin Score: {e}")
    else:
        print("HDBSCAN - Métricas de Silhouette e Davies-Bouldin não aplicáveis.")
            
    clustering_results = {
        "algorithm": "HDBSCAN", "min_cluster_size_param": min_cluster_size,
        "min_samples_param": min_samples, "num_clusters_found": n_clusters_found,
        "num_outliers": n_outliers,
        "silhouette_score": silhouette_avg if isinstance(silhouette_avg, float) else "N/A",
        "davies_bouldin_score": davies_bouldin if isinstance(davies_bouldin, float) else "N/A"
    }
    with open(OUTPUT_METRICS_PATH, 'w') as f:
        json.dump(clustering_results, f, indent=4)
    print(f"Métricas de clusterização salvas em: {OUTPUT_METRICS_PATH}")

    if x_preprocessed.shape[1] >= 2: 
        print("Aplicando PCA para visualização...")
        pca = PCA(n_components=2, random_state=42)
        x_pca = pca.fit_transform(x_preprocessed)
        plt.figure(figsize=(10, 7))
        if num_clustered_points > 0:
            scatter_clusters = plt.scatter(x_pca[mask_clustered_points, 0], x_pca[mask_clustered_points, 1], c=labels[mask_clustered_points], cmap='viridis', s=50, alpha=0.7)
            if n_clusters_found > 0 and len(set(labels[mask_clustered_points])) > 1 : plt.colorbar(scatter_clusters, label='ID do Cluster HDBSCAN')
        if n_outliers > 0: plt.scatter(x_pca[~mask_clustered_points, 0], x_pca[~mask_clustered_points, 1], c='lightgray', s=20, alpha=0.5, label=f'Outliers ({n_outliers})')
        plt.title('Clusters HDBSCAN Visualizados com PCA (2D)')
        plt.xlabel('Componente Principal 1'); plt.ylabel('Componente Principal 2')
        if n_outliers > 0 or n_clusters_found > 0 : plt.legend()
        plt.grid(True); plt.savefig(OUTPUT_IMAGE_PATH_PCA)
        print(f"Gráfico PCA dos clusters salvo em: {OUTPUT_IMAGE_PATH_PCA}")
    else:
        print("Visualização PCA não gerada: features insuficientes.")

    df_original.head(1000).to_csv(OUTPUT_CLUSTERED_DATA_SAMPLE_PATH, index=False)
    print(f"Amostra dos dados com labels de cluster salva em: {OUTPUT_CLUSTERED_DATA_SAMPLE_PATH}")

except Exception as e:
    print(f"ERRO inesperado durante a análise de clusterização: {e}")
    import traceback
    traceback.print_exc()

print("--- Análise de Clusterização Concluída ---")