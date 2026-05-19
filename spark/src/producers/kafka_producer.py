"""
Kafka Log Producer
==================
Procesamiento de Datos Masivos | ITESO

Sends random log entries to a Kafka topic one record at a time,
with a random delay of 5 to 15 seconds between each message.
This simulates a real server emitting log events over time.

Usage:
  python3 kafka_producer.py --broker localhost:9092 --topic server-logs --records 20

Dependencies:
  pip install kafka-python
"""

import argparse
import random
import time
from datetime import datetime

from kafka import KafkaProducer

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
LEVELS = ["INFO ", "WARN ", "ERROR"]

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

DELAY_MIN = 5   # seconds
DELAY_MAX = 15  # seconds


# ─────────────────────────────────────────────
# Log entry generator
# ─────────────────────────────────────────────
def generate_log_entry() -> str:
    """Return a single random log line with the current timestamp."""
    ts = datetime.now().replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
    level = random.choice(LEVELS)
    message = random.choice(MESSAGES[level])
    server = f"server-node-{random.randint(1, 5)}"
    return f"{ts} | {level} | {message} | {server}"


# ─────────────────────────────────────────────
# Producer
# ─────────────────────────────────────────────
def run_producer(args):
    producer = KafkaProducer(
        bootstrap_servers=args.broker,
        # Encode each message as UTF-8 bytes before sending
        value_serializer=lambda msg: msg.encode("utf-8"),
    )

    print(f"Connected to broker : {args.broker}")
    print(f"Topic               : {args.topic}")
    print(f"Records to send     : {'unlimited' if args.records == 0 else args.records}")
    print(f"Delay between records: {DELAY_MIN}-{DELAY_MAX} seconds")
    print("-" * 55)

    count = 0
    try:
        while args.records == 0 or count < args.records:
            entry = generate_log_entry()

            # Send the record to Kafka
            producer.send(args.topic, value=entry)
            producer.flush()   # ensure the message is actually sent before sleeping

            count += 1
            print(f"[{count}] Sent: {entry}")

            # Stop if we have reached the requested number of records
            if args.records != 0 and count >= args.records:
                break

            # Wait a random delay before sending the next record
            delay = random.randint(DELAY_MIN, DELAY_MAX)
            print(f"    Next record in {delay}s ...")
            time.sleep(delay)

    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        producer.close()
        print(f"\nDone. Total records sent: {count}")


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