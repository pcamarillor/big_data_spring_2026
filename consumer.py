from FinalProjectModule.spark_utils_final_project import SparkUtils
from pyspark.sql.functions import from_json, col


mongodb_connector = "org.mongodb.spark:mongo-spark-connector_2.13:10.5.0"
kafka_connector = "org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.0"
su = SparkUtils("Kafka Consumer", 
                "local[*]",
                spark_packages=kafka_connector,mongodb_connector = mongodb_connector)
su.spark

mongo_schema = SparkUtils.generate_schema([
    ("ID", "string"),
    ("Name", "string"),
    ("Address", "string"),
    ("Email", "string"),
    ("Phone", "string"),
    ("Job", "string"),
    ("Company", "string"),
    ("DOB", "string"),
    ("CreditCard", "string"),
    ("IP", "string"),
    ("Notes", "string")
])

mongo_stream = su.spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9093") \
    .option("subscribe", "synthetic_data") \
    .load()

logs_df = mongo_stream.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), mongo_schema).alias("data")) \
    .select("data.*")


transformed_df = logs_df.na.fill("Without Job", subset=["Job"]) \
    .filter(col("ID").isNotNull()) \
    .groupBy("Job") \
    .count()


#----- WRITE TO MONGODB ------

mongo_uri = "mongodb://mongodb-iteso:27017"

def write_to_mongo(batch_df, batch_id):
    batch_df.write \
        .format("mongodb") \
        .mode("append") \
        .option("connection.uri", mongo_uri) \
        .option("database", "final_project") \
        .option("collection", "synthetic_records") \
        .option("writeConcern.w", "1") \
        .option("writeConcern.journal", "true") \
        .option("idFieldList", "Job") \
        .option("operationType", "replace") \
        .option("upsertDocument", "true") \
        .save()

(transformed_df.writeStream
    .outputMode("update")
    .foreachBatch(write_to_mongo)
    .option("checkpointLocation", "/tmp/mongo_checkpoint_2")
    .start()
)


su.spark.streams.awaitAnyTermination()

##PRODUCER
# docker exec -it spark-cluster-spark-notebook-1 python3 /opt/spark/work-dir/src/producers/kafka_producer_final_project.py --broker kafka-kafka-1:9093 --topic synthetic_data --records 1000 --delay 0.5

## consumer
#CONNECT TO INTERNET
# docker exec -it spark-cluster-spark-notebook-1 rm -rf /tmp/mongo_checkpoint_2
# docker exec -it spark-cluster-spark-notebook-1 python3 /opt/spark/work-dir/notebooks/examples/consumer.py

## mongo
# docker exec -it 7c48197d3156 mongosh


# db.synthetic_records.aggregate([
#   { 
#     $sort: { count: -1 } 
#   },
#   { 
#     $limit: 5 
#   },
#   {
#     $project: {
#       _id: 0,
#       Job: 1,
#       total_count: "$count"
#     }
#   }
# ])