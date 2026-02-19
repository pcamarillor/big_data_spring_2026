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
    def generate_schema(columns_info):
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
            'array_int': ArrayType(IntegerType()),
            'array_string': ArrayType(StringType()),
            'map': MapType(StringType(), StringType()),
            'struct': StructType()
        }

        struct_fields = []
        for column_info in columns_info:
            if column_info[1] not in type_mapping:
                raise ValueError(f"Unsupported data type: {column_info[1]}")

            struct_field = StructField(column_info[0], type_mapping[column_info[1]], True)
            struct_fields.append(struct_field)

        return StructType(struct_fields)