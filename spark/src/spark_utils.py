import findspark
findspark.init()

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, LongType, ShortType, DoubleType, FloatType, BooleanType, DateType, TimestampType, BinaryType, ArrayType
from pyspark.sql.functions import count, when, isnull

class SparkUtils:

    def __init__(self, master_url="spark://spark-master:7077", app_name="helloworld",spark_jars=None,spark_packages=None):
            builder = (SparkSession.builder
                .appName(app_name)
                .master(master_url)
                .config("spark.ui.port", "4040"))

            if spark_jars is not None:
                builder = builder.config("spark.jars", spark_jars)

            if spark_packages is not None:
                builder = builder.config("spark.jars.packages", spark_packages)

            self._spark = builder.getOrCreate()
            self._spark.conf.set("spark.sql.shuffle.partitions", "5")
    def __repr__(self):
        return str(self._spark.sparkContext)

    @property
    def spark(self):
        return self._spark

    @staticmethod
    def count_nulls(df):
        return df.select([count(when(isnull(c),c)).alias(c) for c in df.columns])

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
            col_name  = column_info[0]
            col_type  = column_info[1]

            if col_type == "struct":
                # Expect a third element with the sub-field definitions
                if len(column_info) < 3 or not isinstance(column_info[2], list):
                    raise ValueError(
                        f"Column '{col_name}' is declared as 'struct' but "
                        f"no sub-fields list was provided as the third element."
                    )
                # Recurse to build the nested StructType
                nested_schema = SparkUtils.generate_schema(column_info[2])
                struct_field  = StructField(col_name, nested_schema, True)

            elif column_info[1] not in type_mapping:
                raise ValueError(f"Unsupported data type: {column_info[1]}")

            # Create a StructField for the column
            else: 
                struct_field = StructField(column_info[0], type_mapping[column_info[1]], True)
            struct_fields.append(struct_field)

        return StructType(struct_fields)


