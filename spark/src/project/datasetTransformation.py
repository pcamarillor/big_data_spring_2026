from pyspark.sql import functions as F
from spark_utils_emr import SparkUtils
import argparse


def main():

    su = SparkUtils("CarRecords")
    
    schema = SparkUtils.generate_schema([
        ("id", "int"),
        ("license_plate", "string"),
        ("registration_date", "date"),
        ("year", "int"),
        ("model", "string"),
        ("brand", "string"),
        ("color", "string"),
        ("motor_no", "string"),
        ("type", "string"),
        ("firstname", "string"),
        ("lastname", "string"),
        ("address", "string"),
        ("municipality", "string"),
        ("state", "string")
    ])

    car_records_path = "s3://pddm-2026-tad-project/projectData/"

    car_records_df = su.spark.read \
                        .option("header", "true") \
                        .schema(schema) \
                        .csv(car_records_path)

    car_records_df = car_records_df.dropDuplicates(["license_plate"])

    filtered_car_records_df = car_records_df.filter(F.year(F.col("registration_date")) >= F.col("year")).filter(F.col("year") > 2010)

    filtered_car_records_df.write.mode("overwrite").partitionBy("state").parquet("s3://pddm-2026-tad-project/output/")

    su.spark.stop()

if __name__ == "__main__":
    main()
