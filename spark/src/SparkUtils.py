import findspark

findspark.init()

from pyspark.sql import SparkSession

class SparkUtils:
    def __init__(self, master_url, app_name):
        self._spark = SparkSession.builder \
            .appName(app_name) \
            .master(master_url) \
            .config("spark.ui.port", "4040") \
            .getOrCreate()
    # end def

    def __repr__(self):
        return str(self._spark.sparkContext)
    # end def

    def spark_context(self):
        return self._spark.sparkContext
    # end def
# end class