import json
import uuid
import random
from faker import Faker
from datetime import datetime, timedelta
from kafka import KafkaProducer
import time
import argparse

'''
Para crear el kafka topic ejecutar el siguiente comando en la terminal:

docker exec -it <Kafka container ID> \
     /opt/kafka/bin/kafka-topics.sh \
      --create --zookeeper zookeeper:2181 \
      --replication-factor 1 --partitions 1 \
      --topic store-transactions

Luego, para ejecutar el productor:

docker exec -it <Spark-Notebook container ID> /bin/bash
# cd notebooks/batch_processing
# python3 faker_dataset.py --broker kafka:9093 --topic store-transactions --records 20
'''


fake = Faker()


DELAY_MIN = 5   # seconds
DELAY_MAX = 10  # seconds

CATEGORIES = ['electronics', 'clothing', 'food', 'sports', 'home', 'beauty', 'toys']
STATUSES = ['completed', 'pending', 'cancelled', 'refunded']
PAYMENT_METHODS = ['credit_card', 'debit_card', 'paypal', 'crypto', 'bank_transfer']

def generate_record():
    order_date = fake.date_time_between(start_date='-2y', end_date='now')
    return {
        "transaction_id":   str(uuid.uuid4()),
        "customer_id":      str(uuid.uuid4()),
        "customer_name":    fake.name(),
        "customer_email":   fake.email(),
        "customer_country": fake.country_code(),
        "product_id":       str(uuid.uuid4()),
        "product_name":     fake.catch_phrase(),
        "category":         random.choice(CATEGORIES),
        "quantity":         random.randint(1, 20),
        "unit_price":       round(random.uniform(1.0, 2000.0), 2),
        "total_amount":     round(random.uniform(1.0, 40000.0), 2),
        "discount_pct":     round(random.uniform(0, 50), 2),
        "payment_method":   random.choice(PAYMENT_METHODS),
        "status":           random.choice(STATUSES),
        "order_date":       order_date.strftime('%Y-%m-%d'),
        "order_timestamp":  order_date.strftime('%Y-%m-%d %H:%M:%S'),
        "shipping_country": fake.country_code(),
        "shipping_city":    fake.city(),
        "warehouse_id":     random.randint(1, 50),
        "is_returned":      random.choice([True, False]),
        "review_score":     random.randint(1, 5),
        "review_text":      fake.text(max_nb_chars=200),
    }

def run_producer(args):

    producer = KafkaProducer(
        bootstrap_servers=args.broker,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    print(f"Connected to Kafka broker at {args.broker}")
    print(f"Producing to topic: {args.topic}")
    print(f"Records to produce: {'unlimited' if args.records == 0 else args.records}")
    print(f"Delay between records: {DELAY_MIN}-{DELAY_MAX} seconds")
    print("-" * 50)

    count = 0
    try:
        while args.records == 0 or count < args.records:
            record = generate_record()
            producer.send(args.topic, value=record)
            producer.flush()  # Ensure the message is sent before sleeping

            count += 1
            print(f"[{count}] Sent: {record['transaction_id']}")

            if args.records != 0 and count >= args.records:
                break

            delay = random.randint(DELAY_MIN, DELAY_MAX)
            print(f"    Next record in {delay}s ...")
            time.sleep(delay)
    except KeyboardInterrupt:
        print("\nProducer stopped by user.")
    finally:
        producer.close()
        print(f"Producer closed. Total records sent: {count}")

# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send random log entries to a Kafka topic with a delay between each record."
    )
    parser.add_argument(
        "--broker",
        default="localhost:9092",
        help="Kafka broker address (default: localhost:9092).",
    )
    parser.add_argument(
        "--topic",
        default="server-logs",
        help="Kafka topic name (default: server-logs).",
    )
    parser.add_argument(
        "--records",
        type=int,
        default=0,
        help="Number of records to send. 0 means run indefinitely until Ctrl+C (default: 0).",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    run_producer(args)


if __name__ == "__main__":
    main()