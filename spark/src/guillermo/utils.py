import findspark
findspark.init()

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StringType, IntegerType, LongType, ShortType, DoubleType, FloatType, BooleanType, DateType, FloatType, BooleanType, DateType, TimestampType, BinaryType, StructField, ArrayType
from pyspark.sql.functions import count, when, isnull

class SparkUtils:

    def __init__(self, app_name, master_url, spark_jars=None):
        if spark_jars is not None:
           self._spark = (SparkSession.builder
                .appName(app_name)
                .master(master_url)
                .config("spark.ui.port", "4040")
                .config("spark.jars", spark_jars)
                .getOrCreate())
        else:
            self._spark = SparkSession.builder \
                .appName(app_name) \
                .master(master_url) \
                .config("spark.ui.port", "4040") \
                .getOrCreate()
    
    @property
    def spark(self):
        return self._spark

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
    
class Student:
    def __init__(self, name, grade1):
        self._name = name
        self._grades = []
        self._grades.append(grade1)

    def __repr__(self):
        return f"Student(name={self._name})"


    def display(self):
        print(f"name:{self._name}")
        for g in self._grades:
            print(f"grade:{g}")

def squares(n):
    return n**2
        