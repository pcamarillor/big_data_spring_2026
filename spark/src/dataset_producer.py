import argparse
import csv
import io
import os
import random
import time
import uuid
from datetime import datetime, timedelta, date
from faker import Faker

fake = Faker("es_MX")   # Realistic names/addresses for Mx
Faker.seed(42)
random.seed(42)


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

CITIES = {
    "Guadalajara":   (20.6597, -103.3496, 0.35),   # (lat, lon, weight)
    "CDMX":          (19.4326, -99.1332,  0.30),
    "Monterrey":     (25.6866, -100.3161, 0.15),
    "Puebla":        (19.0414, -98.2063,  0.08),
    "Tijuana":       (32.5027, -117.0037, 0.05),
    "León":          (21.1221, -101.6824, 0.04),
    "Querétaro":     (20.5888, -100.3899, 0.03),
}

CITY_NAMES    = list(CITIES.keys())
CITY_WEIGHTS  = [CITIES[c][2] for c in CITY_NAMES]

RIDE_TYPES    = ["standard", "comfort", "xl", "moto"]
RIDE_WEIGHTS  = [0.55, 0.25, 0.10, 0.10]

PAYMENT       = ["cash", "card", "wallet", "voucher"]
PAY_WEIGHTS   = [0.40, 0.35, 0.20, 0.05]

# Weighted statuses — most rides complete successfully
STATUSES      = ["completed", "completed", "completed", "completed",
                 "cancelled", "no_show"]

PROMO_CODES   = [None, None, None, None, None,   # 60 % no promo
                 "BIENVENIDO10", "VIERNES20", "VERANO15",
                 "PRIMERA5", "REGRESA25", "NULL"]  # NULL intentionally malformed

VEHICLE_MAKES = {
    "Nissan":    ["Versa", "Sentra", "March", "Kicks"],
    "Chevrolet": ["Aveo", "Spark", "Trax", "Onix"],
    "Volkswagen":["Jetta", "Vento", "Polo", "Golf"],
    "Toyota":    ["Corolla", "Yaris", "Avanza", "Hilux"],
    "Kia":       ["Rio", "Forte", "Sportage", "Soul"],
    "Honda":     ["Civic", "City", "CR-V", "HR-V"],
}

COLORS = ["Blanco", "Negro", "Gris", "Rojo", "Azul",
          "Plata", "Beige", "Verde", "Naranja", "Amarillo"]

BASE_FARE_RANGES = {   # (min, max) in MXN by ride type
    "standard": (35,  180),
    "comfort":  (55,  280),
    "xl":       (80,  400),
    "moto":     (20,   90),
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def rand_coord(city_name: str, spread: float = 0.15) -> tuple:
    lat0, lon0, _ = CITIES[city_name]
    return (
        round(lat0 + random.uniform(-spread, spread), 6),
        round(lon0 + random.uniform(-spread, spread), 6),
    )


def rand_rating() -> str:
    """Return a rating 1–5 (one decimal) or empty string (not rated)."""
    if random.random() < 0.25:   # 25 % of rides not rated
        return ""
    return str(round(random.uniform(3.0, 5.0), 1))


def license_plate() -> str:
    """Mexican-style plate: 3 letters + 3 digits  e.g. ABC-123."""
    letters = "ABCDEFGHJKLMNPRSTUVWXYZ"
    return (
        "".join(random.choices(letters, k=3))
        + "-"
        + "".join(random.choices("0123456789", k=3))
    )


# ─────────────────────────────────────────────────────────────────────────────
# Row generators
# ─────────────────────────────────────────────────────────────────────────────

# Pre-generate a pool of driver_ids so rides can reference them
_DRIVER_POOL: list[str] = []

def _ensure_driver_pool(size: int = 2_000_000):
    global _DRIVER_POOL
    if not _DRIVER_POOL or len(_DRIVER_POOL) < size:
        print(f"   Generating {size:,} driver IDs (this may take a few seconds)...")
        _DRIVER_POOL = [str(uuid.uuid4()) for _ in range(size)]


def ride_row(ts: datetime) -> list:
    city       = random.choices(CITY_NAMES, weights=CITY_WEIGHTS)[0]
    ride_type  = random.choices(RIDE_TYPES, weights=RIDE_WEIGHTS)[0]
    status     = random.choice(STATUSES)
    distance   = round(random.uniform(0.5, 45.0), 2)
    duration   = max(1, int(distance * random.uniform(2.5, 5.5)))  # approx min/km
    wait_min   = random.randint(2, 12)
    pickup_at  = ts + timedelta(minutes=wait_min)
    dropoff_at = pickup_at + timedelta(minutes=duration)

    lo, hi     = BASE_FARE_RANGES[ride_type]
    base_fare  = round(random.uniform(lo, hi), 2)
    surge      = round(random.choice(
                     [1.0]*6 + [1.2, 1.5, 1.8, 2.0, 2.5, 3.0]
                 ), 1)
    total_fare = round(base_fare * surge, 2)
    tip        = round(random.uniform(5, 50), 2) if (status == "completed" and random.random() < 0.30) else 0.0
    promo      = random.choice(PROMO_CODES)

    p_lat, p_lon = rand_coord(city)
    d_lat, d_lon = rand_coord(city)

    return [
        str(uuid.uuid4()),                          # ride_id
        ts.strftime("%Y-%m-%d %H:%M:%S"),           # requested_at
        pickup_at.strftime("%Y-%m-%d %H:%M:%S"),    # pickup_at
        dropoff_at.strftime("%Y-%m-%d %H:%M:%S"),   # dropoff_at
        str(uuid.uuid4()),                          # user_id
        random.choice(_DRIVER_POOL),                # driver_id
        fake.street_address(),                      # pickup_address
        fake.street_address(),                      # dropoff_address
        p_lat, p_lon,
        d_lat, d_lon,
        distance,
        duration,
        base_fare,
        surge,
        total_fare,
        tip,
        random.choices(PAYMENT, weights=PAY_WEIGHTS)[0],
        status,
        city,
        ride_type,
        promo if promo else "",                     # empty string = no promo
        rand_rating(),                              # rating_driver (may be empty)
        rand_rating(),                              # rating_user   (may be empty)
    ]


RIDE_HEADER = [
    "ride_id", "requested_at", "pickup_at", "dropoff_at",
    "user_id", "driver_id",
    "pickup_address", "dropoff_address",
    "pickup_lat", "pickup_lon", "dropoff_lat", "dropoff_lon",
    "distance_km", "duration_min",
    "base_fare", "surge_multiplier", "total_fare", "tip_amount",
    "payment_method", "status", "city", "ride_type",
    "promo_code", "rating_driver", "rating_user",
]


def driver_row(driver_id: str) -> list:
    city       = random.choices(CITY_NAMES, weights=CITY_WEIGHTS)[0]
    make       = random.choice(list(VEHICLE_MAKES.keys()))
    model      = random.choice(VEHICLE_MAKES[make])
    reg_date   = fake.date_between(start_date=date(2018, 1, 1), end_date=date(2025, 1, 1))
    total      = random.randint(50, 8000)
    avg_r      = round(random.uniform(3.5, 5.0), 2)
    verified   = random.choices([True, False], weights=[0.90, 0.10])[0]
    status     = random.choices(
                     ["active", "active", "active", "suspended", "inactive"],
                 )[0]

    return [
        driver_id,
        fake.name(),
        fake.email(),
        fake.phone_number(),
        license_plate(),
        make, model,
        random.randint(2015, 2024),
        random.choice(COLORS),
        city,
        reg_date.strftime("%Y-%m-%d"),
        total,
        avg_r,
        verified,
        status,
    ]


DRIVER_HEADER = [
    "driver_id", "full_name", "email", "phone", "license_plate",
    "vehicle_make", "vehicle_model", "vehicle_year", "vehicle_color",
    "city", "registration_date", "total_rides", "avg_rating",
    "is_verified", "status",
]


# ─────────────────────────────────────────────────────────────────────────────
# File writers
# ─────────────────────────────────────────────────────────────────────────────

def make_filename(prefix: str, index: int, ext: str = "csv") -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{stamp}_{index:05d}.{ext}"


def rows_to_csv_bytes(header: list, rows: list[list]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


# ── local ────────────────────────────────────────────────────────────────────

def write_rides_local(args):
    _ensure_driver_pool()
    out_dir = os.path.join(args.location, "rides")
    os.makedirs(out_dir, exist_ok=True)
    total_bytes = 0

    ts = datetime(2024, 1, 1, 0, 0, 0)

    for i in range(1, args.rides_files + 1):
        rows = []
        for _ in range(args.rides_lines):
            rows.append(ride_row(ts))
            ts += timedelta(seconds=random.randint(1, 8))

        filename = make_filename("rides", i)
        path = os.path.join(out_dir, filename)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if i == 1:
                w.writerow(RIDE_HEADER)  # header only in first file
            w.writerows(rows)

        size = os.path.getsize(path)
        total_bytes += size
        print(f"  [rides {i:>4}/{args.rides_files}] {filename}  "
              f"({size/1024**2:.1f} MB | total {total_bytes/1024**3:.2f} GB)")

        if args.delay > 0 and i < args.rides_files:
            time.sleep(args.delay)


def write_drivers_local(args):
    _ensure_driver_pool()
    out_dir = os.path.join(args.location, "drivers")
    os.makedirs(out_dir, exist_ok=True)
    # Use a deterministic slice of the pool so driver_ids match
    pool_slice = _DRIVER_POOL[:args.driver_files * args.driver_lines]

    idx = 0
    for i in range(1, args.driver_files + 1):
        rows = []
        for _ in range(args.driver_lines):
            if idx >= len(pool_slice):
                break
            rows.append(driver_row(pool_slice[idx]))
            idx += 1

        filename = make_filename("drivers", i)
        path = os.path.join(out_dir, filename)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if i == 1:
                w.writerow(DRIVER_HEADER)
            w.writerows(rows)

        size = os.path.getsize(path)
        print(f"  [drivers {i:>3}/{args.driver_files}] {filename}  "
              f"({size/1024**2:.1f} MB)")


# ── cloud (S3) ────────────────────────────────────────────────────────────────

def write_rides_cloud(args, s3):
    _ensure_driver_pool()
    ts = datetime(2024, 1, 1, 0, 0, 0)
    total_bytes = 0

    for i in range(1, args.rides_files + 1):
        buf = io.StringIO()
        w = csv.writer(buf)
        if i == 1:
            w.writerow(RIDE_HEADER)

        for _ in range(args.rides_lines):
            row = ride_row(ts)
            w.writerow(row)
            ts += timedelta(seconds=random.randint(1, 8))

        data = buf.getvalue().encode("utf-8")
        filename = make_filename("rides", i)
        key = f"{args.prefix.rstrip('/')}/rides/{filename}"

        s3.put_object(Bucket=args.bucket, Key=key, Body=data)
        total_bytes += len(data)
        print(f"  [rides {i:>4}/{args.rides_files}] s3://{args.bucket}/{key}  "
              f"({len(data)/1024**2:.1f} MB | total {total_bytes/1024**3:.2f} GB)")

        if args.delay > 0 and i < args.rides_files:
            time.sleep(args.delay)

def write_drivers_cloud(args, s3):
    needed = args.driver_files * args.driver_lines
    _ensure_driver_pool(needed)          # ← now uses the correct size
    pool_slice = _DRIVER_POOL[:needed]
    idx = 0

    for i in range(1, args.driver_files + 1):
        buf = io.StringIO()
        w = csv.writer(buf)
        if i == 1:
            w.writerow(DRIVER_HEADER)

        for _ in range(args.driver_lines):
            if idx >= len(pool_slice):
                break
            row = driver_row(pool_slice[idx])
            w.writerow(row)
            idx += 1

        data = buf.getvalue().encode("utf-8")
        filename = make_filename("drivers", i)
        key = f"{args.prefix.rstrip('/')}/drivers/{filename}"

        s3.put_object(Bucket=args.bucket, Key=key, Body=data)
        print(f"  [drivers {i:>3}/{args.driver_files}] s3://{args.bucket}/{key}  "
              f"({len(data)/1024**2:.1f} MB)")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate ride-sharing CSV datasets for the Big Data final project."
    )
    sub = p.add_subparsers(dest="mode", required=True)

    # local
    lp = sub.add_parser("local", help="Write files to a local directory.")
    lp.add_argument("--location", default="./project_data",
                    help="Output root directory.")

    # cloud
    cp = sub.add_parser("cloud", help="Upload files to S3.")
    cp.add_argument("--bucket", required=True)
    cp.add_argument("--prefix", default="project/input")

    for sp in (lp, cp):
        sp.add_argument("--rides-files",  type=int, default=2,
                        help="Number of rides files (default 2).")
        sp.add_argument("--rides-lines",  type=int, default=1000,
                        help="Rows per rides file (default 1000).")
        sp.add_argument("--driver-files", type=int, default=1,
                        help="Number of drivers files (default 1).")
        sp.add_argument("--driver-lines", type=int, default=500,
                        help="Rows per drivers file (default 500).")
        sp.add_argument("--delay", type=float, default=0,
                        help="Seconds between files (streaming demo, default 0).")

    return p


def main():
    args = build_parser().parse_args()

    est_rides_gb   = (args.rides_files  * args.rides_lines  * 340) / 1024**3
    est_drivers_gb = (args.driver_files * args.driver_lines * 200) / 1024**3

    print("=" * 60)
    print("Project Dataset Generator — ITESO Big Data 2026")
    print("=" * 60)
    print(f"Mode           : {args.mode}")
    print(f"Rides files    : {args.rides_files:,}  × {args.rides_lines:,} rows  ≈ {est_rides_gb:.2f} GB")
    print(f"Drivers files  : {args.driver_files:,}  × {args.driver_lines:,} rows  ≈ {est_drivers_gb:.2f} GB")
    print(f"Estimated total: {est_rides_gb + est_drivers_gb:.2f} GB")
    print("=" * 60)

    if args.mode == "local":
        print(f"\n→ Output: {args.location}\n")
        print("Generating DRIVERS table...")
        write_drivers_local(args)
        print("\nGenerating RIDES table...")
        write_rides_local(args)

    else:
        try:
            import boto3
        except ImportError:
            raise SystemExit("boto3 not installed. Run: pip install boto3")
        s3 = boto3.client("s3")
        print(f"\n→ s3://{args.bucket}/{args.prefix}\n")
        print("Uploading DRIVERS table...")
        write_drivers_cloud(args, s3)
        print("\nUploading RIDES table...")
        write_rides_cloud(args, s3)

    print("\n✓ Done.")


if __name__ == "__main__":
    main()
