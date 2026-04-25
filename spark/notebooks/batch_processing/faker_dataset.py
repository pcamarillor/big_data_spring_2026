import boto3
import json
import uuid
import random
from faker import Faker
from datetime import datetime, timedelta
import io
import gzip

fake = Faker()
s3 = boto3.client('s3', region_name='us-east-1')

BUCKET = 'batch-processing-s3-746812'
PREFIX = 'raw/transactions/'
RECORDS_PER_FILE = 500_000
NUM_FILES = 60  # ~60 archivos de ~500MB c/u = ~30GB total

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

def upload_file(file_num):
    print(f"Generando archivo {file_num + 1}/{NUM_FILES}...")
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb') as gz:
        for i in range(RECORDS_PER_FILE):
            record = generate_record()
            line = json.dumps(record) + '\n'
            gz.write(line.encode('utf-8'))
    
    buffer.seek(0)
    key = f"{PREFIX}part-{str(file_num).zfill(4)}.json.gz"
    s3.upload_fileobj(buffer, BUCKET, key)
    print(f"Up in: s3://{BUCKET}/{key}")

if __name__ == "__main__":
    print("Iniciando generación de dataset...")
    for i in range(NUM_FILES):
        upload_file(i)
    print("Dataset complete, generated 30GB of data in S3.")