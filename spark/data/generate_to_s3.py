import argparse
import csv
import os
import random
import subprocess
import time
from datetime import datetime, timedelta

from faker import Faker

# ---------------------------------------------------------------------------
# Constantes del dominio
# ---------------------------------------------------------------------------
MEXICAN_STATES = [
    "Aguascalientes", "Baja California", "Baja California Sur", "Campeche",
    "Chiapas", "Chihuahua", "Ciudad de Mexico", "Coahuila", "Colima",
    "Durango", "Estado de Mexico", "Guanajuato", "Guerrero", "Hidalgo",
    "Jalisco", "Michoacan", "Morelos", "Nayarit", "Nuevo Leon", "Oaxaca",
    "Puebla", "Queretaro", "Quintana Roo", "San Luis Potosi", "Sinaloa",
    "Sonora", "Tabasco", "Tamaulipas", "Tlaxcala", "Veracruz", "Yucatan",
    "Zacatecas",
]
SPORTS = ["futbol_7", "futbol_5", "padel", "tenis", "basquetbol",
          "voleibol", "squash"]
SURFACES = ["cesped_sintetico", "cemento", "duela", "cesped_natural", "arcilla"]
RESERVATION_STATUS = ["completed"] * 8 + ["cancelled", "no_show"]
PAYMENT_METHODS = ["tarjeta_credito", "tarjeta_debito", "transferencia",
                   "efectivo", "oxxo"]
CHANNELS = ["app", "web", "whatsapp", "presencial"]
PROMO_CODES = ["", "", "", "", "VERANO20", "ESTUDIANTE10", "GRUPO15"]

CHUNK_DIR = "/tmp/datagen"
os.makedirs(CHUNK_DIR, exist_ok=True)


def s3_exists(bucket, key):
    """Resume capability: revisa si un objeto ya esta en S3."""
    r = subprocess.run(
        ["aws", "s3api", "head-object", "--bucket", bucket, "--key", key],
        capture_output=True
    )
    return r.returncode == 0


def upload_and_clean(local_path, bucket, key):
    subprocess.run(
        ["aws", "s3", "cp", local_path, f"s3://{bucket}/{key}", "--quiet"],
        check=True
    )
    os.remove(local_path)


def gen_facilities(n, path):
    fake = Faker("es_MX")
    Faker.seed(42)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["facility_id", "facility_name", "city", "state",
                    "address", "lat", "lon", "owner_name", "tax_id", "opened_at"])
        for i in range(n):
            w.writerow([
                f"FAC{i:08d}",
                f"{fake.company()} Sports Center",
                fake.city(),
                random.choice(MEXICAN_STATES),
                fake.address().replace("\n", ", "),
                round(random.uniform(14.5, 32.7), 6),
                round(random.uniform(-117.1, -86.7), 6),
                fake.name(),
                fake.bothify(text="???######??#"),
                fake.date_between(start_date="-10y", end_date="-1y").isoformat(),
            ])


def gen_courts(n_facilities, max_per_fac, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["court_id", "facility_id", "sport", "surface",
                    "capacity", "hourly_rate_mxn"])
        idx = 0
        for fac in range(n_facilities):
            for _ in range(random.randint(1, max_per_fac)):
                w.writerow([
                    f"CRT{idx:09d}",
                    f"FAC{fac:08d}",
                    random.choice(SPORTS),
                    random.choice(SURFACES),
                    random.choice([4, 10, 14, 22]),
                    random.choice([300, 450, 600, 800, 1200, 1500]),
                ])
                idx += 1
    return idx


def gen_users_chunk(chunk_id, n_users, path, write_header):
    fake = Faker("es_MX")
    Faker.seed(1000 + chunk_id)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["user_id", "first_name", "last_name", "email", "phone",
                        "city", "state", "birth_date", "registered_at",
                        "preferred_sport"])
        offset = chunk_id * n_users
        for i in range(n_users):
            w.writerow([
                f"USR{offset + i:010d}",
                fake.first_name(),
                fake.last_name(),
                fake.email(),
                fake.phone_number(),
                fake.city(),
                random.choice(MEXICAN_STATES),
                fake.date_of_birth(minimum_age=15, maximum_age=70).isoformat(),
                fake.date_time_between(start_date="-5y", end_date="now").isoformat(),
                random.choice(SPORTS),
            ])


def gen_reservations_chunk(chunk_id, n_rows, n_users, n_courts,
                           res_path, pay_path, write_header):
    fake = Faker("es_MX")
    Faker.seed(5000 + chunk_id)
    base = datetime(2022, 1, 1)
    with open(res_path, "w", newline="", encoding="utf-8") as fr, \
         open(pay_path, "w", newline="", encoding="utf-8") as fp:
        wres, wpay = csv.writer(fr), csv.writer(fp)
        if write_header:
            wres.writerow(["reservation_id", "user_id", "court_id",
                           "start_time", "end_time", "status", "channel",
                           "promo_code", "notes", "created_at"])
            wpay.writerow(["payment_id", "reservation_id", "amount_mxn",
                           "payment_method", "paid_at", "is_refunded"])
        for i in range(n_rows):
            res_id = f"RES{chunk_id:04d}{i:010d}"
            user_id = f"USR{random.randint(0, n_users - 1):010d}"
            court_id = f"CRT{random.randint(0, n_courts - 1):09d}"
            offset_min = random.randint(0, 60 * 24 * 365 * 4)
            start = base + timedelta(minutes=offset_min)
            duration = random.choice([60, 90, 120])
            end = start + timedelta(minutes=duration)
            status = random.choice(RESERVATION_STATUS)
            notes = fake.sentence(nb_words=8) if random.random() < 0.10 else ""
            wres.writerow([
                res_id, user_id, court_id,
                start.isoformat(), end.isoformat(),
                status,
                random.choice(CHANNELS),
                random.choice(PROMO_CODES),
                notes,
                (start - timedelta(days=random.randint(0, 14))).isoformat(),
            ])
            if status == "completed":
                rate = random.choice([300, 450, 600, 800, 1200, 1500])
                amount = round(rate * (duration / 60.0), 2)
                wpay.writerow([
                    f"PAY{chunk_id:04d}{i:010d}",
                    res_id, amount,
                    random.choice(PAYMENT_METHODS),
                    (start - timedelta(minutes=random.randint(0, 2880))).isoformat(),
                    random.random() < 0.02,
                ])
        
            if random.random() < 0.001:
                wres.writerow([
                    res_id, user_id, court_id,
                    start.isoformat(), end.isoformat(),
                    status, "app", "", "", start.isoformat(),
                ])
            if random.random() < 0.0005:
                wres.writerow([
                    f"RES{chunk_id:04d}NULL{i:08d}",
                    "", "", "", "", "completed", "app", "", "", "",
                ])

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bucket", required=True, help="Bucket destino (sin s3://)")
    p.add_argument("--prefix", default="raw", help="Prefijo en el bucket")
    p.add_argument("--target-gb", type=int, default=35)
    args = p.parse_args()

    bytes_per_res = 400
    target_bytes = args.target_gb * 1024**3
    total_res = int(target_bytes / bytes_per_res)
    rows_per_chunk = 1_000_000  # ~400 MB por chunk
    n_chunks = max(1, total_res // rows_per_chunk)

    n_facilities = 50_000
    max_courts_per_fac = 6
    n_users = 5_000_000
    users_per_chunk = 500_000
    n_user_chunks = n_users // users_per_chunk

    print(f"[plan] objetivo={args.target_gb} GB")
    print(f"       reservaciones={total_res:,} en {n_chunks} chunks")
    print(f"       usuarios={n_users:,} en {n_user_chunks} chunks")
    print(f"       destino: s3://{args.bucket}/{args.prefix}/\n")

    started = time.time()

    # ---- 1. Facilities ---------------------------------------------------
    key = f"{args.prefix}/facilities/facilities.csv"
    if s3_exists(args.bucket, key):
        print("[1/4] facilities: ya en S3, skip")
    else:
        print("[1/4] generando facilities...", flush=True)
        path = f"{CHUNK_DIR}/facilities.csv"
        gen_facilities(n_facilities, path)
        upload_and_clean(path, args.bucket, key)

    # ---- 2. Courts -------------------------------------------------------
    key = f"{args.prefix}/courts/courts.csv"
    if s3_exists(args.bucket, key):
        print("[2/4] courts: ya en S3, skip")
        n_courts = n_facilities * max_courts_per_fac
    else:
        print("[2/4] generando courts...", flush=True)
        path = f"{CHUNK_DIR}/courts.csv"
        n_courts = gen_courts(n_facilities, max_courts_per_fac, path)
        upload_and_clean(path, args.bucket, key)
        print(f"       {n_courts:,} canchas")

    # ---- 3. Users --------------------------------------------------------
    print(f"[3/4] users ({n_user_chunks} chunks):")
    for i in range(n_user_chunks):
        key = f"{args.prefix}/users/users_part_{i:04d}.csv"
        if s3_exists(args.bucket, key):
            print(f"   [{i+1:02d}/{n_user_chunks}] skip", flush=True)
            continue
        path = f"{CHUNK_DIR}/users_part_{i:04d}.csv"
        gen_users_chunk(i, users_per_chunk, path, write_header=(i == 0))
        upload_and_clean(path, args.bucket, key)
        print(f"   [{i+1:02d}/{n_user_chunks}] ok", flush=True)

    # ---- 4. Reservations + Payments -------------------------------------
    print(f"\n[4/4] reservations + payments ({n_chunks} chunks, esto es lo pesado):")
    chunk_times = []
    for i in range(n_chunks):
        res_key = f"{args.prefix}/reservations/reservations_part_{i:04d}.csv"
        pay_key = f"{args.prefix}/payments/payments_part_{i:04d}.csv"
        if s3_exists(args.bucket, res_key):
            print(f"   [{i+1:03d}/{n_chunks}] skip", flush=True)
            continue
        t0 = time.time()
        res_path = f"{CHUNK_DIR}/res_{i:04d}.csv"
        pay_path = f"{CHUNK_DIR}/pay_{i:04d}.csv"
        gen_reservations_chunk(
            i, rows_per_chunk, n_users, n_courts,
            res_path, pay_path, write_header=(i == 0)
        )
        upload_and_clean(res_path, args.bucket, res_key)
        upload_and_clean(pay_path, args.bucket, pay_key)
        elapsed = time.time() - t0
        chunk_times.append(elapsed)
        avg = sum(chunk_times) / len(chunk_times)
        eta_min = ((n_chunks - i - 1) * avg) / 60
        print(f"   [{i+1:03d}/{n_chunks}] ok ({elapsed:.0f}s) — ETA {eta_min:.0f} min",
              flush=True)

    total_min = (time.time() - started) / 60
    print(f"\n[done] {total_min:.0f} minutos totales")
    print(f"\nVerifica el tamano:")
    print(f"  aws s3 ls s3://{args.bucket}/{args.prefix}/ --recursive "
          f"--summarize --human-readable | tail -2")


if __name__ == "__main__":
    main()
