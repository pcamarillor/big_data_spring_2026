import findspark
findspark.init()

from pyspark.sql import SparkSession

from pyspark.sql.types import StructField, \
                                StringType, \
                                StructType, \
                                IntegerType, \
                                LongType, \
                                ShortType, \
                                DoubleType, \
                                FloatType, \
                                BooleanType, \
                                DateType, \
                                TimestampType, \
                                BinaryType, \
                                ArrayType, \
                                MapType


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
