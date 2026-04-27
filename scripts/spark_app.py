#!/usr/bin/env python3

import argparse

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from spark_utils import SparkUtils


class RideShareBatchPipeline:
    """
    Spark batch processing pipeline for ride-sharing trip data.

    Pipeline:
        raw JSONL from S3
        -> cleaning
        -> derived columns
        -> completed-trip filtering
        -> zone dimension join
        -> aggregations
        -> partitioned Parquet output
    """

    def __init__(
        self,
        input_path: str,
        output_path: str,
        master: str = "yarn",
        shuffle_partitions: str = "48",
    ) -> None:
        self.input_path = input_path
        self.output_path = output_path
        self.master = master
        self.shuffle_partitions = shuffle_partitions

        self.spark_utils = SparkUtils(
            app_name="RideSharingBatchProcessingPipeline",
            master_url=self.master,
        )

        self.spark = self.spark_utils.spark
        self.spark.sparkContext.setLogLevel("WARN")
        self.spark.conf.set("spark.sql.shuffle.partitions", self.shuffle_partitions)

    def build_trip_schema(self):
        """Build schema for raw ride-sharing JSONL records."""
        return SparkUtils.generate_schema([
            ("trip_id", "string"),
            ("request_timestamp", "string"),
            ("pickup_timestamp", "string"),
            ("dropoff_timestamp", "string"),
            ("rider_id", "string"),
            ("driver_id", "string"),
            ("pickup_city", "string"),
            ("pickup_zone", "string"),
            ("dropoff_city", "string"),
            ("dropoff_zone", "string"),
            ("trip_distance_km", "double"),
            ("fare_amount", "double"),
            ("tip_amount", "double"),
            ("payment_method", "string"),
            ("vehicle_type", "string"),
            ("trip_status", "string"),
            ("weather_condition", "string"),
            ("surge_multiplier", "double"),
        ])

    def read_raw_data(self) -> DataFrame:
        """Read raw JSONL files from S3."""
        return (
            self.spark.read
            .schema(self.build_trip_schema())
            .json(self.input_path)
        )

    def clean_data(self, df: DataFrame) -> DataFrame:
        """Apply cleaning transformations."""
        return (
            df.dropDuplicates(["trip_id"])
            .dropna(subset=[
                "trip_id",
                "request_timestamp",
                "pickup_timestamp",
                "pickup_city",
                "pickup_zone",
            ])
            .filter(F.col("trip_distance_km") > 0)
            .filter(F.col("fare_amount") >= 0)
            .fillna({
                "payment_method": "unknown",
                "tip_amount": 0.0,
                "surge_multiplier": 1.0,
            })
        )

    def derive_columns(self, df: DataFrame) -> DataFrame:
        """Create derived analytical columns."""
        return (
            df.withColumn("request_ts", F.to_timestamp(F.col("request_timestamp")))
            .withColumn("pickup_ts", F.to_timestamp(F.col("pickup_timestamp")))
            .withColumn("dropoff_ts", F.to_timestamp(F.col("dropoff_timestamp")))
            .withColumn("trip_date", F.to_date(F.col("request_ts")))
            .withColumn("trip_hour", F.hour(F.col("request_ts")))
            .withColumn(
                "total_amount",
                F.round(F.col("fare_amount") + F.col("tip_amount"), 2),
            )
            .withColumn(
                "trip_duration_minutes",
                F.round(
                    (F.col("dropoff_ts").cast("long") - F.col("pickup_ts").cast("long")) / 60,
                    2,
                ),
            )
            .withColumn(
                "revenue_per_km",
                F.round(F.col("total_amount") / F.col("trip_distance_km"), 2),
            )
            .withColumn(
                "is_completed",
                F.when(F.col("trip_status") == "completed", F.lit(True)).otherwise(F.lit(False)),
            )
        )

    def filter_completed_trips(self, df: DataFrame) -> DataFrame:
        """Keep completed trips with valid timestamps and positive duration."""
        return (
            df.filter(F.col("trip_status") == "completed")
            .filter(F.col("dropoff_ts").isNotNull())
            .filter(F.col("trip_duration_minutes") > 0)
            .filter(F.col("trip_date").isNotNull())
        )

    def create_zone_dimension(self) -> DataFrame:
        """Create a small zone dimension DataFrame."""
        zone_rows = [
            ("Guadalajara", "Centro", "urban"),
            ("Guadalajara", "Providencia", "business"),
            ("Guadalajara", "Americana", "nightlife"),
            ("Guadalajara", "Chapultepec", "nightlife"),
            ("Guadalajara", "Oblatos", "residential"),

            ("Zapopan", "Andares", "commercial"),
            ("Zapopan", "Chapalita", "residential"),
            ("Zapopan", "Ciudad Granja", "student"),
            ("Zapopan", "Valle Real", "residential"),
            ("Zapopan", "Tesistan", "suburban"),

            ("Tlaquepaque", "Centro", "tourism"),
            ("Tlaquepaque", "Forum", "commercial"),
            ("Tlaquepaque", "Las Juntas", "industrial"),
            ("Tlaquepaque", "Santa Anita", "suburban"),
            ("Tlaquepaque", "El Alamo", "residential"),

            ("Tonalá", "Centro", "urban"),
            ("Tonalá", "Loma Dorada", "residential"),
            ("Tonalá", "Jauja", "residential"),
            ("Tonalá", "Coyula", "suburban"),
            ("Tonalá", "Puente Grande", "suburban"),

            ("Tlajomulco", "Santa Fe", "residential"),
            ("Tlajomulco", "Cajititlan", "tourism"),
            ("Tlajomulco", "San Agustin", "suburban"),
            ("Tlajomulco", "La Rioja", "residential"),
            ("Tlajomulco", "El Palomar", "residential"),
        ]

        zone_schema = SparkUtils.generate_schema([
            ("zone_city", "string"),
            ("zone_name", "string"),
            ("zone_type", "string"),
        ])

        return self.spark.createDataFrame(zone_rows, zone_schema)

    def join_zone_dimension(self, trips_df: DataFrame, zone_df: DataFrame) -> DataFrame:
        """Join trips with zone dimension."""
        return (
            trips_df.join(
                zone_df,
                (trips_df.pickup_city == zone_df.zone_city)
                & (trips_df.pickup_zone == zone_df.zone_name),
                "left",
            )
            .drop("zone_city", "zone_name")
            .fillna({"zone_type": "unknown"})
        )

    def aggregate_results(self, df: DataFrame) -> DataFrame:
        """Aggregate daily analytical metrics."""
        return (
            df.groupBy(
                "trip_date",
                "pickup_city",
                "vehicle_type",
                "zone_type",
            )
            .agg(
                F.count("*").alias("total_trips"),
                F.sum("total_amount").alias("total_revenue"),
                F.avg("total_amount").alias("avg_total_amount"),
                F.avg("trip_distance_km").alias("avg_distance_km"),
                F.avg("trip_duration_minutes").alias("avg_duration_minutes"),
                F.avg("revenue_per_km").alias("avg_revenue_per_km"),
                F.avg("surge_multiplier").alias("avg_surge_multiplier"),
            )
            .withColumn("total_revenue", F.round(F.col("total_revenue"), 2))
            .withColumn("avg_total_amount", F.round(F.col("avg_total_amount"), 2))
            .withColumn("avg_distance_km", F.round(F.col("avg_distance_km"), 2))
            .withColumn("avg_duration_minutes", F.round(F.col("avg_duration_minutes"), 2))
            .withColumn("avg_revenue_per_km", F.round(F.col("avg_revenue_per_km"), 2))
            .withColumn("avg_surge_multiplier", F.round(F.col("avg_surge_multiplier"), 2))
            .orderBy("trip_date", "pickup_city", "vehicle_type", "zone_type")
        )

    def write_output(self, df: DataFrame) -> None:
        """Write final DataFrame to S3 as partitioned Parquet."""
        (
            df.write
            .mode("overwrite")
            .partitionBy("trip_date")
            .parquet(self.output_path)
        )

    def run(self) -> None:
        """Execute the full Spark pipeline."""
        print(f"Input path  : {self.input_path}")
        print(f"Output path : {self.output_path}")
        print(f"Master      : {self.master}")

        print("Reading raw JSONL data from S3...")
        raw_df = self.read_raw_data()

        print("Applying cleaning transformations...")
        clean_df = self.clean_data(raw_df)

        print("Creating derived columns...")
        derived_df = self.derive_columns(clean_df)

        print("Filtering completed trips...")
        completed_df = self.filter_completed_trips(derived_df)

        print("Creating zone dimension DataFrame...")
        zone_df = self.create_zone_dimension()

        print("Joining trips with zone dimension...")
        enriched_df = self.join_zone_dimension(completed_df, zone_df)

        print("Aggregating analytical results...")
        final_df = self.aggregate_results(enriched_df)

        print("Writing partitioned Parquet output to S3...")
        self.write_output(final_df)

        print("Spark batch pipeline completed successfully.")

    def stop(self) -> None:
        """Stop Spark session."""
        self.spark.stop()


class SparkAppCLI:
    """Command-line interface for the Spark pipeline."""

    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser(
            description="Spark batch pipeline for synthetic ride-sharing trip data."
        )

        parser.add_argument(
            "--input",
            required=True,
            help="S3 input path containing raw JSONL files.",
        )

        parser.add_argument(
            "--output",
            required=True,
            help="S3 output path for transformed Parquet files.",
        )

        parser.add_argument(
            "--master",
            default="yarn",
            help="Spark master URL. Use 'yarn' on EMR and 'local[*]' for local testing.",
        )

        parser.add_argument(
            "--shuffle-partitions",
            default="48",
            help="Number of Spark shuffle partitions.",
        )

        return parser.parse_args()

    def run(self) -> None:
        args = self.parse_args()

        pipeline = RideShareBatchPipeline(
            input_path=args.input,
            output_path=args.output,
            master=args.master,
            shuffle_partitions=args.shuffle_partitions,
        )

        try:
            pipeline.run()
        finally:
            pipeline.stop()


def main() -> None:
    SparkAppCLI().run()


if __name__ == "__main__":
    main()