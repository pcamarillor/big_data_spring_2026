
import boto3
import csv
import json
import time
import io
from kafka import KafkaProducer

BUCKET = "iteso-bucket1"
PREFIX = "data/"
TOPIC = "financial-transactions"
DELAY = 0.1

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

s3 = boto3.client("s3")

response = s3.list_objects_v2(
    Bucket=BUCKET,
    Prefix=PREFIX
)

files = [
    obj["Key"]
    for obj in response.get("Contents", [])
    if obj["Key"].endswith(".csv")
]

for file_key in files:

    obj = s3.get_object(
        Bucket=BUCKET,
        Key=file_key
    )

    body = obj["Body"].read().decode("utf-8")

    reader = csv.DictReader(
        io.StringIO(body)
    )

    for row in reader:
        producer.send(
            TOPIC,
            value=dict(row)
        )

        time.sleep(DELAY)

producer.flush()
