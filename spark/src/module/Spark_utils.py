# spark_utils.py
from pyspark.sql import SparkSession

class SparkUtils:
    def __init__(self, app_name):
        self.spark = SparkSession.builder.appName(app_name).getOrCreate()
    
    def get_spark_session(self):
        return self.spark