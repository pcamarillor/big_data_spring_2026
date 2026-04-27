from pyspark.sql import functions as F
from spark_utils_emr import SparkUtils
import argparse

# --------------------------------------------------
# EMR code
# Reads raw CSV from S3
# Applies transformations
# --------------------------------------------------

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="S3 input path")
    parser.add_argument("--destination", required=True, help="S3 output path")
    args = parser.parse_args()

    source = args.source
    destination = args.destination

    # Spark Session
    su = SparkUtils("gaming-final-project")
    spark = su.spark


    #Ingestion of the data from the s3 bucket
    df = spark.read.option("header", True).csv(source)

    #DATA CLEANING
    df = df.dropDuplicates()

    #No nulls for text fields
    df = df.fillna({
    "publisher": "Unknown",
    "developer": "Unknown",
    "genre": "Unknown",
    "console": "Unknown",
    "payment_method": "Unknown"
    })

    #No nulls for numeric fields 
    df = df.fillna({
    "critic_score": 0,
    "total_sales": 0,
    "na_sales": 0,
    "jp_sales": 0,
    "pal_sales": 0,
    "other_sales": 0,
    "quantity": 0,
    "discount": 0,
    "price": 0
    })

    #Make data have the right type as in csv is all text data
    df = (df
        .withColumn("critic_score", F.col("critic_score").cast("double"))
        .withColumn("total_sales", F.col("total_sales").cast("double"))
        .withColumn("na_sales", F.col("na_sales").cast("double"))
        .withColumn("jp_sales", F.col("jp_sales").cast("double"))
        .withColumn("pal_sales", F.col("pal_sales").cast("double"))
        .withColumn("other_sales", F.col("other_sales").cast("double"))
        .withColumn("quantity", F.col("quantity").cast("int"))
        .withColumn("discount", F.col("discount").cast("double"))
        .withColumn("price", F.col("price").cast("double"))
        .withColumn("purchase_date", F.to_date("purchase_date", "M/d/yyyy"))
        .withColumn("release_date", F.to_date("release_date", "M/d/yyyy"))
    )

    #Remove records with no purchase date
    df = df.dropna(subset=["purchase_date"])

    #COLUMN DERIVATION
    #Add columns
    df = (df.withColumn("revenue", F.round((F.col("price") * F.col("quantity")) * (1 - F.col("discount")),2 ))
        .withColumn("purchase_year", F.year("purchase_date"))
        .withColumn("purchase_month", F.month("purchase_date"))
        .withColumn("release_year", F.year("release_date"))
        .withColumn("game_age", F.col("purchase_year") - F.col("release_year") )
    )

    #FILTERING AND SORTING
    #Filters by this conditions and shows them in order of their revenue 
    df = (df
        .filter(F.col("genre") == "Action")
        .filter(F.col("payment_method") == "Credit Card")
        .orderBy(F.desc("revenue"))
    )

    # AGGREGATION
    #Shows the most selled games based on revenue
    df = (df
        .groupBy("console", "title")
        .agg(
            F.round(F.sum("revenue"), 2).alias("total_revenue"),
            F.count("*").alias("transactions"),
            F.sum("quantity").alias("units_sold"),
            F.round(F.avg("critic_score"), 2).alias("avg_score")
        )
        .orderBy(F.desc("total_revenue"))
    )
    
    df.write \
        .mode("overwrite") \
        .partitionBy("console") \
        .parquet(destination)

    spark.stop()



if __name__ == "__main__":
    main()
