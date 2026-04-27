from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, monotonically_increasing_id
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType, DateType
from faker import Faker
import random, uuid, datetime

spark = SparkSession.builder.appName("GenerateOrdersFaker").getOrCreate()

TOTAL_ROWS = 210_000_000
NUM_PARTITIONS = 200
S3_OUTPUT = "s3://bigdata-batch-delmuro-faker-2026/raw/"

categories = ['electronics', 'clothing', 'home', 'sports', 'books', 'toys']
statuses = ['pending', 'shipped', 'delivered', 'cancelled', 'returned']
payments = ['credit_card', 'debit_card', 'paypal', 'bank_transfer']
products = {
    'electronics': ['Laptop', 'Smartphone', 'Headphones', 'Tablet', 'Smartwatch'],
    'clothing': ['T-Shirt', 'Jeans', 'Jacket', 'Sneakers', 'Dress'],
    'home': ['Blender', 'Lamp', 'Pillow', 'Vacuum', 'Towel Set'],
    'sports': ['Yoga Mat', 'Dumbbells', 'Running Shoes', 'Bicycle', 'Tennis Racket'],
    'books': ['Novel', 'Cookbook', 'Textbook', 'Biography', 'Comic Book'],
    'toys': ['Lego Set', 'Board Game', 'Puzzle', 'Action Figure', 'Stuffed Animal'],
}

schema = StructType([
    StructField("order_id", StringType()),
    StructField("customer_name", StringType()),
    StructField("customer_email", StringType()),
    StructField("country", StringType()),
    StructField("city", StringType()),
    StructField("order_status", StringType()),
    StructField("payment_method", StringType()),
    StructField("product_name", StringType()),
    StructField("category", StringType()),
    StructField("quantity", IntegerType()),
    StructField("unit_price", FloatType()),
    StructField("discount", FloatType()),
    StructField("order_date", StringType()),
    StructField("delivery_date", StringType()),
])


def generate_partition(iterator):
    fake = Faker()
    for row in iterator:
        cat = random.choice(categories)
        status = random.choice(statuses)
        order_date = fake.date_time_between(start_date='-2y', end_date='now')
        delivery_date = (fake.date_time_between(start_date=order_date, end_date='+30d').strftime('%Y-%m-%d %H:%M:%S')
                        if status == 'delivered' else '')
        yield (
            str(uuid.uuid4()),
            fake.name(),
            fake.email(),
            fake.country(),
            fake.city(),
            status,
            random.choice(payments),
            random.choice(products[cat]),
            cat,
            random.randint(1, 10),
            round(random.uniform(5.0, 2000.0), 2),
            round(random.uniform(0.0, 0.5), 2),
            order_date.strftime('%Y-%m-%d %H:%M:%S'),
            delivery_date,
        )


# Crea un DataFrame ficticio con TOTAL_ROWS y luego mapea las particiones con Faker.
dummy = spark.range(0, TOTAL_ROWS, numPartitions=NUM_PARTITIONS)
result = dummy.rdd.mapPartitions(generate_partition).toDF(schema)

result.write.option("header", "true").mode("overwrite").csv(S3_OUTPUT)

spark.stop()
