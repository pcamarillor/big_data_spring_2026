import boto3
from pyspark.sql import SparkSession

session = boto3.session.Session()
creds = session.get_credentials().get_frozen_credentials()

spark = SparkSession.builder \
    .appName("verify") \
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262") \
    .config("spark.hadoop.fs.s3a.access.key", creds.access_key) \
    .config("spark.hadoop.fs.s3a.secret.key", creds.secret_key) \
    .config("spark.hadoop.fs.s3a.session.token", creds.token) \
    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.TemporaryAWSCredentialsProvider") \
    .config("spark.hadoop.fs.s3a.endpoint", "s3.amazonaws.com") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

df = spark.read.parquet("s3a://iteso-batch-processing/output/agg/top_products/")
df.show(truncate=False)

spark.stop()
