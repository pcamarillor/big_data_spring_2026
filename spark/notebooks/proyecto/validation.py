from pyspark.sql import SparkSession

validation_df = spark.read.parquet(
    's3://emr-proyecto-058264391995-us-east-1-an/output/clean_data/'
)
validation_df.show(5)
