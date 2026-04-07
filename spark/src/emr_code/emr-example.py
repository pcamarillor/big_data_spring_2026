from pyspark.sql import functions as F
from spark_utils_emr import SparkUtils

su = SparkUtils("emr-test")

# Create sample data
data = [
    ("Mario Kart", 4.8, 1200),
    ("Zelda BOTW", 4.9, 3400),
    ("Animal Crossing", 4.7, 2100),
    ("Smash Bros", 4.6, 1800),
]
df = su.spark.createDataFrame(data, ["game", "rating", "reviews"])

# Run some transformations
result = (df
    .withColumn("weighted_score", F.round(F.col("rating") * F.log(F.col("reviews")), 2))
    .orderBy(F.desc("weighted_score")))

result.write.mode("overwrite").csv("s3://iteso-super-bucket/output/emr-test/")

su.spark.stop()