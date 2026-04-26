from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField,
    StringType, IntegerType, LongType, ShortType,
    DoubleType, FloatType, BooleanType,
    DateType, TimestampType, BinaryType, ArrayType
)
from pyspark.sql.functions import col, when, percentile_approx, count, isnull

class SparkUtils:

    def __init__(self, app_name, master_url=None, spark_jars=None, spark_packages=None):
        spark_builder = SparkSession.builder.appName(app_name)
        if master_url is not None:
            spark_builder = spark_builder.master(master_url)
        if spark_jars is not None:
            spark_builder = spark_builder.config("spark.jars", spark_jars)
        if spark_packages is not None:
            spark_builder = spark_builder.config("spark.jars.packages", spark_packages)
        self._spark = spark_builder.getOrCreate()
        self._spark.conf.set("spark.sql.shuffle.partitions", "50")

    @property
    def spark(self):
        return self._spark

    @staticmethod
    def generate_schema(columns_info) -> StructType:
        type_mapping = {
            "string":       StringType(),
            "int":          IntegerType(),
            "long":         LongType(),
            "short":        ShortType(),
            "double":       DoubleType(),
            "float":        FloatType(),
            "boolean":      BooleanType(),
            "date":         DateType(),
            "timestamp":    TimestampType(),
            "binary":       BinaryType(),
            "array_int":    ArrayType(IntegerType()),
            "array_string": ArrayType(StringType()),
            "struct":       StructType(),
        }
        struct_fields = []
        for column_info in columns_info:
            col_name = column_info[0]
            col_type = column_info[1]
            if col_type == "struct":
                if len(column_info) < 3 or not isinstance(column_info[2], list):
                    raise ValueError(f"Column '{col_name}' needs sub-fields list.")
                nested_schema = SparkUtils.generate_schema(column_info[2])
                struct_field  = StructField(col_name, nested_schema, True)
            elif col_type not in type_mapping:
                raise ValueError(f"Unsupported type: '{col_type}' for column '{col_name}'")
            else:
                struct_field = StructField(col_name, type_mapping[col_type], True)
            struct_fields.append(struct_field)
        return StructType(struct_fields)

    @staticmethod
    def count_nulls(df):
        return df.select([count(when(isnull(c), c)).alias(c) for c in df.columns])


class Percentiles:
    def __init__(self, arr):
        self._01 = arr[0]
        self._99 = arr[1]


BUCKET           = "emr-proyecto-058264391995-us-east-1-an"
IMPRESSIONS_PATH = f"s3://{BUCKET}/data/impressions/"
CAMPAIGNS_PATH   = f"s3://{BUCKET}/data/campaigns/"
OUTPUT_PATH      = f"s3://{BUCKET}/output/clean_data/"

LOW  = 0.01
HIGH = 0.99
SHUFFLE_PARTITIONS = 50

IMPRESSIONS_COLS = [
    "impression_id",
    "day",
    "campaign_id",
    "ad_category",
    "country",
    "device_type",
    "bid_price_usd",
    "floor_price_usd",
    "quality_score",
    "predicted_ctr",
    "label",
    "is_weekend",
]

CAMPAIGNS_COLS = [
    "campaign_id",
    "advertiser_name",
    "campaign_type",
    "budget_usd",
    "is_active",
]


def main():
    su    = SparkUtils("BigData-FinalProject-AdTech")
    spark = su.spark
    spark.sparkContext.setLogLevel("WARN")

    SHUFFLE_PARTITIONS = 50
    spark.conf.set("spark.sql.shuffle.partitions", str(SHUFFLE_PARTITIONS))

    impressions_schema = SparkUtils.generate_schema([
        ("impression_id",    "string"),
        ("timestamp",        "timestamp"),
        ("day",              "int"),
        ("user_id",          "string"),
        ("session_id",       "string"),
        ("device_type",      "string"),
        ("os",               "string"),
        ("browser",          "string"),
        ("country",          "string"),
        ("region",           "string"),
        ("city",             "string"),
        ("ad_id",            "string"),
        ("campaign_id",      "string"),
        ("advertiser_id",    "string"),
        ("ad_category",      "string"),
        ("ad_position",      "string"),
        ("ad_format",        "string"),
        ("page_url_hash",    "string"),
        ("referrer_hash",    "string"),
        ("user_age_bucket",  "string"),
        ("user_gender",      "string"),
        ("user_interest_1",  "string"),
        ("user_interest_2",  "string"),
        ("page_views_today", "int"),
        ("time_on_site_sec", "int"),
        ("recency_days",     "int"),
        ("frequency_30d",    "int"),
        ("bid_price_usd",    "double"),
        ("floor_price_usd",  "double"),
        ("quality_score",    "double"),
        ("predicted_ctr",    "double"),
        ("hour_of_day",      "int"),
        ("day_of_week",      "int"),
        ("is_weekend",       "int"),
        ("label",            "int"),
    ])

    campaigns_schema = SparkUtils.generate_schema([
        ("campaign_id",      "string"),
        ("campaign_name",    "string"),
        ("advertiser_name",  "string"),
        ("campaign_type",    "string"),
        ("ad_category",      "string"),
        ("target_country",   "string"),
        ("budget_usd",       "double"),
        ("start_date",       "date"),
        ("end_date",         "date"),
        ("is_active",        "int"),
    ])

    impressions_raw = (
        spark.read
        .schema(impressions_schema)
        .option("sep", "\t")
        .option("header", "true")
        .option("timestampFormat", "yyyy-MM-dd'T'HH:mm:ss")
        .csv(IMPRESSIONS_PATH)
    )

    campaigns_raw = (
        spark.read
        .schema(campaigns_schema)
        .option("sep", "\t")
        .option("header", "true")
        .option("dateFormat", "yyyy-MM-dd")
        .csv(CAMPAIGNS_PATH)
    )

    imp_percentiles = impressions_raw.select(
        percentile_approx("bid_price_usd",   [LOW, HIGH]).alias("bid_p"),
        percentile_approx("floor_price_usd", [LOW, HIGH]).alias("floor_p"),
        percentile_approx("quality_score",   [LOW, HIGH]).alias("qs_p"),
        percentile_approx("predicted_ctr",   [LOW, HIGH]).alias("ctr_p"),
    ).first()

    camp_percentiles = campaigns_raw.select(
        percentile_approx("budget_usd", [LOW, HIGH]).alias("budget_p"),
    ).first()

    bid_p    = Percentiles(imp_percentiles["bid_p"])
    floor_p  = Percentiles(imp_percentiles["floor_p"])
    qs_p     = Percentiles(imp_percentiles["qs_p"])
    ctr_p    = Percentiles(imp_percentiles["ctr_p"])
    budget_p = Percentiles(camp_percentiles["budget_p"])

    impressions_clean = (
        impressions_raw
        .select(IMPRESSIONS_COLS)
        .dropna()
        .dropDuplicates(["impression_id"])
        .filter(col("bid_price_usd")  .between(bid_p._01,   bid_p._99))
        .filter(col("floor_price_usd").between(floor_p._01, floor_p._99))
        .filter(col("quality_score")  .between(qs_p._01,    qs_p._99))
        .filter(col("predicted_ctr")  .between(ctr_p._01,   ctr_p._99))
        .filter(col("bid_price_usd")  >= col("floor_price_usd"))
    )

    campaigns_clean = (
        campaigns_raw
        .select(CAMPAIGNS_COLS)
        .dropDuplicates(["campaign_id"])
        .fillna({"is_active": 0})
        .dropna()
        .filter(col("budget_usd").between(budget_p._01, budget_p._99))
    )

    cols = list(set(IMPRESSIONS_COLS + CAMPAIGNS_COLS))

    df = (
        impressions_clean
        .join(campaigns_clean, on="campaign_id", how="left")
        .select(cols)
        .withColumn("revenue",
            col("bid_price_usd") * col("label"))
        .withColumn("bid_margin",
            col("bid_price_usd") - col("floor_price_usd"))
        .withColumn("ctr_error",
            col("predicted_ctr") - col("label"))
        .withColumn("ctr_bucket",
            when(col("predicted_ctr") < 0.05,  "low")
            .when(col("predicted_ctr") < 0.15, "medium")
            .otherwise("high"))
        .withColumn("quality_bucket",
            when(col("quality_score") < 3.0,  "low")
            .when(col("quality_score") < 7.0, "medium")
            .otherwise("high"))
    )

    df.write \
        .mode("overwrite") \
        .partitionBy("day") \
        .parquet(OUTPUT_PATH)

    spark.stop()


if __name__ == "__main__":
    main()