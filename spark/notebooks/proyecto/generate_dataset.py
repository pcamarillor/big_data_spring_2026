import gzip
import uuid
import random
import argparse
import boto3
from datetime import datetime, timedelta, date
from faker import Faker
from io import BytesIO

BUCKET             = "emr-proyecto-058264391995-us-east-1-an"
IMPRESSIONS_PREFIX = "data/impressions"
CAMPAIGNS_PREFIX   = "data/campaigns"
NUM_DAYS           = 24
ROWS_PER_DAY       = 6_000_000
BATCH_SIZE         = 50_000
NUM_CAMPAIGNS      = 10_000

# ── LOOKUP TABLES ─────────────────────────────────────────────────────────────
DEVICE_TYPES   = ["desktop", "mobile", "tablet"]
DEVICE_WEIGHTS = [0.45, 0.45, 0.10]

OS_BY_DEVICE = {
    "desktop": ["Windows", "macOS", "Linux"],
    "mobile":  ["Android", "iOS"],
    "tablet":  ["Android", "iOS", "Windows"],
}

BROWSERS       = ["Chrome", "Firefox", "Safari", "Edge", "Samsung Internet", "Opera"]
AD_CATEGORIES  = [
    "electronics", "fashion", "travel", "automotive", "food_beverage",
    "health_beauty", "home_garden", "sports", "finance", "entertainment",
    "education", "real_estate", "gaming", "pets", "baby_kids",
]
AD_POSITIONS   = ["top", "sidebar", "bottom", "interstitial", "in_feed"]
AD_FORMATS     = ["banner", "video", "native", "carousel", "rich_media"]
AGE_BUCKETS    = ["18-24", "25-34", "35-44", "45-54", "55+"]
GENDERS        = ["M", "F", "U"]
CAMPAIGN_TYPES = ["awareness", "conversion", "retargeting", "engagement"]
INTERESTS      = [
    "technology", "sports", "music", "travel", "cooking", "fashion",
    "gaming", "fitness", "finance", "art", "automotive", "parenting",
    "science", "politics", "nature", "movies", "books", "beauty",
]
COUNTRIES = [
    "US", "GB", "CA", "AU", "DE", "FR", "BR", "MX", "IN", "JP",
    "KR", "IT", "ES", "NL", "SE", "PL", "AR", "CO", "CL", "ZA",
]

IMPRESSIONS_HEADER = "\t".join([
    "impression_id", "timestamp", "day", "user_id", "session_id",
    "device_type", "os", "browser", "country", "region", "city",
    "ad_id", "campaign_id", "advertiser_id", "ad_category",
    "ad_position", "ad_format", "page_url_hash", "referrer_hash",
    "user_age_bucket", "user_gender", "user_interest_1", "user_interest_2",
    "page_views_today", "time_on_site_sec", "recency_days", "frequency_30d",
    "bid_price_usd", "floor_price_usd", "quality_score", "predicted_ctr",
    "hour_of_day", "day_of_week", "is_weekend", "label",
])

CAMPAIGNS_HEADER = "\t".join([
    "campaign_id", "campaign_name", "advertiser_name", "campaign_type",
    "ad_category", "target_country", "budget_usd",
    "start_date", "end_date", "is_active",
])


# ── CAMPAIGNS TABLE ───────────────────────────────────────────────────────────

def generate_campaigns(n: int) -> list:
    fake = Faker()
    Faker.seed(999)
    random.seed(999)

    s3      = boto3.client("s3")
    s3_key  = f"{CAMPAIGNS_PREFIX}/campaigns.gz"
    buffer  = BytesIO()
    gz      = gzip.GzipFile(fileobj=buffer, mode="wb")
    ids     = []

    gz.write((CAMPAIGNS_HEADER + "\n").encode("utf-8"))

    base = date(2023, 1, 1)
    for i in range(n):
        cid       = f"camp_{i:05d}"
        start     = base + timedelta(days=random.randint(0, 300))
        end       = start + timedelta(days=random.randint(7, 180))
        is_active = "" if random.random() < 0.05 else str(random.randint(0, 1))

        row = "\t".join([
            cid,
            fake.catch_phrase(),
            fake.company(),
            random.choice(CAMPAIGN_TYPES),
            random.choice(AD_CATEGORIES),
            random.choice(COUNTRIES),
            str(round(random.uniform(1_000, 500_000), 2)),
            start.isoformat(),
            end.isoformat(),
            is_active,
        ])
        gz.write((row + "\n").encode("utf-8"))
        ids.append(cid)

    gz.close()
    buffer.seek(0)
    s3.upload_fileobj(buffer, BUCKET, s3_key)
    return ids

def make_row(fake: Faker, day: int, base_date: datetime, campaign_ids: list) -> str:
    device  = random.choices(DEVICE_TYPES, DEVICE_WEIGHTS)[0]
    os_name = random.choice(OS_BY_DEVICE[device])
    hour    = random.randint(0, 23)
    dow     = random.randint(0, 6)
    ts      = base_date + timedelta(
        hours=hour,
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    floor      = round(random.uniform(0.01, 2.00), 4)
    bid        = round(floor + random.uniform(0.00, 3.00), 4)
    quality    = round(random.uniform(0.0, 10.0), 3)
    pctr       = round(random.betavariate(2, 18), 6)
    click_prob = min(pctr * (quality / 10) * 2.5, 1.0)
    label      = 1 if random.random() < click_prob else 0

    return "\t".join([
        str(uuid.uuid4()),
        ts.isoformat(),
        str(day),
        str(uuid.uuid4()),
        str(uuid.uuid4()),
        device,
        os_name,
        random.choice(BROWSERS),
        random.choice(COUNTRIES),
        fake.state_abbr(),
        fake.city(),
        str(uuid.uuid4()),
        random.choice(campaign_ids),                              # FK → campaigns
        str(uuid.uuid4()),
        random.choice(AD_CATEGORIES),
        random.choice(AD_POSITIONS),
        random.choice(AD_FORMATS),
        uuid.uuid4().hex[:16],
        uuid.uuid4().hex[:16] if random.random() > 0.2 else "",  # 20% null
        random.choice(AGE_BUCKETS),
        random.choice(GENDERS),
        random.choice(INTERESTS),
        random.choice(INTERESTS),
        str(random.randint(1, 50)),
        str(random.randint(5, 3600)),
        str(random.randint(0, 365)),
        str(random.randint(1, 200)),
        str(bid),
        str(floor),
        str(quality),
        str(pctr),
        str(hour),
        str(dow),
        str(1 if dow >= 5 else 0),
        str(label),
    ])

def generate_day(day: int, rows: int, campaign_ids: list) -> None:
    fake      = Faker()
    Faker.seed(day * 42)
    random.seed(day * 42)

    s3        = boto3.client("s3")
    s3_key    = f"{IMPRESSIONS_PREFIX}/day_{day}.gz"
    base_date = datetime(2024, 1, 1) + timedelta(days=day)

    buffer = BytesIO()
    gz     = gzip.GzipFile(fileobj=buffer, mode="wb")
    gz.write((IMPRESSIONS_HEADER + "\n").encode("utf-8"))

    generated = 0
    while generated < rows:
        batch = min(BATCH_SIZE, rows - generated)
        chunk = "\n".join(make_row(fake, day, base_date, campaign_ids)
                          for _ in range(batch))
        gz.write((chunk + "\n").encode("utf-8"))
        generated += batch

    gz.close()
    buffer.seek(0)
    s3.upload_fileobj(buffer, BUCKET, s3_key)


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic ad-tech dataset")
    parser.add_argument("--rows",           type=int,  default=ROWS_PER_DAY, help="Rows per day")
    parser.add_argument("--start-day",      type=int,  default=0,            help="Start from this day (inclusive)")
    parser.add_argument("--end-day",        type=int,  default=NUM_DAYS - 1, help="End at this day (inclusive, default 23)")
    parser.add_argument("--bucket",         type=str,  default=BUCKET,       help="S3 bucket name")
    parser.add_argument("--skip-campaigns", action="store_true",             help="Skip campaigns generation")
    args = parser.parse_args()

    days_to_generate = list(range(args.start_day, args.end_day + 1))
    

    # Step 1 — campaigns dimension table (only on fresh start)
    if not args.skip_campaigns and args.start_day == 0:
        campaign_ids = generate_campaigns(NUM_CAMPAIGNS)
    else:
        campaign_ids = [f"camp_{i:05d}" for i in range(NUM_CAMPAIGNS)]

    # Step 2 — impressions by day range
    for day in days_to_generate:
        generate_day(day, args.rows, campaign_ids)

if __name__ == "__main__":
    main()
