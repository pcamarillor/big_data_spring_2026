import importlib
import subprocess
import sys
import random
import uuid
from pathlib import Path
import argparse


def check_package(package_name, import_name=None):
    """
    Check and install package if missing
    """
    import_name = import_name or package_name
    try:
        importlib.import_module(import_name)
    except ImportError:
        print(f"Installing {package_name}...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", package_name]
        )
        print(f"\nRestart script after installing {package_name}\n")
        sys.exit(0)


# ---------------------------------------------------
# LOAD BASE VIDEO GAME DATASET
# ---------------------------------------------------
def load_games_dataset(file_path, pd):
    df = pd.read_csv(file_path)

    # normalize columns just in case
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    return df


# ---------------------------------------------------
# GENERATE USERS
# ---------------------------------------------------
def generate_users(n, pd, fake):
    return pd.DataFrame([
        {
            "user_id": i,
            "username": fake.user_name(),
            "country": fake.country(),
            "signup_date": fake.date_between(start_date="-5y", end_date="today"),
            "age": random.randint(13, 55)
        }
        for i in range(1, n + 1)
    ])


# ---------------------------------------------------
# GENERATE PURCHASES
# ---------------------------------------------------
def generate_purchases(n, users_df, games_df, pd, fake):
    payment_methods = ["Credit Card", "PayPal", "Debit Card", "Gift Card"]
    regions = ["NA", "EU", "LATAM", "ASIA"]

    user_ids = users_df["user_id"].tolist()

    rows = []

    for i in range(1, n + 1):
        game = games_df.sample(1).iloc[0]

        base_price = round(random.uniform(5, 70), 2)
        discount = round(random.uniform(0, 0.50), 2)
        final_price = round(base_price * (1 - discount), 2)

        rows.append({
            "transaction_id": str(uuid.uuid4()),
            "purchase_number": i,
            "user_id": random.choice(user_ids),
            "game_name": str(game.get("name", "Unknown")),
            "platform": str(game.get("platform", "PC")),
            "genre": str(game.get("genre", "Unknown")),
            "publisher": str(game.get("publisher", "Unknown")),
            "release_year": game.get("year", None),
            "purchase_date": fake.date_between(start_date="-4y", end_date="today"),
            "region": random.choice(regions),
            "payment_method": random.choice(payment_methods),
            "price": base_price,
            "discount": discount,
            "final_price": final_price,
            "quantity": random.randint(1, 3),
            "rating": random.randint(1, 5)
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------
# SAVE DATA
# ---------------------------------------------------
def save_data(users_df, purchases_df, path):
    Path(f"{path}/csv").mkdir(parents=True, exist_ok=True)
    Path(f"{path}/parquet").mkdir(parents=True, exist_ok=True)

    users_df.to_csv(f"{path}/csv/users.csv", index=False)
    purchases_df.to_csv(f"{path}/csv/purchases.csv", index=False)

    users_df.to_parquet(f"{path}/parquet/users.parquet", index=False)
    purchases_df.to_parquet(f"{path}/parquet/purchases.parquet", index=False)

    print("CSV and Parquet files saved.")


# ---------------------------------------------------
# MAIN
# ---------------------------------------------------
def main(game_file, users_count, purchases_count, path):
    check_package("pandas")
    import pandas as pd

    check_package("faker", "faker")
    from faker import Faker

    check_package("pyarrow")

    import numpy as np

    Faker.seed(42)
    random.seed(42)
    np.random.seed(42)

    fake = Faker()

    print("Loading Kaggle Video Game Sales dataset...")
    games_df = load_games_dataset(game_file, pd)
    print("Games loaded:", len(games_df))

    print("Generating users...")
    users_df = generate_users(users_count, pd, fake)

    print("Generating purchases...")
    purchases_df = generate_purchases(
        purchases_count,
        users_df,
        games_df,
        pd,
        fake
    )

    save_data(users_df, purchases_df, path)

    print("Finished :)")


# ---------------------------------------------------
# CLI
# ---------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Gaming Big Data Dataset from Video Game Sales 2024"
    )

    parser.add_argument(
        "--games-file",
        type=str,
        default="video_game_sales_2024.csv",
        help="Path to Kaggle dataset CSV"
    )

    parser.add_argument(
        "--users",
        type=int,
        default=1000000,
        help="Number of synthetic users"
    )

    parser.add_argument(
        "--purchases",
        type=int,
        default=10000000,
        help="Number of synthetic purchases"
    )

    parser.add_argument(
        "--path",
        type=Path,
        default=Path("."),
        help="Output directory"
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Small test mode"
    )

    args = parser.parse_args()

    if args.quick:
        args.users = 100
        args.purchases = 1000

    main(
        game_file=args.games_file,
        users_count=args.users,
        purchases_count=args.purchases,
        path=args.path
    )