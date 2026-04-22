"""
Videogame Dataset Generator (Based on logs_producer.py)
======================================================

Generates large CSV files (~30GB total) using Faker
and uploads them to S3 (cloud mode) or writes locally.

Usage:

# Local test
python videogames_producer.py local --location ./data --files 1 --rows 10000

# Cloud (full dataset ~30GB)
python videogames_producer.py cloud --bucket my-bucket --prefix data/videogames --files 120 --rows 500000
"""

import argparse
import os
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
Faker.seed(0)

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
GENRES = [
    "RPG", "Action", "FPS", "Battle Royale",
    "Sports", "Racing", "Fighting", "Simulation"
]

PLATFORMS = [
    "PS5", "Xbox Series X", "Nintendo Switch",
    "PC", "Mobile"
]

# ─────────────────────────────────────────────
# Row generator 
# ─────────────────────────────────────────────
def generate_rows(n_rows: int):
    """Generate CSV rows as a string (similar to logs)."""
    lines = []
    ts = datetime.now()

    for _ in range(n_rows):
        price  = "" if random.random() < 0.05 else round(random.uniform(1, 80), 2)
        rating = "" if random.random() < 0.08 else round(random.uniform(1, 10), 1)

        row = f"{uuid.uuid4()}," \
              f"{ts.strftime('%Y-%m-%d %H:%M:%S')}," \
              f"{fake.user_name()}," \
              f"{fake.word().title()} {fake.word().title()}," \
              f"{random.choice(GENRES)}," \
              f"{random.choice(PLATFORMS)}," \
              f"{fake.country()}," \
              f"{price}," \
              f"{random.choice([1,2,3,5,10])}," \
              f"{rating}"

        lines.append(row)
        ts += timedelta(seconds=random.randint(1, 5))

    return "\n".join(lines)


def make_filename(index: int):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"videogames_{stamp}_{index:03d}.csv"


# ─────────────────────────────────────────────
# LOCAL MODE
# ─────────────────────────────────────────────
def write_local(args):
    os.makedirs(args.location, exist_ok=True)

    header = "event_id,timestamp,player_username,game_title,genre,platform,region,sale_price,units_sold,rating\n"

    for i in range(1, args.files + 1):
        content = header + generate_rows(args.rows)
        filename = make_filename(i)
        path = os.path.join(args.location, filename)

        with open(path, "w") as f:
            f.write(content)

        print(f"[{i}/{args.files}] Written: {path}")


# ─────────────────────────────────────────────
# CLOUD MODE (S3)
# ─────────────────────────────────────────────
def write_cloud(args):
    try:
        import boto3
    except ImportError:
        raise SystemExit("boto3 not installed")

    s3 = boto3.client("s3")

    header = "event_id,timestamp,player_username,game_title,genre,platform,region,sale_price,units_sold,rating\n"

    for i in range(1, args.files + 1):
        content = header + generate_rows(args.rows)
        filename = make_filename(i)
        key = f"{args.prefix.rstrip('/')}/{filename}"

        s3.put_object(
            Bucket=args.bucket,
            Key=key,
            Body=content.encode("utf-8")
        )

        size_mb = len(content) / (1024 * 1024)
        print(f"[{i}/{args.files}] Uploaded: s3://{args.bucket}/{key} ({size_mb:.1f} MB)")


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate videogame dataset"
    )

    subparsers = parser.add_subparsers(dest="mode", required=True)

    # local
    local_parser = subparsers.add_parser("local")
    local_parser.add_argument("--location", default="./data")

    # cloud
    cloud_parser = subparsers.add_parser("cloud")
    cloud_parser.add_argument("--bucket", required=True)
    cloud_parser.add_argument("--prefix", default="data/videogames")

    # shared
    for p in (local_parser, cloud_parser):
        p.add_argument("--files", type=int, default=120)
        p.add_argument("--rows", type=int, default=500000)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    print(f"Mode  : {args.mode}")
    print(f"Files : {args.files}")
    print(f"Rows  : {args.rows} per file")
    print(f"Est GB: {(args.files * args.rows * 200) / 1e9:.2f} (approx)\n")

    if args.mode == "local":
        write_local(args)
    else:
        write_cloud(args)

    print("\nDone.")


if __name__ == "__main__":
    main()
