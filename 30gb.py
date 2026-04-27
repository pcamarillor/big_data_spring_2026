import json
import uuid
import random
import boto3
import io
import gzip
from faker import Faker
from datetime import datetime, timedelta
import time

fake = Faker()
random.seed(42)


BUCKET       = "batch-proc-proy1"          
S3_PREFIX    = "raw/transactions/"
TOTAL_ROWS   = 240_000_000                 
CHUNK_SIZE   = 500_000                     


CATEGORIES    = ["electronics","clothing","books","home","sports",
                 "beauty","toys","automotive","grocery","music"]
PAYMENT_METHODS = ["credit_card","debit_card","paypal","crypto","bank_transfer"]
DEVICE_TYPES  = ["mobile","desktop","tablet"]
COUNTRIES     = [fake.country_code() for _ in range(40)]

s3 = boto3.client("s3")

def make_seller_pool(n=5000):
    return [str(uuid.uuid4()) for _ in range(n)]

def generate_record(seller_pool):
    unit_price   = round(random.uniform(1.0, 2000.0), 2)
    quantity     = random.randint(1, 20)
    discount_pct = round(random.uniform(0.0, 0.50), 3) if random.random() > 0.3 else None
    effective_discount = discount_pct if discount_pct else 0.0
    total_price  = round(unit_price * quantity * (1 - effective_discount), 2)

    return {
        "transaction_id":  str(uuid.uuid4()),
        "user_id":         str(uuid.uuid4()),
        "product_id":      str(uuid.uuid4()),
        "category":        random.choice(CATEGORIES),
        "product_name":    fake.catch_phrase(),
        "quantity":        quantity,
        "unit_price":      unit_price,
        "discount_pct":    discount_pct,          # intentional nulls
        "total_price":     total_price,
        "payment_method":  random.choice(PAYMENT_METHODS),
        "country":         random.choice(COUNTRIES),
        "timestamp":       (datetime(2023,1,1) +
                            timedelta(seconds=random.randint(0, 63_072_000))
                           ).isoformat(),
        "seller_id":       random.choice(seller_pool),
        "is_returned":     random.random() < 0.08,
        "device_type":     random.choice(DEVICE_TYPES),
        "review_score":    random.choice([1,2,3,4,5,None]),  # intentional nulls
    }

def upload_chunk(rows, chunk_index, max_retries=5):
    key = f"{S3_PREFIX}part-{chunk_index:05d}.json.gz"
    
    
    try:
        s3.head_object(Bucket=BUCKET, Key=key)
        print(f"  skipping {key} (already exists)")
        return
    except:
        pass

    for attempt in range(max_retries):
        try:
            buf = io.BytesIO()
            with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
                for row in rows:
                    gz.write((json.dumps(row) + "\n").encode())
            buf.seek(0)
            s3.upload_fileobj(
                buf, BUCKET, key,
                ExtraArgs={"ContentType": "application/gzip"},
                Config=boto3.s3.transfer.TransferConfig(
                    multipart_threshold=50 * 1024 * 1024,
                    multipart_chunksize=10 * 1024 * 1024,
                    max_concurrency=2,
                )
            )
            print(f"  uploaded {key}  ({len(rows):,} rows)")
            return
        except Exception as e:
            wait = 10 * (attempt + 1)
            print(f"  ERROR en {key}, intento {attempt+1}/{max_retries}: {e}")
            print(f"  reintentando en {wait}s...")
            time.sleep(wait)
    
    print(f"  FALLO PERMANENTE en {key} después de {max_retries} intentos")


def main():
    seller_pool = make_seller_pool()
    chunk, chunk_idx = [], 0

    for i in range(TOTAL_ROWS):
        chunk.append(generate_record(seller_pool))
        if len(chunk) == CHUNK_SIZE:
            upload_chunk(chunk, chunk_idx)
            chunk_idx += 1
            chunk = []

    if chunk:
        upload_chunk(chunk, chunk_idx)

    print(f"\nDone — {TOTAL_ROWS:,} records en {chunk_idx+1} chunks.")


if __name__ == "__main__":
    main()