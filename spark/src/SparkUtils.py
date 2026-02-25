import findspark

findspark.init()

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType,\
    IntegerType, LongType, ShortType, DoubleType, FloatType,\
    BooleanType, DateType, TimestampType, BinaryType, ArrayType
from pyspark.sql.functions import when, count, isnull

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

    @staticmethod
    def generate_schema(columns) -> StructType:
        # maps string type names to PySpark data types
        types_map = {
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

        for col in columns:
            if col[1] not in types_map: raise ValueError(f"Unsupported data type: {col[1]}")
            # end if

            # appends StructField to the list
            struct_fields.append(StructField(col[0], types_map[col[1]], True))
        # end for-in

        return StructType(struct_fields)
    # end def

    @staticmethod
    def count_nulls(df):
        return df.select([count(when(isnull(col), col)).alias(col) for col in df.columns])
    # end def
# end class