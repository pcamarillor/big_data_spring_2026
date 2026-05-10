"""
Kafka Polymarket Producer
=========================
Procesamiento de Datos Masivos | ITESO

Simulates real-time prediction market transactions inspired by Polymarket.
The producer continuously generates market transaction events and sends them
to a Kafka topic with a random delay between records.

Usage:
  python3 polymarket_producer.py --broker kafka:9093 --topic polymarket-events --records 100

Dependencies:
  pip install kafka-python
"""

import argparse
import json
import random
import time
from datetime import datetime
from uuid import uuid4

from kafka import KafkaProducer


# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

CATEGORIES = [
    "Politics",
    "Crypto",
    "Sports",
    "Economy",
    "Technology",
    "World News"
]

MARKETS = [
    ("market-001", "Will Bitcoin reach 100k this year?", "Crypto"),
    ("market-002", "Will candidate A win the election?", "Politics"),
    ("market-003", "Will Team A win the championship?", "Sports"),
    ("market-004", "Will inflation decrease next quarter?", "Economy"),
    ("market-005", "Will a new AI model launch this month?", "Technology"),
    ("market-006", "Will a peace agreement be reached?", "World News"),
]

OUTCOMES = ["YES", "NO"]

TRADE_SIDES = ["BUY", "SELL"]

DELAY_MIN = 2
DELAY_MAX = 6


# ─────────────────────────────────────────────
# Event generator
# ─────────────────────────────────────────────

def generate_market_event() -> dict:
    """
    Generate a random Polymarket-style transaction event.
    """

    market_id, market_title, category = random.choice(MARKETS)

    price = round(random.uniform(0.05, 0.95), 2)
    quantity = random.randint(1, 500)

    event = {
        "event_id": str(uuid4()),
        "market_id": market_id,
        "market_title": market_title,
        "category": category,
        "user_id": f"user-{random.randint(1, 1000)}",
        "outcome": random.choice(OUTCOMES),
        "trade_side": random.choice(TRADE_SIDES),
        "price": price,
        "quantity": quantity,
        "transaction_value": round(price * quantity, 2),
        "timestamp": datetime.now().replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
    }

    return event


# ─────────────────────────────────────────────
# Producer
# ─────────────────────────────────────────────

def run_producer(args):

    producer = KafkaProducer(
        bootstrap_servers=args.broker,
        value_serializer=lambda msg: json.dumps(msg).encode("utf-8"),
    )

    print(f"Connected to broker  : {args.broker}")
    print(f"Topic                : {args.topic}")
    print(f"Records to send      : {'unlimited' if args.records == 0 else args.records}")
    print(f"Delay between events : {DELAY_MIN}-{DELAY_MAX} seconds")
    print("-" * 70)

    count = 0

    try:

        while args.records == 0 or count < args.records:

            event = generate_market_event()

            producer.send(args.topic, value=event)
            producer.flush()

            count += 1

            print(f"[{count}] Sent: {json.dumps(event)}")

            if args.records != 0 and count >= args.records:
                break

            delay = random.randint(DELAY_MIN, DELAY_MAX)

            print(f"    Next event in {delay}s ...")

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
        description="Send simulated Polymarket events to a Kafka topic."
    )

    parser.add_argument(
        "--broker",
        required=True,
        help="Kafka broker address (example: kafka:9093)."
    )

    parser.add_argument(
        "--topic",
        required=True,
        help="Kafka topic name."
    )

    parser.add_argument(
        "--records",
        type=int,
        default=0,
        help="Number of records to send. 0 means infinite stream."
    )

    return parser


def main():

    parser = build_parser()

    args = parser.parse_args()

    run_producer(args)


if __name__ == "__main__":
    main()