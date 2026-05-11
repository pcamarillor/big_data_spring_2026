import csv
import os
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
random.seed(42)
Faker.seed(42)

BASE_DIR = "data"
USERS_DIR = os.path.join(BASE_DIR, "users")
CONTENT_DIR = os.path.join(BASE_DIR, "content")
WATCH_DIR = os.path.join(BASE_DIR, "watch_history")

os.makedirs(USERS_DIR, exist_ok=True)
os.makedirs(CONTENT_DIR, exist_ok=True)
os.makedirs(WATCH_DIR, exist_ok=True)

NUM_USERS = 1000
NUM_CONTENT = 1000
NUM_WATCH_ROWS = 1000

countries = ["Mexico", "USA", "Canada", "Spain", "Argentina", "Brazil", "Colombia", "Chile", "Peru", "Venezuela", "Ecuador", "Guatemala", "Cuba", "Bolivia", "Honduras", "Paraguay", "El Salvador", "Nicaragua", "Costa Rica", "Panama"]
devices = ["mobile", "smart_tv", "tablet", "laptop", "desktop", "frige", "Wii", "nintendo 3ds"] #jeje
subscription_types = ["free", "basic", "standard", "premium"]
genres = ["Drama", "Comedy", "Action", "Sci-Fi", "Horror", "Documentary", "Romance", "Thriller", "Fantasy", "Mystery", "Adventure", "Crime", "Family", "Musical", "War", "Western"]
content_types = ["movie", "series", "documentary", "short_film", "animation", "reality_show", "talk_show", "game_show"]
languages = ["English", "Spanish", "French", "Japanese", "Koxrean", "German", "Italian", "Portuguese", "Russian", "Hindi"]
ratings = ["G", "PG", "PG-13", "R", "TV-MA", "TV-14", "TV-G", "TV-PG", "TV-Y", "TV-Y7"]
studios = ["Nova Studios", "Pixel Forge", "Sunset Media", "Blue Frame", "Vision Works", "Echo Entertainment", "Starlight Productions", "Luna Films", "Cosmic Pictures", "Nebula Studios"]

def random_signup_date():
    start = datetime(2019, 1, 1)
    end = datetime(2029, 1, 1)
    delta = end - start
    return (start + timedelta(days=random.randint(0, delta.days))).date().isoformat()

def random_watch_timestamp():
    start = datetime(2024, 1, 1)
    end = datetime(2029, 1, 1)
    delta = end - start
    dt = start + timedelta(
        days=random.randint(0, delta.days),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return dt.isoformat(sep=" ")

def generate_users():
    path = os.path.join(USERS_DIR, "users.csv")
    user_ids = []

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "user_id", "username", "email", "country", "city",
            "subscription_type", "signup_date", "age", "preferred_device"
        ])

        for i in range(NUM_USERS):
            user_id = f"U{i+1:07d}"
            user_ids.append(user_id)
            country = random.choice(countries)
            writer.writerow([
                user_id,
                fake.user_name(),
                fake.email(),
                country,
                fake.city(),
                random.choice(subscription_types),
                random_signup_date(),
                random.randint(16, 75),
                random.choice(devices)
            ])

    return user_ids

def generate_content():
    path = os.path.join(CONTENT_DIR, "content.csv")
    content_ids = []

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "content_id", "title", "genre", "content_type", "release_year",
            "duration_minutes", "language", "rating", "studio"
        ])

        for i in range(NUM_CONTENT):
            content_id = f"C{i+1:07d}"
            content_ids.append(content_id)
            ctype = random.choice(content_types)
            duration = random.randint(20, 180) if ctype != "series" else random.randint(20, 60)

            writer.writerow([
                content_id,
                fake.catch_phrase(),
                random.choice(genres),
                ctype,
                random.randint(1980, 2025),
                duration,
                random.choice(languages),
                random.choice(ratings),
                random.choice(studios)
            ])

    return content_ids

def generate_watch_history(user_ids, content_ids):
    path = os.path.join(WATCH_DIR, "watch_history.csv")

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "event_id", "user_id", "content_id", "watch_timestamp", "device",
            "watch_time_minutes", "completion_percentage", "is_finished", "region"
        ])

        for _ in range(NUM_WATCH_ROWS):
            completion = round(random.uniform(1, 100), 2)
            watch_time = random.randint(1, 240)

            writer.writerow([
                str(uuid.uuid4()),
                random.choice(user_ids),
                random.choice(content_ids),
                random_watch_timestamp(),
                random.choice(devices),
                watch_time,
                completion,
                completion >= 90,
                random.choice(countries)
            ])

def main():
    print("Generating users...")
    user_ids = generate_users()

    print("Generating content...")
    content_ids = generate_content()

    print("Generating watch history...")
    generate_watch_history(user_ids, content_ids)

    print("Done.")

if __name__ == "__main__":
    main()