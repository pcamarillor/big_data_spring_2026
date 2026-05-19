import findspark

findspark.init()

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType,\
    IntegerType, LongType, ShortType, DoubleType, FloatType,\
    BooleanType, DateType, TimestampType, BinaryType, ArrayType
from pyspark.sql.functions import when, count, isnull

class SparkUtils:
    def __init__(self, master_url, app_name, spark_jars=None, spark_packages=None):
        spark_builder = SparkSession \
            .builder \
            .appName(app_name) \
            .config("spark.ui.port", "4040")
        
        if master_url is not None: spark_builder = spark_builder.master(master_url)
        # end if
    
        if spark_jars is not None: spark_builder = spark_builder.config("spark.jars", spark_jars)
        # end if

        if spark_packages is not None: spark_builder = spark_builder.config("spark.jars.packages", spark_packages)
        # end if

        self._spark = spark_builder.getOrCreate()
        self._spark.conf.set("spark.sql.shuffle.partitions", "5")
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
            col_name  = col[0]
            col_type  = col[1]

            if col_type == "struct":
                # Expect a third element with the sub-field definitions
                if len(col) < 3 or not isinstance(col[2], list):
                    raise ValueError(
                        f"Column '{col_name}' is declared as 'struct' but "
                        f"no sub-fields list was provided as the third element."
                    )
                # end if

                nested_schema = SparkUtils.generate_schema(col[2]) # recurses to build the nested StructType
                
                struct_field  = StructField(col_name, nested_schema, True)
            elif col_type not in types_map:
                raise ValueError(f"Unsupported data type: '{col_type}' for column '{col_name}'")
            else: struct_field = StructField(col[0], types_map[col[1]], True) # creates a StructField for the column
            # end if-elif-else
            
            struct_fields.append(struct_field)
        # end for-in

        return StructType(struct_fields)
    # end def

    @staticmethod
    def count_nulls(df):
        return df.select([count(when(isnull(col), col)).alias(col) for col in df.columns])
    # end def
# end class