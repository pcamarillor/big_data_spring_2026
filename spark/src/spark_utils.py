import findspark

findspark.init()

from pyspark.sql import SparkSession

from pyspark.sql.types import StructType, StructField, StringType, IntegerType, LongType, ShortType, DoubleType, FloatType, BooleanType, DateType, TimestampType, BinaryType, ArrayType

from pyspark.sql.functions import when, count, isnull
class SparkUtils:

        def __init__(self,master_url, appname):

                self._spark = SparkSession.builder \
                        .appName("Spark SQL example") \
                        .config("spark.ui.port", "4040") \
                        .getOrCreate()
                
        def __repr__(self):
                return str(self._spark.sparkContext)
        
        def spark_context(self):
                return self._spark.sparkContext
        
        
        @staticmethod
        def generate_schema(columns_info) -> StructType:
                """
                Generates a list of StructField objects from a list of tuples.

                Args:
                column_info (list of tuples): Each tuple contains (column_name, data_type_string).

                Returns:
                list: A list of StructField objects.
                """
                # Mapping from string type names to PySpark data types
                type_mapping = {
                "string": StringType(),
                "int": IntegerType(),
                "long": LongType(),
                "short": ShortType(),
                "double": DoubleType(),
                "float": FloatType(),
                "boolean": BooleanType(),
                "date": DateType(),
                "timestamp": TimestampType(),
                "binary": BinaryType(),
                "array_int": ArrayType(IntegerType()),
                "array_string": ArrayType(StringType()),
                "struct": StructType()
                }

                struct_fields = []
                for column_info in columns_info:
                        if column_info[1] not in type_mapping:
                                raise ValueError(f"Unsupported data type: {column_info[1]}")

                        # Create a StructField for the column
                        struct_field = StructField(column_info[0], type_mapping[column_info[1]], True)
                        struct_fields.append(struct_field)

                return StructType(struct_fields)
        
        @staticmethod
        def count_nulls(df):
                return df.select([count(when(isnull(c), c)).alias(c) for c in df.columns])