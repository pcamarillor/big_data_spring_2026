import pyspark.sql.types as StructType
from typing import Tuple
from pyspark.sql.types import StructField, StructType, StringType, IntegerType, FloatType, BooleanType, DateType, TimestampType, ArrayType, MapType, NullType, LongType
class SchemaUtils:
    @staticmethod
    def datatypes():
        return {
            "string": StringType,
            "int": IntegerType,
            "long": LongType,
            "float": FloatType,
            "bool": BooleanType,
            "date": DateType,
            "timestamp": TimestampType,
            "array": ArrayType,
            "map": MapType,
            "null": NullType,  
        }
    @staticmethod
    def create_schema(attributes: Tuple[str, str]) -> StructType:
        try:
            schema = StructType()
            datatypes = SchemaUtils.datatypes()
            for name, type in attributes:
                schema.add(StructField(name, datatypes[type.lower()]()))
            return schema
        except Exception as e:
            print(f"Error creating schema: {e}")
            return None
