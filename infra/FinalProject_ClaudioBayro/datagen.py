import csv
import random
import uuid
from faker import Faker
from datetime import datetime, timedelta
import os

fake = Faker()

OUTPUT_DIR = "data"
TARGET_SIZE_GB = 31
ROWS_PER_FILE = 500_000

os.makedirs(OUTPUT_DIR, exist_ok=True)

categories = ["Politics", "Crypto", "Sports", "Economics", "Technology", "World News"]
outcomes = ["YES", "NO"]
sides = ["BUY", "SELL"]

markets = [
    {
        "market_id": str(uuid.uuid4()),
        "market_title": fake.sentence(nb_words=8),
        "category": random.choice(categories)
    }
    for _ in range(5000)
]

def random_timestamp():
    start = datetime(2025, 1, 1)
    end = datetime(2026, 4, 1)
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))

def current_size_gb():
    total = 0
    for root, _, files in os.walk(OUTPUT_DIR):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))
    return total / (1024 ** 3)

file_num = 0

while current_size_gb() < TARGET_SIZE_GB:
    file_path = f"{OUTPUT_DIR}/trades_{file_num}.csv"

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "trade_id",
            "user_id",
            "market_id",
            "market_title",
            "category",
            "outcome",
            "side",
            "price",
            "shares",
            "trade_amount",
            "fee",
            "timestamp",
            "country"
        ])

        for _ in range(ROWS_PER_FILE):
            market = random.choice(markets)
            price = round(random.uniform(0.01, 0.99), 4)
            shares = round(random.uniform(1, 5000), 2)
            trade_amount = round(price * shares, 2)
            fee = round(trade_amount * 0.02, 2)

            writer.writerow([
                str(uuid.uuid4()),
                str(uuid.uuid4()),
                market["market_id"],
                market["market_title"],
                market["category"],
                random.choice(outcomes),
                random.choice(sides),
                price,
                shares,
                trade_amount,
                fee,
                random_timestamp().isoformat(),
                fake.country()
            ])

    print(f"Created {file_path}. Current size: {current_size_gb():.2f} GB")
    file_num += 1