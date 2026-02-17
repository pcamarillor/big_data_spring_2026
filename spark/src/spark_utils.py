import findspark
findspark.init()

from pyspark.sql import SparkSession

class SparkUtils:
    def __init__(self, master_url, appname):
        self._spark = SparkSession.builder \
                    .appName(appname) \
                    .master(master_url) \
                    .config("spark.ui.port", "4040") \
                    .getOrCreate()
    
    def __repr__(self):
        return str(self._spark.sparkContext)
    
    def spark_context(self):
        return self._spark.sparkContext