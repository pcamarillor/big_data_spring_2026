import argparse

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    to_timestamp,
    to_date,
    date_format,
    round,
    when,
    coalesce,
    sum as spark_sum,
    avg,
    countDistinct
)


parser = argparse.ArgumentParser()

parser.add_argument("--input", required=True)
parser.add_argument("--output", required=True)

args = parser.parse_args()

input_path = args.input.rstrip("/")
output_path = args.output.rstrip("/")



spark = (
    SparkSession.builder
    .appName("Fashion Retail Batch Pipeline")
    .getOrCreate()
)


sales = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv(f"{input_path}/sales/")
)

products = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv(f"{input_path}/products/")
)

customers = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv(f"{input_path}/customers/")
)

stores = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv(f"{input_path}/stores/")
)


products_clean = products.select(
    col("product_id"),
    col("category").alias("product_category"),
    col("product_name").alias("catalog_product_name"),
    col("brand").alias("catalog_brand"),
    col("price").alias("catalog_price"),
    col("cost")
)

customers_clean = customers.select(
    col("customer_id"),
    col("customer_name"),
    col("gender"),
    col("age"),
    col("city").alias("customer_city")
)



sales_clean = (
    sales
    .dropDuplicates(["sale_id"])
    .filter(col("sale_id").isNotNull())
    .filter(col("customer_id").isNotNull())
    .filter(col("product_id").isNotNull())
    .filter(col("store_id").isNotNull())
    .filter(col("quantity") > 0)
    .filter(col("unit_price") > 0)
    .filter((col("discount") >= 0) & (col("discount") <= 0.90))
)



sales_joined = (
    sales_clean
    .join(products_clean, on="product_id", how="left")
    .join(customers_clean, on="customer_id", how="left")
    .join(stores, on="store_id", how="left")
)



sales_final = (
    sales_joined
    .withColumn("sale_time", to_timestamp(col("sale_timestamp")))
    .withColumn("sale_date", to_date(col("sale_time")))
    .withColumn("year_month", date_format(col("sale_time"), "yyyy-MM"))
    .withColumn("final_category", coalesce(col("product_category"), col("category")))
    .withColumn("gross_sales", round(col("quantity") * col("unit_price"), 2))
    .withColumn("discount_amount", round(col("gross_sales") * col("discount"), 2))
    .withColumn("net_sales", round(col("gross_sales") - col("discount_amount"), 2))
    .withColumn("profit", round(col("net_sales") - (col("cost") * col("quantity")), 2))
    .withColumn(
        "age_group",
        when(col("age") < 25, "18-24")
        .when((col("age") >= 25) & (col("age") < 35), "25-34")
        .when((col("age") >= 35) & (col("age") < 45), "35-44")
        .when((col("age") >= 45) & (col("age") < 60), "45-59")
        .otherwise("60+")
    )
    .withColumn(
        "return_status",
        when(col("returned") == True, "returned")
        .otherwise("not_returned")
    )
)



sales_final = (
    sales_final
    .filter(col("sale_time").isNotNull())
    .filter(col("final_category").isNotNull())
    .filter(col("net_sales") > 0)
    .sortWithinPartitions("year_month", "final_category", "channel")
)



monthly_summary = (
    sales_final
    .groupBy("year_month", "final_category", "channel")
    .agg(
        countDistinct("sale_id").alias("total_sales"),
        spark_sum("quantity").alias("total_units"),
        round(spark_sum("gross_sales"), 2).alias("gross_revenue"),
        round(spark_sum("discount_amount"), 2).alias("total_discount"),
        round(spark_sum("net_sales"), 2).alias("net_revenue"),
        round(spark_sum("profit"), 2).alias("total_profit"),
        round(avg("discount"), 4).alias("avg_discount")
    )
)



sales_final.write \
    .mode("overwrite") \
    .partitionBy("year_month") \
    .parquet(f"{output_path}/sales_final")

monthly_summary.write \
    .mode("overwrite") \
    .partitionBy("year_month") \
    .parquet(f"{output_path}/monthly_summary")



print("Sample from sales_final:")
spark.read.parquet(f"{output_path}/sales_final").show(10, truncate=False)

print("Sample from monthly_summary:")
spark.read.parquet(f"{output_path}/monthly_summary").show(10, truncate=False)

spark.stop()