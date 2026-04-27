try:
    import findspark
    findspark.init()
except ImportError:
    pass

from types import MappingProxyType
from typing import Iterable, Optional, Tuple

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    ArrayType,
    BinaryType,
    BooleanType,
    DateType,
    DoubleType,
    FloatType,
    IntegerType,
    LongType,
    ShortType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)


class SparkUtils:
    """
    Utility class for Spark session creation and common DataFrame helpers.

    Responsibilities:
    - Create and expose a SparkSession.
    - Generate StructType schemas from simple column definitions.
    - Provide reusable DataFrame helper methods.
    """

    TYPE_MAPPING = MappingProxyType({
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
        "struct": StructType(),
    })

    NULLABLE = True

    def __init__(
        self,
        app_name: str,
        master_url: str = "yarn",
        spark_jars: Optional[str] = None,
        spark_packages: Optional[str] = None,
        shuffle_partitions: str = "48",
    ) -> None:
        spark_builder = (
            SparkSession.builder
            .appName(app_name)
            .config("spark.ui.port", "4040")
        )

        if master_url:
            spark_builder = spark_builder.master(master_url)

        if spark_jars:
            spark_builder = spark_builder.config("spark.jars", spark_jars)

        if spark_packages:
            spark_builder = spark_builder.config("spark.jars.packages", spark_packages)

        self._spark = spark_builder.getOrCreate()
        self._spark.conf.set("spark.sql.shuffle.partitions", shuffle_partitions)

    @property
    def spark(self) -> SparkSession:
        """Return the active SparkSession."""
        return self._spark

    @classmethod
    def generate_schema(cls, columns_info: Iterable[Tuple[str, str]]) -> StructType:
        """
        Generate a StructType schema from column definitions.

        Args:
            columns_info:
                Iterable of tuples in this format:
                (column_name, data_type_string)

        Returns:
            StructType object usable by Spark readers.
        """
        struct_fields = []

        for column_name, data_type in columns_info:
            if data_type not in cls.TYPE_MAPPING:
                raise ValueError(f"Unsupported Spark data type: {data_type}")

            struct_fields.append(
                StructField(
                    column_name,
                    cls.TYPE_MAPPING[data_type],
                    cls.NULLABLE,
                )
            )

        return StructType(struct_fields)

    @staticmethod
    def count_nulls(df: DataFrame) -> DataFrame:
        """
        Return a DataFrame with one row and one column per original column,
        containing the number of null values per column.
        """
        expressions = [
            F.sum(F.when(F.col(column_name).isNull(), 1).otherwise(0)).alias(column_name)
            for column_name in df.columns
        ]

        return df.agg(*expressions)