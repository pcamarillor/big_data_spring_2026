"""
Dataset Producer for Spark Testing
==================================

Generates fake CSV records with Faker + random/constants.

Schema:
id,license_plate,registration_date,year,model,brand,color,motor_no,type,firstname,lastname,address,municipality,state

Usage examples:
  python dataset_producer.py local --location ./data --files 10 --lines 100000
  python dataset_producer.py cloud --bucket my-bucket --prefix spark/input --files 5 --lines 200000
"""

import argparse
import csv
import io
import os
import random
import time
from datetime import datetime

try:
    from faker import Faker
except ImportError as exc:
    raise SystemExit(
        "Missing dependency 'faker'. Install it with: py -m pip install faker"
    ) from exc


COLUMNS = [
    "id",
    "license_plate",
    "registration_date",
    "year",
    "model",
    "brand",
    "color",
    "motor_no",
    "type",
    "firstname",
    "lastname",
    "address",
    "municipality",
    "state",
]

MODELS = {
    "Toyota": ["Corolla", "Yaris", "Camry", "Hilux"],
    "Nissan": ["Sentra", "Versa", "Altima", "Frontier"],
    "Honda": ["Civic", "Accord", "CR-V", "Fit"],
    "Ford": ["Focus", "Fiesta", "Escape", "Ranger"],
    "Chevrolet": ["Aveo", "Spark", "Malibu", "S10"],
    "Volkswagen": ["Jetta", "Polo", "Golf", "Tiguan"],
}

COLORS = ["White", "Black", "Gray", "Blue", "Red", "Silver", "Green"]
VEHICLE_TYPES = ["Sedan", "SUV", "Hatchback", "Pickup", "Van"]


def generate_record(record_id: int, fake: Faker, rng: random.Random) -> list[str]:
    brand = rng.choice(list(MODELS.keys()))
    model = rng.choice(MODELS[brand])
    year = rng.randint(1998, datetime.now().year)

    return [
        str(record_id),
        fake.bothify(text="???-####").upper(),
        fake.date_between(start_date="-30y", end_date="today").isoformat(),
        str(year),
        model,
        brand,
        rng.choice(COLORS),
        fake.bothify(text="??##??##??").upper(),
        rng.choice(VEHICLE_TYPES),
        fake.first_name(),
        fake.last_name(),
        fake.street_address().replace(",", " "),
        fake.city(),
        fake.state(),
    ]


def make_filename(index: int) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"records_{stamp}_{index:03d}.csv"


def generate_record_lines(n_lines: int) -> str:
    fake = Faker("es_MX")
    rng = random.Random()

    lines = []
    lines.append(",".join(COLUMNS))

    for i in range(n_lines):
        record = generate_record(i, fake, rng)
        lines.append(",".join(record))

    return "\n".join(lines)

# ─────────────────────────────────────────────
# Mode handlers
# ─────────────────────────────────────────────

def write_local(args):
    os.makedirs(args.location, exist_ok=True)

    for i in range(1, args.files + 1):
        content = generate_record_lines(args.lines)
        filename = make_filename(i)
        path = os.path.join(args.location, filename)

        with open(path, "w", encoding="UTF-8") as f:
            f.write(content)

        print(f"[{i}/{args.files}] Written: {path}")

def write_cloud(args):
    try:
        import boto3
    except ImportError:
        raise SystemExit("boto3 is not installed. Run: pip3 install boto3")

    s3 = boto3.client("s3")

    for i in range(1, args.files + 1):
        content = generate_record_lines(args.lines)
        filename = make_filename(i)
        key = f"{args.prefix.rstrip('/')}/{filename}"

        s3.put_object(
            Bucket=args.bucket,
            Key=key,
            Body=content.encode("utf-8"),
        )

        print(f"[{i}/{args.files}] Uploaded: s3://{args.bucket}/{key}")

# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate CSV datasets for Spark.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # ── local sub-command ──
    local_parser = subparsers.add_parser("local", help="Write CSV files to local directory.")
    local_parser.add_argument(
        "--location",
        default="./dataset_output",
        help="Target directory for generated CSV files.",
    )

    # ── cloud sub-command ──
    cloud_parser = subparsers.add_parser("cloud", help="Upload CSV files to S3.")
    cloud_parser.add_argument("--bucket", required=True, help="S3 bucket name.")
    cloud_parser.add_argument(
        "--prefix",
        default="spark/input",
        help="S3 prefix (folder) for uploaded files.",
    )

    # ── shared arguments ──
    for p in (local_parser, cloud_parser):
        p.add_argument(
            "--files",
            type=int,
            default=1,
            help="Number of log files to generate (default: 1).",
        )
        p.add_argument(
            "--lines",
            type=int,
            default=100,
            help="Number of log entries per file (default: 100).",
        )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    print(f"Mode    : {args.mode}")
    print(f"Files   : {args.files}")
    print(f"Rows    : {args.lines} per file")

    if args.mode == "local":
        print(f"Location: {args.location}\\n")
        write_local(args)
    else:
        print(f"Bucket  : {args.bucket}")
        print(f"Prefix  : {args.prefix}\\n")
        write_cloud(args)

    print("\\nDone.")


if __name__ == "__main__":
    main()
