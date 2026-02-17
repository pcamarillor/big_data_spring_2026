import findspark
findspark.init()

from pyspark.sql import SparkSession

class SparkUtils:

    def __init__(self, app_name, master_url):
        self._spark = SparkSession.builder \
                .appName(app_name) \
                .master(master_url) \
                .config("spark.ui.port", "4040") \
                .getOrCreate()
    
