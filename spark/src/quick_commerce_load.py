from pyspark.sql.types import StructType, StructField, LongType, StringType, IntegerType, FloatType
from pyspark.sql import SparkSession

# Initialize Spark Session
spark = SparkSession.builder.appName("QuickCommerceAnalysis").getOrCreate()

# Define corrected schema
QuickCommerce_schema = StructType([
    StructField("Order_ID", LongType(), True),
    StructField("Company", StringType(), True),
    StructField("City", StringType(), True),
    StructField("CustomerAge", IntegerType(), True),
    StructField("Order_value", FloatType(), True),
    StructField("Delivery_time_min", FloatType(), True),
    StructField("Distance_km", FloatType(), True),
    StructField("Items_count", FloatType(), True),
    StructField("Product_category", StringType(), True),
    StructField("Payment_method", StringType(), True),
    StructField("Customer-rating", FloatType(), True),
    StructField("Discount_applied", FloatType(), True),
    StructField("Delivery_partner_rating", FloatType(), True)
])

# Load data
csv_path = r"../data/quick_commerce_data_raw.csv"
df = spark.read.csv(csv_path, header=True, schema=QuickCommerce_schema)

# Show schema and data
df.printSchema()
df.show(5)
