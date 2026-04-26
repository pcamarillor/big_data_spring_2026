from pyspark.sql import SparkSession
import pyspark.sql.functions as F

spark = SparkSession.builder \
    .appName("BigData-Final-Pipeline") \
    .config("spark.hadoop.fs.s3a.impl",
            "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.aws.credentials.provider",
            "com.amazonaws.auth.InstanceProfileCredentialsProvider") \
    .getOrCreate()

BUCKET = "s3a://batch-processing-s3-746812"

# 1. Read raw data from S3
df_raw = spark.read.json(f"{BUCKET}/raw/transactions/")

# 2. Data Cleaning — drop duplicates and delete nulls in critical fields
df_clean = df_raw.dropDuplicates(["transaction_id"]) \
    .dropna(subset=["transaction_id", "customer_id",
                    "category", "total_amount"])

# 3. Derived columns — calculate revenue after discount and extract order year
df_enriched = df_clean \
    .withColumn("revenue_after_discount",
                F.round(F.col("total_amount") * (1 - F.col("discount_pct") / 100), 2)) \
    .withColumn("order_year",
                F.year(F.to_date(F.col("order_date"))))

# 4. Filtering — exclude cancelled transactions and invalid amounts
df_filtered = df_enriched.filter(
    (F.col("status") != "cancelled") & (F.col("total_amount") > 0)
)

# 5. Aggregation — metrics by category and year
df_agg = df_filtered.groupBy("category", "order_year") \
    .agg(
        F.count("transaction_id").alias("total_transactions"),
        F.round(F.sum("revenue_after_discount"), 2).alias("total_revenue"),
        F.round(F.avg("review_score"), 2).alias("avg_review_score")
    )

# 6. Join — fill with order count per country
df_country_stats = df_filtered.groupBy("customer_country") \
    .agg(F.count("*").alias("orders_per_country"))

df_final = df_filtered.join(df_country_stats, on="customer_country", how="left")

# 7. Persistence
df_final.write \
    .mode("overwrite") \
    .partitionBy("category") \
    .parquet(f"{BUCKET}/output/transactions_processed/")

print("Pipeline completed successfully.")
spark.stop()