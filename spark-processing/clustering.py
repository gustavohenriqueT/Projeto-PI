from pyspark.ml.clustering import KMeans
from pyspark.ml.feature import VectorAssembler

def cluster_locations(df, k=3):
    assembler = VectorAssembler(
        inputCols=["lat", "lon"],
        outputCol="features"
    )
    df = assembler.transform(df)
    
    kmeans = KMeans(
        featuresCol="features",
        k=k,
        seed=42
    )
    
    model = kmeans.fit(df)
    return model.transform(df)