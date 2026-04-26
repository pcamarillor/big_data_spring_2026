"""
Spark Utils — EMR Edition
Procesamiento de Datos Masivos | ITESO
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import (
    StructType, StructField,
    StringType, IntegerType, LongType, ShortType,
    DoubleType, FloatType, BooleanType,
    DateType, TimestampType, BinaryType,
    ArrayType,
)
from pyspark.sql.functions import count, when, isnull


class SparkUtils:

    def __init__(self, app_name, master_url=None, spark_jars=None, spark_packages=None):
        spark_builder = SparkSession.builder.appName(app_name)

        if master_url is not None:
            spark_builder = spark_builder.master(master_url)
        if spark_jars is not None:
            spark_builder = spark_builder.config("spark.jars", spark_jars)
        if spark_packages is not None:
            spark_builder = spark_builder.config("spark.jars.packages", spark_packages)

        self._spark = spark_builder.getOrCreate()

    @property
    def spark(self):
        return self._spark

    @staticmethod
    def generate_schema(columns_info) -> StructType:
        """
        Build a StructType from a list of (col_name, type_string) tuples.
        Supported types: string, int, long, short, double, float, boolean,
                         date, timestamp, binary, array_int, array_string, struct.
        """
        type_mapping = {
            "string":       StringType(),
            "int":          IntegerType(),
            "long":         LongType(),
            "short":        ShortType(),
            "double":       DoubleType(),
            "float":        FloatType(),
            "boolean":      BooleanType(),
            "date":         DateType(),
            "timestamp":    TimestampType(),
            "binary":       BinaryType(),
            "array_int":    ArrayType(IntegerType()),
            "array_string": ArrayType(StringType()),
            "struct":       StructType(),
        }

        struct_fields = []
        for column_info in columns_info:
            col_name = column_info[0]
            col_type = column_info[1]

            if col_type == "struct":
                if len(column_info) < 3 or not isinstance(column_info[2], list):
                    raise ValueError(
                        f"Column '{col_name}' is declared as 'struct' but "
                        f"no sub-fields list was provided as the third element."
                    )
                nested_schema = SparkUtils.generate_schema(column_info[2])
                struct_field  = StructField(col_name, nested_schema, True)
            elif col_type not in type_mapping:
                raise ValueError(
                    f"Unsupported data type: '{col_type}' for column '{col_name}'"
                )
            else:
                struct_field = StructField(col_name, type_mapping[col_type], True)

            struct_fields.append(struct_field)

        return StructType(struct_fields)

    @staticmethod
    def count_nulls(df: DataFrame) -> DataFrame:
        return df.select([count(when(isnull(c), c)).alias(c) for c in df.columns])

    @staticmethod
    def null_audit(df: DataFrame, label: str = "") -> None:
        header = f"[NULL AUDIT] {label}" if label else "[NULL AUDIT]"
        print(f"\n{header}")
        SparkUtils.count_nulls(df).show()

    @staticmethod
    def quick_summary(df: DataFrame, label: str = "", n: int = 5) -> None:
        header = f"[SUMMARY] {label}" if label else "[SUMMARY]"
        print(f"\n{header}")
        print(f"  Rows    : {df.count():,}")
        print(f"  Columns : {len(df.columns)}")
        df.printSchema()
        df.show(n, truncate=False)

    def read_csv(self, path: str, columns_info: list) -> DataFrame:
        schema = SparkUtils.generate_schema(columns_info)
        return (
            self._spark.read
            .option("header", "true")
            .option("mode", "PERMISSIVE")
            .schema(schema)
            .csv(path)
        )
