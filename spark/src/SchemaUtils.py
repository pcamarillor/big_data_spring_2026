import pyspark.sql.types as StructType
from typing import Tuple
from pyspark.sql.types import StructField, StructType, StringType, IntegerType, FloatType, BooleanType, DateType, TimestampType, ArrayType, MapType, NullType, LongType
class SchemaUtils:
    @staticmethod
    def datatypes():
        return {
            "string": StringType(),
            "int": IntegerType(),
            "long": LongType(),
            "float": FloatType(),
            "bool": BooleanType(),
            "date": DateType(),
            "timestamp": TimestampType(),
            "array_string": ArrayType(StringType()),
            "array_int": ArrayType(IntegerType()),
            "array_long": ArrayType(LongType()),
            "array_float": ArrayType(FloatType()),
            "array_bool": ArrayType(BooleanType()),
            "array_date": ArrayType(DateType()),
            "array_timestamp": ArrayType(TimestampType()),
            "struct": StructType(),
            "null": NullType(),  
        }
    @staticmethod
    def create_schema(attributes: Tuple[str, str]) -> StructType:
        try:
            schema = StructType()
            datatypes = SchemaUtils.datatypes()
            for name, type in attributes:
                schema.add(StructField(name, datatypes[type.lower()]))
            return schema
        except Exception as e:
            print(f"Error creating schema: {e}")
            return None
