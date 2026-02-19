import findspark
findspark.init()

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType

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

    @staticmethod
    def generate_schema(schema_list):
        
        # StringType: Represents string values.
        # IntegerType: Represents integer values.
        # LongType: Represents long integer values.
        # ShortType: Represents short integer values.
        # DoubleType: Represents double-precision floating-point values.
        # FloatType: Represents single-precision floating-point values.
        # BooleanType: Represents boolean values (True/False).
        # DateType: Represents date values.
        # TimestampType: Represents timestamp values.
        # BinaryType: Represents binary data.
        # ArrayType: Represents arrays of elements.
        # MapType: Represents key-value pairs.
        # StructType: Represents nested structures (complex types).

        type_mapping = {
            'string': StringType(),
            'integer': IntegerType(),
            'long': LongType(),
            'short': ShortType(),
            'double': DoubleType(),
            'float': FloatType(),
            'boolean': BooleanType(),
            'date': DateType(),
            'timestamp': TimestampType(),
            'binary': BinaryType(),
            'array': ArrayType(StringType()),
            'map': MapType(StringType(), StringType()),
            'struct': StructType()
        }
        fields = [StructField(name, type_mapping.get(dtype, StringType()), True) for name, dtype in schema_list]
        return StructType(fields)