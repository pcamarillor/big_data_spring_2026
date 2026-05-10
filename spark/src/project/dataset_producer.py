"""
Log File Generator
==================
Procesamiento de Datos Masivos | ITESO

Generates random .log files in the streaming format expected by dataset_producer.py.

Usage examples:
  # Local mode — write to a local directory
  python3 dataset_producer.py local --location /opt/spark/work-dir/data/streaming/files/ --files 5 --lines 12

  # Cloud mode — upload to S3 (run on EC2)
  python3 dataset_producer.py cloud --bucket my-bucket --prefix /input --files 3 --lines 50

Dependencies (only for cloud mode):
  pip install boto3
"""

import argparse
import os
import time
import random
from datetime import datetime, timedelta
from calendar import monthrange

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
FILIAL = ["Zapopan", "Guadalajara", "Monterrey", "Cancun", "Mexico City", "Merida", "Puebla", "Tijuana", "Leon", "Queretaro"]
STATES = {
    "Zapopan": "Jalisco",
    "Guadalajara": "Jalisco",
    "Monterrey": "Nuevo León",
    "Cancun": "Quintana Roo",
    "Mexico City": "Ciudad de México",
    "Merida": "Yucatán",
    "Puebla": "Puebla",
    "Tijuana": "Baja California",
    "Leon": "Guanajuato",
    "Queretaro": "Querétaro"
}

EMPLOYEES = {
    "Zapopan": ["Alejandra Martinez", "Bruno Fernandez", "Carolina Rodriguez", "Diego Sanchez", "Elena Gomez", "Fernando Lopez", "Gabriela Torres", "Hector Ramirez", "Isabel Morales", "Jorge Castillo"],
    "Guadalajara": ["Daniela Hernandez", "Eduardo Vargas", "Fernanda Jimenez", "Gustavo Mendez", "Helena Castro", "Ignacio Ruiz", "Jimena Ortiz", "Kevin Dominguez"],
    "Monterrey": ["Gabriela Navarro", "Hugo Medina", "Irene Vazquez", "Javier Romero", "Karla Gutierrez", "Leonardo Flores", "Mariana Chavez", "Nicolas Herrera", "Olivia Delgado"],
    "Cancun": ["Julia Cervantes", "Karla Salazar", "Luis Cervantes", "Monica Ibarra", "Nestor Aguilar", "Patricia Campos", "Quintin Molina", "Raquel Espinoza"],
    "Mexico City": ["Miguel Angel Reyes", "Natalia Guerrero", "Omar Santiago", "Paulina Mendoza", "Ricardo Contreras", "Sofia Gomez", "Tomas Estrada", "Ursula Paredes", "Valentina Cruz"],
    "Merida": ["Pablo Cortes", "Quetzalli Marin", "Rodrigo Silva", "Samantha Rios", "Tadeo Fuentes", "Valeria Luna", "William Cabrera", "Ximena Vega"],
    "Puebla": ["Sebastian Moreno", "Teresa Montes", "Ulises Pacheco", "Veronica Zavala", "Xavier Gallegos", "Yolanda Sandoval", "Zacarias Lara", "Adriana Velasco"],
    "Tijuana": ["Vicente Ponce", "Wendy Mora", "Ximena Acosta", "Yasmin Bravo", "Zenon Figueroa", "Andrea Maldonado", "Benjamin Garza", "Cristina Pereira"],
    "Leon": ["Yesenia Cordero", "Zeferino Avila", "Armando Benitez", "Beatriz Ochoa", "Carlos Alberto Soto", "Dulce Maria Padilla", "Emilio Carrillo", "Fabiana Trejo"],
    "Queretaro": ["Berenice Salinas", "Camilo Ramos", "Diana Laura Serrano", "Esteban Villanueva", "Frida Rojas", "Gonzalo Bermudez", "Hilda Meza", "Ivan Alejandro Cuevas"]
}

SHIFTS = ["Morning", "Afternoon", "Night"]

SCHEDULE = {
    "Morning": ("8:00", "15:00"),   # 8:00 - 15:00
    "Afternoon": ("16:00", "23:00"), # 16:00 - 23:00
    "Night": ("1:00", "8:00")       # 1:00 - 8:00
}

HOUR_RATE = {
    "Morning": 15.0,
    "Afternoon": 18.0,
    "Night": 20.0
}

PHONE_PREFIXES = ["+52 33", "+52 81", "+52 55", "+52 999", "+52 9999"]

DEPARTMENTS = ["HR", "Finance", "IT", "Sales", "Support"]

# ─────────────────────────────────────────────
# Log generation helpers
# ─────────────────────────────────────────────

def generate_phone_number() -> str:
    """Generate a random phone number with a valid prefix."""
    prefix = random.choice(PHONE_PREFIXES)
    suffix_length = 7 if len(prefix) == 6 else 8  # Adjust suffix length based on prefix
    suffix = "".join(random.choices("0123456789", k=suffix_length))
    return f"{prefix} {suffix}"

def generate_log_days(n_days: int) -> str:
    """Generate n_days of Clock_in entries"""
    lines = []

    year = random.randint(2000, 2026)
    month = random.randint(1, 12)
    day = random.randint(1, monthrange(year, month)[1])

    date = datetime(year, month, day)

    lines.append("id, employee, phone, hour_rate, department, year, month, day, hour_in, hour_out, shift, filial, state, country")

    for line in range(n_days):
        filial = random.choice(FILIAL)
        for employee in EMPLOYEES[filial]:

            id = f"{employee}_{date.strftime('%Y%m%d')}"

            shift = random.choice(SHIFTS)

            start_str, end_str = SCHEDULE[shift]
            diff_start = random.randint(-30, 30)  # Randomize start time by ±30 minutes
            diff_end = random.randint(-30, 30)    # Randomize end time by ±30 minutes
            start_time = datetime.strptime(start_str, "%H:%M") + timedelta(minutes=diff_start)
            end_time = datetime.strptime(end_str, "%H:%M") + timedelta(minutes=diff_end)
            hour_rate = HOUR_RATE[shift]
            phone_number = generate_phone_number()
            department = random.choice(DEPARTMENTS)
            country = "Mexico"
            state = STATES[filial]

            lines.append(f"{line},{employee},{phone_number},{hour_rate},{department},{date.year},{date.month},{date.day},{start_time.strftime('%H:%M')},{end_time.strftime('%H:%M')},{shift},{filial},{state},{country}")

        date += timedelta(days=1)

    return "\n".join(lines)


def make_filename(index: int) -> str:
    """Return a unique filename for each generated file."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"logs_{stamp}_{index:03d}.csv"


# ─────────────────────────────────────────────
# Mode handlers
# ─────────────────────────────────────────────
def write_local(args):
    os.makedirs(args.location, exist_ok=True)

    for i in range(1, args.files + 1):
        content = generate_log_days(args.lines)
        filename = make_filename(i)
        path = os.path.join(args.location, filename)

        with open(path, "w") as f:
            f.write(content)

        print(f"[{i}/{args.files}] Written: {path}")
        time.sleep(20)

def write_cloud(args):
    try:
        import boto3
    except ImportError:
        raise SystemExit("boto3 is not installed. Run: pip3 install boto3")

    s3 = boto3.client("s3")

    for i in range(1, args.files + 1):
        content = generate_log_days(args.lines)
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
    parser = argparse.ArgumentParser(
        description="Generate random .log files for the PySpark streaming demo."
    )

    subparsers = parser.add_subparsers(dest="mode", required=True)

    # ── local sub-command ──
    local_parser = subparsers.add_parser("local", help="Write log files to a local directory.")
    local_parser.add_argument(
        "--location",
        default="./logs_input",
        help="Directory where log files will be saved (default: ./logs_input).",
    )

    # ── cloud sub-command ──
    cloud_parser = subparsers.add_parser("cloud", help="Upload log files to an S3 bucket.")
    cloud_parser.add_argument("--bucket", required=True, help="S3 bucket name.")
    cloud_parser.add_argument(
        "--prefix",
        default="logs/input",
        help="S3 key prefix (folder path) for the uploaded files (default: logs/input).",
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


def main():
    parser = build_parser()
    args = parser.parse_args()

    print(f"Mode    : {args.mode}")
    print(f"Files   : {args.files}")
    print(f"Lines   : {args.lines} per file")

    if args.mode == "local":
        print(f"Location: {args.location}\n")
        write_local(args)
    else:
        print(f"Bucket  : {args.bucket}")
        print(f"Prefix  : {args.prefix}\n")
        write_cloud(args)

    print("\nDone.")


if __name__ == "__main__":
    main()