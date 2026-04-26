from pyspark.sql import SparkSession

class SparkUtils:

    def __init__(self, app_name, master_url=None, spark_jars=None, spark_packages=None):
        spark_builder = SparkSession.builder.appName(app_name)
        if master_url is not None:
            spark_builder = spark_builder.master(master_url)
        if spark_jars is not None:
            spark_builder = spark_builder.config("spark.jars", spark_jars)
        if spark_packages is not None:
            spark_builder = spark_builder.config("spark.jars.packages", spark_packages)
        self._spark = spark_builder.getOrCreate()
        self._spark.conf.set("spark.sql.shuffle.partitions", "50")

    @property
    def spark(self):
        return self._spark


su = SparkUtils("Validation")
spark = su.spark

validation_df = spark.read.parquet(
    's3://emr-proyecto-058264391995-us-east-1-an/output/clean_data/'
)
validation_df.show(5)
