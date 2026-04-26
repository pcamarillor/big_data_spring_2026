"""
E-Commerce Batch Processing Pipeline
=====================================
Procesamiento de Datos Masivos | ITESO

Spark application that reads the synthetic e-commerce dataset from S3,
applies a series of transformations, and persists the results in Parquet
format partitioned by year and category.

All transformations are defined lazily.  The .write() calls in Section 6
are the only actions — they trigger the full DAG evaluation in one pass.

Dataset layout on S3 (produced by data_producer.py cloud mode):
    s3://<BUCKET>/data/customers/   -- dimension table (CSV files)
    s3://<BUCKET>/data/products/    -- dimension table (CSV files)
    s3://<BUCKET>/data/orders/      -- fact table      (CSV files)

Transformations implemented
---------------------------
1. Data Cleaning      — null handling, duplicate removal, invalid-record filter
2. Column Derivation  — gross_revenue, net_revenue, discount_amount,
                        revenue_tier, discount_level, shipping_speed (expressions)
                        age_group (Python UDF)
3. Aggregations       — revenue by region, by category/year, top products,
                        premium analysis, age-group breakdown
4. Joins              — orders x customers (inner), result x products (left)
5. Filtering/Sorting  — high-value completed orders from premium customers

Submit to EMR
-------------
spark-submit \\
  --deploy-mode cluster \\
  --py-files s3://<BUCKET>/scripts/spark_emr_utils.py \\
  s3://<BUCKET>/scripts/spark_app.py \\
  --bucket <BUCKET>
"""

import argparse

from batch_processing_project.spark_emr_utils import SparkUtils

from pyspark.sql.functions import (
    col, count, avg, desc, when,
    sum   as _sum,
    round as _round,
    udf,
)
from pyspark.sql.types import StringType


# ─────────────────────────────────────────────
# UDF — customer age group
# Registered at module level so EMR serialises it once per executor.
# ─────────────────────────────────────────────
@udf(returnType=StringType())
def age_group_udf(age):
    if age is None:
        return "UNKNOWN"
    if age <= 25:
        return "YOUNG"
    elif age <= 44:
        return "ADULT"
    else:
        return "SENIOR"


# ─────────────────────────────────────────────
# Schema definitions  (SparkUtils tuple format)
# ─────────────────────────────────────────────
CUSTOMERS_SCHEMA = [
    ("customer_id",    "int"),
    ("first_name",     "string"),
    ("last_name",      "string"),
    ("email",          "string"),
    ("phone",          "string"),
    ("region",         "string"),
    ("city",           "string"),
    ("zip_code",       "string"),
    ("signup_date",    "string"),
    ("is_premium",     "string"),
    ("lifetime_spend", "float"),
    ("age",            "int"),
]

PRODUCTS_SCHEMA = [
    ("product_id",  "int"),
    ("name",        "string"),
    ("category",    "string"),
    ("subcategory", "string"),
    ("brand",       "string"),
    ("unit_price",  "float"),
    ("cost",        "float"),
    ("stock",       "int"),
    ("weight_kg",   "float"),
    ("is_active",   "string"),
    ("rating",      "float"),
    ("launch_date", "string"),
]

ORDERS_SCHEMA = [
    ("order_id",        "int"),
    ("customer_id",     "int"),
    ("product_id",      "int"),
    ("order_date",      "string"),
    ("year",            "string"),
    ("month",           "string"),
    ("category",        "string"),
    ("region",          "string"),
    ("quantity",        "int"),
    ("unit_price",      "float"),
    ("discount",        "float"),
    ("total_amount",    "float"),
    ("payment_method",  "string"),
    ("status",          "string"),
    ("shipping_days",   "int"),
    ("is_returned",     "string"),
    ("warehouse_id",    "int"),
    ("coupon_code",     "string"),
    ("device_type",     "string"),
    ("referral_source", "string"),
]


# ─────────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────────
def main(bucket: str):

    INPUT_PATH  = f"s3://{bucket}/data"
    OUTPUT_PATH = f"s3://{bucket}/output/ecommerce_parquet"
    AGG_PATH    = f"s3://{bucket}/output/agg"
    APP_NAME    = "ECommerce-Batch-Pipeline"

    su    = SparkUtils(APP_NAME)
    spark = su.spark

    print(f"\n{'='*60}")
    print(f"  {APP_NAME}")
    print(f"  Procesamiento de Datos Masivos | ITESO")
    print(f"  Bucket : {bucket}")
    print(f"{'='*60}\n")

    # ──────────────────────────────────────────
    # 1. INGEST 
    # ──────────────────────────────────────────
    print("[1/6] Ingesting data from S3...")

    customers_df = su.read_csv(f"{INPUT_PATH}/customers/", CUSTOMERS_SCHEMA)
    products_df  = su.read_csv(f"{INPUT_PATH}/products/",  PRODUCTS_SCHEMA)
    orders_df    = su.read_csv(f"{INPUT_PATH}/orders/",    ORDERS_SCHEMA)

    # printSchema reads metadata from the logical plan — no data scan
    customers_df.printSchema()
    products_df.printSchema()
    orders_df.printSchema()

    # ──────────────────────────────────────────
    # 2. DATA CLEANING  
    # ──────────────────────────────────────────
    print("\n[2/6] Data Cleaning...")

    orders_clean = (
        orders_df
        .dropna(subset=["order_id", "customer_id", "product_id", "total_amount"])
        .fillna({"coupon_code": "NONE", "shipping_days": 0, "discount": 0.0})
        .dropDuplicates(["order_id"])
        .filter(col("status").isin(["completed", "shipped", "pending"]))
        .filter((col("total_amount") > 0) & (col("quantity") > 0))
    )

    customers_clean = (
        customers_df
        .fillna({"city": "unknown", "zip_code": "00000", "lifetime_spend": 0.0})
        .dropDuplicates(["customer_id"])
    )

    products_clean = (
        products_df
        .fillna({"subcategory": "General", "rating": 0.0, "stock": 0})
        .dropDuplicates(["product_id"])
    )

    # Cache is lazy — no computation triggered here.
    # The plan is materialised the first time a write action hits these nodes.
    orders_clean.cache()
    customers_clean.cache()
    products_clean.cache()

    # ──────────────────────────────────────────
    # 3. COLUMN DERIVATION  
    #
    # total_amount in the source = qty * unit_price * (1 - discount).
    # gross_revenue recomputes the pre-discount value; net_revenue recomputes
    # the post-discount value explicitly so the lineage is transparent.
    # ──────────────────────────────────────────
    print("\n[3/6] Column Derivation...")

    orders_enriched = (
        orders_clean
        .withColumn("gross_revenue",
                    _round(col("quantity") * col("unit_price"), 2))
        .withColumn("net_revenue",
                    _round(col("quantity") * col("unit_price") * (1 - col("discount")), 2))
        .withColumn("discount_amount",
                    _round(col("gross_revenue") - col("net_revenue"), 2))
        .withColumn("revenue_tier",
                    when(col("net_revenue") < 500,  "LOW")
                    .when(col("net_revenue") < 5000, "MEDIUM")
                    .otherwise("HIGH"))
        .withColumn("discount_level",
                    when(col("discount") == 0.0,   "NO_DISCOUNT")
                    .when(col("discount") <= 0.15, "LOW_DISCOUNT")
                    .when(col("discount") <= 0.30, "MID_DISCOUNT")
                    .otherwise("HIGH_DISCOUNT"))
        .withColumn("shipping_speed",
                    when(col("shipping_days") <= 3,  "EXPRESS")
                    .when(col("shipping_days") <= 7, "STANDARD")
                    .otherwise("SLOW"))
    )

    # ──────────────────────────────────────────
    # 4. JOINS  
    # ──────────────────────────────────────────
    print("\n[4/6] Joins...")

    orders_with_customers = orders_enriched.join(
        customers_clean.select(
            "customer_id", "first_name", "last_name",
            "city", "is_premium", "age",
        ),
        on="customer_id",
        how="inner",
    )

    # UDF column — age_group derived from the age column brought by the join
    orders_with_customers = orders_with_customers.withColumn(
        "age_group", age_group_udf(col("age"))
    )

    full_df = orders_with_customers.join(
        (
            products_clean
            .select("product_id", "name", "brand", "category", "unit_price", "cost", "rating")
            .withColumnRenamed("name",       "product_name")
            .withColumnRenamed("category",   "product_category")
            .withColumnRenamed("unit_price", "product_unit_price")
        ),
        on="product_id",
        how="left",
    )

    # profit_margin: (net revenue - cost of goods) / net revenue * 100
    full_df = full_df.withColumn(
        "profit_margin",
        _round(
            (col("net_revenue") - col("cost") * col("quantity")) / col("net_revenue") * 100,
            2,
        ),
    )

    # Cache is lazy — triggered on the first write that reads full_df.
    # Avoids recomputing the join plan for every aggregation write below.
    full_df.cache()

    # ──────────────────────────────────────────
    # 5. AGGREGATIONS & FILTERING
    #
    # All DataFrames defined here remain unevaluated until a write() call
    # in Section 6 triggers the DAG execution.
    # ──────────────────────────────────────────
    print("\n[5/6] Defining aggregations and filter (lazy)...")

    # 5a — Revenue by region
    revenue_by_region = (
        full_df
        .groupBy("region")
        .agg(
            count("*").alias("total_orders"),
            _round(_sum("net_revenue"),  2).alias("total_revenue"),
            _round(avg("net_revenue"),   2).alias("avg_order_value"),
            _round(avg("profit_margin"), 2).alias("avg_profit_margin"),
        )
        .orderBy(desc("total_revenue"))
    )

    # 5b — Revenue by category and year
    revenue_by_category_year = (
        full_df
        .groupBy("category", "year")
        .agg(
            count("*").alias("total_orders"),
            _round(_sum("net_revenue"), 2).alias("total_revenue"),
            _round(avg("discount"),     2).alias("avg_discount"),
        )
        .orderBy("year", desc("total_revenue"))
    )

    # 5c — Top 10 products by revenue
    top_products = (
        full_df
        .groupBy("product_id", "product_name", "brand", "product_category")
        .agg(
            count("*").alias("times_sold"),
            _round(_sum("net_revenue"),  2).alias("total_revenue"),
            _round(avg("profit_margin"), 2).alias("avg_profit_margin"),
        )
        .orderBy(desc("total_revenue"))
        .limit(10)
    )

    # 5d — Premium vs non-premium customers
    premium_analysis = (
        full_df
        .groupBy("is_premium")
        .agg(
            count("*").alias("total_orders"),
            _round(_sum("net_revenue"),  2).alias("total_revenue"),
            _round(avg("net_revenue"),   2).alias("avg_order_value"),
            _round(avg("shipping_days"), 1).alias("avg_shipping_days"),
        )
        .orderBy(desc("total_revenue"))
    )

    # 5e — Age-group x category breakdown  (uses the UDF-derived column)
    age_group_analysis = (
        full_df
        .groupBy("age_group", "category")
        .agg(
            count("*").alias("total_orders"),
            _round(avg("net_revenue"), 2).alias("avg_order_value"),
        )
        .orderBy("age_group", desc("avg_order_value"))
    )

    # 5f — Filter: high-value completed orders from premium customers
    high_value_orders = (
        full_df
        .filter(
            (col("is_premium")   == "True") &
            (col("revenue_tier") == "HIGH") &
            (col("status")       == "completed")
        )
        .select(
            "order_id", "first_name", "last_name", "region",
            "product_name", "net_revenue", "profit_margin",
            "shipping_speed", "age_group",
        )
        .orderBy(desc("net_revenue"))
    )

    # ──────────────────────────────────────────
    # 6. PERSIST  — all .write() calls are the only actions in the pipeline.
    #    Each write triggers the DAG from source to that output.
    #    full_df is cached so the join plan is not recomputed for every agg.
    # ──────────────────────────────────────────
    print(f"\n[6/6] Persisting results to S3...")

    # Main enriched dataset — partitioned by year and category
    print(f"  Writing full dataset  -> {OUTPUT_PATH}")
    full_df.write \
        .mode("overwrite") \
        .partitionBy("year", "category") \
        .parquet(OUTPUT_PATH)

    # Analytical summaries
    print(f"  Writing aggregations -> {AGG_PATH}/")

    revenue_by_region.write \
        .mode("overwrite") \
        .parquet(f"{AGG_PATH}/revenue_by_region")

    revenue_by_category_year.write \
        .mode("overwrite") \
        .parquet(f"{AGG_PATH}/revenue_by_category_year")

    top_products.write \
        .mode("overwrite") \
        .parquet(f"{AGG_PATH}/top_products")

    premium_analysis.write \
        .mode("overwrite") \
        .parquet(f"{AGG_PATH}/premium_analysis")

    age_group_analysis.write \
        .mode("overwrite") \
        .parquet(f"{AGG_PATH}/age_group_analysis")

    high_value_orders.write \
        .mode("overwrite") \
        .parquet(f"{AGG_PATH}/high_value_orders")

    print("\n[DONE] Pipeline completed successfully.")
    print(f"  Main output : {OUTPUT_PATH}")
    print(f"  Aggregations: {AGG_PATH}/")

    orders_clean.unpersist()
    customers_clean.unpersist()
    products_clean.unpersist()
    full_df.unpersist()

    spark.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="E-Commerce Batch Processing Pipeline — EMR"
    )
    parser.add_argument(
        "--bucket",
        required=True,
        help="S3 bucket name where the data lives and output will be written.",
    )
    args = parser.parse_args()
    main(args.bucket)
