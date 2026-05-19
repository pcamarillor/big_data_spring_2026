"""
Log File Generator
==================
Procesamiento de Datos Masivos | ITESO

Generates random .log files in the streaming format expected by log_streaming.py.

Usage examples:
  # Local mode — write to a local directory
  python3 src/producers/log_producer.py local --location /opt/spark/work-dir/data/streaming/logs/ --files 5 --lines 10

  # Cloud mode — upload to S3 (run on EC2)
  python generate_logs.py cloud --bucket my-bucket --prefix logs/input --files 3 --lines 50

Dependencies (only for cloud mode):
  pip install boto3
"""

import argparse
import os
import random
from datetime import datetime, timedelta
import time

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
LEVELS = ["INFO ", "WARN ", "ERROR"]   # padded to keep columns aligned

MESSAGES = {
    "INFO ": [
        "User login successful",
        "Backup completed successfully",
        "Cache cleared",
        "Service restarted",
        "Health check passed",
        "Configuration reloaded",
    ],
    "WARN ": [
        "Disk usage 85%",
        "Memory usage 90%",
        "CPU spike detected",
        "Response time above threshold",
        "Retry attempt 3 of 5",
        "Certificate expires in 7 days",
    ],
    "ERROR": [
        "500 Internal Server Error",
        "404 Not Found",
        "Database connection timeout",
        "Disk full",
        "Authentication failed",
        "Unhandled exception in worker thread",
    ],
}

# ─────────────────────────────────────────────
# Log generation helpers
# ─────────────────────────────────────────────
def random_server(n_servers=5):
    """Return a server name like 'server-node-3'."""
    return f"server-node-{random.randint(1, n_servers)}"


def generate_log_lines(n_lines: int) -> str:
    """Generate n_lines of log entries as a single string."""
    lines = []
    ts = datetime.now().replace(microsecond=0)

    for _ in range(n_lines):
        level = random.choice(LEVELS)
        message = random.choice(MESSAGES[level])
        server = random_server()
        lines.append(f"{ts.strftime('%Y-%m-%d %H:%M:%S')} | {level} | {message} | {server}")
        ts += timedelta(seconds=random.randint(1, 10))   # small random gap between events

    return "\n".join(lines)


def make_filename(index: int) -> str:
    """Return a unique filename for each generated file."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"logs_{stamp}_{index:03d}.log"


# ─────────────────────────────────────────────
# Mode handlers
# ─────────────────────────────────────────────
def write_local(args):
    os.makedirs(args.location, exist_ok=True)

    for i in range(1, args.files + 1):
        content = generate_log_lines(args.lines)
        filename = make_filename(i)
        path = os.path.join(args.location, filename)

        with open(path, "w") as f:
            f.write(content)

        print(f"[{i}/{args.files}] Written: {path}")

        time.sleep(2)  # simulate delay between file generations

def write_cloud(args):
    try:
        import boto3
    except ImportError:
        raise SystemExit("boto3 is not installed. Run: pip install boto3")

    s3 = boto3.client("s3")

    for i in range(1, args.files + 1):
        content = generate_log_lines(args.lines)
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