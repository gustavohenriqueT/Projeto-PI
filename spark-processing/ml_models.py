from pyspark.ml.regression import LinearRegression
from pyspark.ml.feature import VectorAssembler

def train_linear_regression(df):
    assembler = VectorAssembler(
        inputCols=["passengers"],
        outputCol="features"
    )
    df = assembler.transform(df)
    
    lr = LinearRegression(
        featuresCol="features",
        labelCol="lat",
        maxIter=10
    )
    
    model = lr.fit(df)
    return model