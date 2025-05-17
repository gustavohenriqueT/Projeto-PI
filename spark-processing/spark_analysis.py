from pyspark.sql import SparkSession
from ml_models import train_linear_regression
from clustering import cluster_locations

spark = SparkSession.builder.appName("TransportAnalysis").getOrCreate()

# Load data
df = spark.read.csv("/data/transport_data.csv", header=True, inferSchema=True)

# Machine Learning
lr_model = train_linear_regression(df)
clustered_data = cluster_locations(df)

# Save results to PostgreSQL
clustered_data.write.format("jdbc") \
    .option("url", "jdbc:postgresql://postgres:5432/transport_db") \
    .option("dbtable", "transport_clusters") \
    .option("user", "admin") \
    .option("password", "password") \
    .save()

spark.stop()