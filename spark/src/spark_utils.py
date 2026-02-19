import findspark
findspark.init()

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

class SparkUtils:

    def __init__(self, app_name, master_url):
        self._spark = SparkSession.builder \
            .appName(app_name) \
            .master(master_url) \
            .config("spark.ui.port", "4040") \
            .getOrCreate()

    @staticmethod
    def generateSchema(columns_info) -> StructType:
        type_mapping = {
            "string": StringType(),
            "int": IntegerType()        
        }
        
        fields = []
        for name, dtype in columns_info:           
            if isinstance(dtype, str):
                dtype = type_mapping.get(dtype.lower(), StringType())
            fields.append(StructField(name, dtype, True))
        
        return StructType(fields)



#from spark_utils import SparkUtils
#from spark_utils import SparkUtils
#from pyspark.sql.types import StructType, StructField, StringType, IntegerType

#schema = SparkUtils.generateSchema([("name", "string"), ("age", "int"), ("age", "string")])
#schema