from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    FloatType,
    BooleanType
)
from faker import Faker
import random
import uuid
from datetime import datetime, timedelta



TOTAL_ROWS = 200_000_000
NUM_PARTITIONS = 200

S3_OUTPUT = "s3://fashion-retail-batch-ikramzaldivar/raw/fashion_retail/"


spark = (
    SparkSession.builder
    .appName("GenerateFashionRetailData")
    .getOrCreate()
)



categories = ["clothing", "shoes", "accessories", "beauty"]

products_by_category = {
    "clothing": ["Dress", "Jeans", "Jacket", "T-Shirt", "Skirt", "Blouse"],
    "shoes": ["Sneakers", "Boots", "Heels", "Sandals", "Loafers"],
    "accessories": ["Bag", "Belt", "Sunglasses", "Necklace", "Scarf"],
    "beauty": ["Lipstick", "Foundation", "Mascara", "Perfume", "Skincare Set"]
}

brands = [
    "Urban Muse",
    "Nova Chic",
    "Velvet Lane",
    "Aura Beauty",
    "Luna Wear",
    "Casa Denim"
]

channels = ["store", "web", "mobile_app"]

payment_methods = [
    "credit_card",
    "debit_card",
    "cash",
    "paypal"
]

cities = [
    "Guadalajara",
    "Zapopan",
    "CDMX",
    "Monterrey",
    "Queretaro",
    "Puebla"
]

states = [
    "Jalisco",
    "CDMX",
    "Nuevo Leon",
    "Queretaro",
    "Puebla"
]



sales_schema = StructType([
    StructField("sale_id", StringType(), True),
    StructField("sale_timestamp", StringType(), True),
    StructField("customer_id", StringType(), True),
    StructField("product_id", StringType(), True),
    StructField("store_id", StringType(), True),
    StructField("category", StringType(), True),
    StructField("product_name", StringType(), True),
    StructField("brand", StringType(), True),
    StructField("channel", StringType(), True),
    StructField("quantity", IntegerType(), True),
    StructField("unit_price", FloatType(), True),
    StructField("discount", FloatType(), True),
    StructField("payment_method", StringType(), True),
    StructField("returned", BooleanType(), True),
    StructField("city", StringType(), True),
    StructField("state", StringType(), True)
])



def generate_sales_partition(iterator):
    fake = Faker("es_MX")

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 4, 1)
    total_seconds = int((end_date - start_date).total_seconds())

    for row in iterator:
        category = random.choice(categories)
        product_name = random.choice(products_by_category[category])
        sale_date = start_date + timedelta(seconds=random.randint(0, total_seconds))

        quantity = random.randint(1, 5)
        unit_price = round(random.uniform(150, 5000), 2)
        discount = random.choice([0.0, 0.05, 0.10, 0.15, 0.20])

        customer_number = random.randint(1, 500000)
        product_number = random.randint(1, 50000)
        store_number = random.randint(1, 300)

        yield (
            str(uuid.uuid4()),
            sale_date.strftime("%Y-%m-%d %H:%M:%S"),
            f"C{customer_number}",
            f"P{product_number}",
            f"S{store_number}",
            category,
            product_name,
            random.choice(brands),
            random.choice(channels),
            quantity,
            unit_price,
            discount,
            random.choice(payment_methods),
            random.choice([True, False]),
            random.choice(cities),
            random.choice(states)
        )


print("Generating sales data...")

dummy_data = spark.range(
    0,
    TOTAL_ROWS,
    numPartitions=NUM_PARTITIONS
)

sales_df = dummy_data.rdd.mapPartitions(
    generate_sales_partition
).toDF(sales_schema)

sales_df.write \
    .option("header", "true") \
    .mode("overwrite") \
    .csv(S3_OUTPUT + "sales/")



print("Generating products table...")

products_data = []

for i in range(1, 50001):
    category = random.choice(categories)
    product_name = random.choice(products_by_category[category])
    price = round(random.uniform(150, 5000), 2)
    cost = round(price * random.uniform(0.40, 0.70), 2)

    products_data.append((
        f"P{i}",
        category,
        product_name,
        random.choice(brands),
        price,
        cost
    ))

products_schema = StructType([
    StructField("product_id", StringType(), True),
    StructField("category", StringType(), True),
    StructField("product_name", StringType(), True),
    StructField("brand", StringType(), True),
    StructField("price", FloatType(), True),
    StructField("cost", FloatType(), True)
])

products_df = spark.createDataFrame(products_data, products_schema)

products_df.coalesce(1).write \
    .option("header", "true") \
    .mode("overwrite") \
    .csv(S3_OUTPUT + "products/")



print("Generating customers table...")

fake = Faker("es_MX")
customers_data = []

for i in range(1, 500001):
    customers_data.append((
        f"C{i}",
        fake.name(),
        random.choice(["female", "male", "other"]),
        random.randint(18, 70),
        random.choice(cities)
    ))

customers_schema = StructType([
    StructField("customer_id", StringType(), True),
    StructField("customer_name", StringType(), True),
    StructField("gender", StringType(), True),
    StructField("age", IntegerType(), True),
    StructField("city", StringType(), True)
])

customers_df = spark.createDataFrame(customers_data, customers_schema)

customers_df.coalesce(1).write \
    .option("header", "true") \
    .mode("overwrite") \
    .csv(S3_OUTPUT + "customers/")



print("Generating stores table...")

stores_data = []

for i in range(1, 301):
    stores_data.append((
        f"S{i}",
        random.choice(cities),
        random.choice(states),
        random.choice(["mall", "street", "outlet", "flagship"])
    ))

stores_schema = StructType([
    StructField("store_id", StringType(), True),
    StructField("store_city", StringType(), True),
    StructField("store_state", StringType(), True),
    StructField("store_type", StringType(), True)
])

stores_df = spark.createDataFrame(stores_data, stores_schema)

stores_df.coalesce(1).write \
    .option("header", "true") \
    .mode("overwrite") \
    .csv(S3_OUTPUT + "stores/")


print("Fashion retail dataset generated successfully.")

spark.stop()