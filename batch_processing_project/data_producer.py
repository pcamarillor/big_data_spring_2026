"""
E-Commerce Data Producer
========================
Procesamiento de Datos Masivos | ITESO

Generates synthetic e-commerce CSV files (customers, products, orders) using
Faker, following the same local/cloud pattern as logs_producer.py.

The three tables together form a single cohesive e-commerce dataset:
  - customers  : dimension table  (~5 % of total size)
  - products   : dimension table  (~5 % of total size)
  - orders     : fact table       (~90 % of total size)

Usage examples:
  # Local mode — write to a local directory
  python3 data_producer.py local --location ./ecommerce_data --target-gb 1

  # Cloud mode — upload to S3 (run on EC2)
  python3 data_producer.py cloud --bucket my-bucket --target-gb 30

Dependencies:
  pip install faker boto3
"""

import argparse
import csv
import io
import os
import random
from datetime import datetime, timedelta

from faker import Faker

# ─────────────────────────────────────────────
# Faker setup
# ─────────────────────────────────────────────
fake = Faker("es_MX")
Faker.seed(42)
random.seed(42)

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
CATEGORIES = [
    "Electronics", "Clothing", "Home & Garden", "Sports", "Books",
    "Beauty", "Toys", "Food & Beverage", "Automotive", "Health",
]

PAYMENT_METHODS = ["credit_card", "debit_card", "paypal", "oxxo", "bank_transfer"]

ORDER_STATUSES = ["completed", "pending", "cancelled", "refunded", "shipped"]

REGIONS = [
    "CDMX", "Jalisco", "Nuevo Leon", "Puebla", "Yucatan",
    "Veracruz", "Guanajuato", "Chihuahua", "Sonora", "Oaxaca",
]

DEVICE_TYPES = ["mobile", "desktop", "tablet"]

REFERRAL_SOURCES = ["organic", "paid_ad", "email", "social", "direct"]

# Size distribution across tables (must sum to 1.0)
TABLE_WEIGHTS = {
    "customers": 0.05,
    "products":  0.05,
    "orders":    0.90,
}

# Rows generated per file (controls file granularity)
CHUNK_ROWS = 50_000

# Fixed dimension pool sizes — orders reference IDs within these ranges
N_CUSTOMERS = 500_000
N_PRODUCTS  = 100_000


# ─────────────────────────────────────────────
# Row generators
# ─────────────────────────────────────────────
def _rand_date(start_year: int = 2020, end_year: int = 2024) -> str:
    """Return a random YYYY-MM-DD string within the given year range."""
    start = datetime(start_year, 1, 1)
    end   = datetime(end_year, 12, 31)
    return (start + timedelta(days=random.randint(0, (end - start).days))).strftime("%Y-%m-%d")


def customer_row(customer_id: int) -> dict:
    return {
        "customer_id":    customer_id,
        "first_name":     fake.first_name(),
        "last_name":      fake.last_name(),
        "email":          fake.email(),
        "phone":          fake.phone_number(),
        "region":         random.choice(REGIONS),
        "city":           fake.city(),
        "zip_code":       fake.postcode(),
        "signup_date":    _rand_date(2018, 2023),
        "is_premium":     random.choice([True, False]),
        "lifetime_spend": round(random.uniform(50.0, 50_000.0), 2),
        "age":            random.randint(18, 75),
    }


def product_row(product_id: int) -> dict:
    return {
        "product_id":  product_id,
        "name":        fake.catch_phrase(),
        "category":    random.choice(CATEGORIES),
        "subcategory": fake.word().capitalize(),
        "brand":       fake.company(),
        "unit_price":  round(random.uniform(5.0, 5_000.0), 2),
        "cost":        round(random.uniform(1.0, 3_000.0), 2),
        "stock":       random.randint(0, 10_000),
        "weight_kg":   round(random.uniform(0.1, 50.0), 2),
        "is_active":   random.choice([True, False]),
        "rating":      round(random.uniform(1.0, 5.0), 1),
        "launch_date": _rand_date(2015, 2024),
    }


def order_row(order_id: int) -> dict:
    qty        = random.randint(1, 10)
    unit_price = round(random.uniform(5.0, 5_000.0), 2)
    discount   = round(random.uniform(0.0, 0.4), 2)
    order_date = _rand_date(2020, 2024)
    return {
        "order_id":        order_id,
        "customer_id":     random.randint(1, N_CUSTOMERS),
        "product_id":      random.randint(1, N_PRODUCTS),
        "order_date":      order_date,
        "year":            order_date[:4],
        "month":           order_date[5:7],
        "category":        random.choice(CATEGORIES),
        "region":          random.choice(REGIONS),
        "quantity":        qty,
        "unit_price":      unit_price,
        "discount":        discount,
        "total_amount":    round(qty * unit_price * (1 - discount), 2),
        "payment_method":  random.choice(PAYMENT_METHODS),
        "status":          random.choice(ORDER_STATUSES),
        "shipping_days":   random.randint(1, 30),
        "is_returned":     random.choice([True, False]),
        "warehouse_id":    random.randint(1, 20),
        "coupon_code":     fake.bothify(text="??##??##") if random.random() < 0.3 else "",
        "device_type":     random.choice(DEVICE_TYPES),
        "referral_source": random.choice(REFERRAL_SOURCES),
    }


# Field name lists derived once from sample rows
CUSTOMER_FIELDS = list(customer_row(0).keys())
PRODUCT_FIELDS  = list(product_row(0).keys())
ORDER_FIELDS    = list(order_row(0).keys())

TABLE_CONFIG = {
    #  table       (row_fn,       fields)
    "customers": (customer_row, CUSTOMER_FIELDS),
    "products":  (product_row,  PRODUCT_FIELDS),
    "orders":    (order_row,    ORDER_FIELDS),
}


# ─────────────────────────────────────────────
# CSV helpers
# ─────────────────────────────────────────────
def rows_to_csv_bytes(rows: list, fieldnames: list) -> bytes:
    """Serialise a list of row dicts to UTF-8 CSV bytes (header included)."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def estimate_row_size(row_fn, fields: list, samples: int = 500) -> float:
    """Return average bytes per row using a small sample."""
    sample = [row_fn(i) for i in range(samples)]
    return len(rows_to_csv_bytes(sample, fields)) / samples


# ─────────────────────────────────────────────
# Chunk planning
# ─────────────────────────────────────────────
def plan_chunks(target_bytes: int) -> dict:
    """
    Calculate how many files each table needs to collectively
    reach target_bytes, respecting each table's size weight.

    Returns a dict keyed by table name with generation parameters.
    """
    plan = {}
    for table, weight in TABLE_WEIGHTS.items():
        row_fn, fields = TABLE_CONFIG[table]
        table_bytes    = int(target_bytes * weight)
        row_size       = estimate_row_size(row_fn, fields)
        total_rows     = int(table_bytes / row_size)
        n_chunks       = max(1, total_rows // CHUNK_ROWS)
        rows_per_chunk = total_rows // n_chunks

        plan[table] = {
            "chunks":          n_chunks,
            "rows_per_chunk":  rows_per_chunk,
            "bytes_per_chunk": int(rows_per_chunk * row_size),
            "row_fn":          row_fn,
            "fields":          fields,
        }
    return plan


def print_plan(plan: dict, target_gb: float) -> None:
    print(f"\n{'─'*57}")
    print(f"  Target size : {target_gb:.1f} GB")
    print(f"  Rows/file   : {CHUNK_ROWS:,}")
    print(f"{'─'*57}")
    print(f"  {'Table':<12} {'Files':>6} {'Rows/file':>11} {'MB/file':>9}")
    print(f"  {'─'*12} {'─'*6} {'─'*11} {'─'*9}")
    for table, cfg in plan.items():
        mb = cfg["bytes_per_chunk"] / (1024 ** 2)
        print(f"  {table:<12} {cfg['chunks']:>6,} {cfg['rows_per_chunk']:>11,} {mb:>8.1f}")
    print(f"{'─'*57}\n")


def make_filename(table: str, index: int) -> str:
    """Return a timestamped filename for each generated file."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{table}_{stamp}_{index:04d}.csv"


# ─────────────────────────────────────────────
# Mode handlers
# ─────────────────────────────────────────────
def write_local(args):
    target_bytes = int(args.target_gb * (1024 ** 3))
    plan         = plan_chunks(target_bytes)
    print_plan(plan, args.target_gb)

    for table, cfg in plan.items():
        table_dir = os.path.join(args.location, table)
        os.makedirs(table_dir, exist_ok=True)

        row_id = 1
        for i in range(1, cfg["chunks"] + 1):
            rows    = [cfg["row_fn"](row_id + j) for j in range(cfg["rows_per_chunk"])]
            row_id += cfg["rows_per_chunk"]

            content  = rows_to_csv_bytes(rows, cfg["fields"])
            filename = make_filename(table, i)
            path     = os.path.join(table_dir, filename)

            with open(path, "wb") as f:
                f.write(content)

            size_mb = len(content) / (1024 ** 2)
            print(f"  [{table}] [{i:04d}/{cfg['chunks']:04d}] Written : {path}  ({size_mb:.1f} MB)")


def write_cloud(args):
    try:
        import boto3
    except ImportError:
        raise SystemExit("boto3 is not installed.  Run: pip install boto3")

    s3           = boto3.client("s3", region_name=args.region)
    target_bytes = int(args.target_gb * (1024 ** 3))
    plan         = plan_chunks(target_bytes)
    print_plan(plan, args.target_gb)

    total_uploaded = 0

    for table, cfg in plan.items():
        prefix = f"{args.prefix.rstrip('/')}/{table}"
        row_id = 1

        for i in range(1, cfg["chunks"] + 1):
            rows    = [cfg["row_fn"](row_id + j) for j in range(cfg["rows_per_chunk"])]
            row_id += cfg["rows_per_chunk"]

            content  = rows_to_csv_bytes(rows, cfg["fields"])
            filename = make_filename(table, i)
            key      = f"{prefix}/{filename}"

            s3.put_object(Bucket=args.bucket, Key=key, Body=content)

            total_uploaded += len(content)
            size_mb  = len(content) / (1024 ** 2)
            total_gb = total_uploaded / (1024 ** 3)

            print(
                f"  [{table}] [{i:04d}/{cfg['chunks']:04d}] "
                f"Uploaded : s3://{args.bucket}/{key}  "
                f"({size_mb:.1f} MB | total so far: {total_gb:.2f} GB)"
            )


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate synthetic e-commerce CSV data for the Big Data pipeline."
    )

    subparsers = parser.add_subparsers(dest="mode", required=True)

    # ── local sub-command ──
    local_parser = subparsers.add_parser("local", help="Write CSV files to a local directory.")
    local_parser.add_argument(
        "--location",
        default="./ecommerce_data",
        help="Root directory where table folders will be created (default: ./ecommerce_data).",
    )

    # ── cloud sub-command ──
    cloud_parser = subparsers.add_parser("cloud", help="Upload CSV files to an S3 bucket.")
    cloud_parser.add_argument("--bucket", required=True, help="S3 bucket name.")
    cloud_parser.add_argument(
        "--prefix",
        default="data",
        help="S3 key prefix — folder inside the bucket (default: data).",
    )
    cloud_parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region for the S3 client (default: us-east-1).",
    )

    # ── shared argument ──
    for p in (local_parser, cloud_parser):
        p.add_argument(
            "--target-gb",
            type=float,
            default=30.0,
            help="Total dataset size to generate in GB (default: 30).",
        )

    return parser


def main():
    parser = build_parser()
    args   = parser.parse_args()

    print(f"\n{'='*57}")
    print(f"  E-Commerce Data Producer")
    print(f"  Procesamiento de Datos Masivos | ITESO")
    print(f"{'='*57}")
    print(f"  Mode      : {args.mode}")
    print(f"  Target GB : {args.target_gb}")

    if args.mode == "local":
        print(f"  Location  : {args.location}")
        write_local(args)
    else:
        print(f"  Bucket    : {args.bucket}")
        print(f"  Prefix    : {args.prefix}")
        print(f"  Region    : {args.region}")
        write_cloud(args)

    print("\nDone.")


if __name__ == "__main__":
    main()
