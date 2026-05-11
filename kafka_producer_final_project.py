"""
Kafka Data Producer
===================
Procesamiento de Datos Masivos | ITESO

This script creates fake (synthetic) data that looks like real people info
and sends it to a Kafka topic.

Usage example:
  # Send data to a Kafka server
  python kafka_producer.py --broker localhost:9092 --topic synthetic_data --records 5000

Dependencies:
  pip install kafka-python faker
"""

# ── Built-in tools (come with Python, no install needed) ──
import argparse      # Lets us type commands like "python file.py --records 100"
import json          # Converts Python dictionaries to JSON text (and back)
import random        # Picks random numbers (used to add randomness like null values)
import time          # Lets us pause/sleep between messages

# ── External tool (must install separately) ──
from faker import Faker  # A library that creates fake but realistic data (names, emails, etc.)


# ═══════════════════════════════════════════════════════
# SETTINGS (you can change these numbers)
# ═══════════════════════════════════════════════════════

# Chance that any field (except ID and Name) becomes empty (None)
# 0.05 = 5% chance. So out of 100 records, about 5 will have a missing field.
NULL_PROBABILITY = 0

DUPLICATE_PROBABILITY = 0.05

def generate_record(fake: Faker) -> dict:
    """
    Creates ONE fake person record.
    
    Returns a dictionary (a collection of key-value pairs) like:
    {
        "ID": "123e4567-e89b-12d3-a456-426614174000",
        "Name": "John Smith",
        "Address": "123 Main St, Springfield",
        ...
    }
    """
    
    # Build a list of fake data fields.
    # Each line calls a Faker method to make up realistic-looking data.
    row = [
        fake.uuid4(),                           # Unique ID (like a fingerprint for the record)
        fake.name(),                            # Random full name
        fake.address().replace('\n', ', '),     # Random address (replace newlines with commas)
        fake.email(),                           # Random email like john.smith@email.com
        fake.phone_number(),                    # Random phone number
        fake.job(),                             # Random job title like "Software Engineer"
        fake.company(),                         # Random company name like "Acme Corp"
        fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat(),  # Random birthday
        fake.credit_card_number(),              # Random fake credit card number
        fake.ipv4(),                            # Random IP address like 192.168.1.1
        fake.text(max_nb_chars=200).replace('\n', ' ')  # Random short paragraph
    ]
    
    # ── Add some "messiness" to the data ──
    # Starting from index 2 (Address), randomly set some fields to None (empty).
    # This simulates real-world dirty data where some info is missing.
    for i in range(2, len(row)):          # Loop through fields 2 to 10
        if random.random() < NULL_PROBABILITY:  # If random number is less than 0.05
            row[i] = None                       # Make this field empty
    
    # Convert the list into a dictionary with named keys.
    # This makes the data easier to read and process later.
    return {
        "ID": row[0],
        "Name": row[1],
        "Address": row[2],
        "Email": row[3],
        "Phone": row[4],
        "Job": row[5],
        "Company": row[6],
        "DOB": row[7],           # Date of Birth
        "CreditCard": row[8],
        "IP": row[9],
        "Notes": row[10]
    }


# ═══════════════════════════════════════════════════════
# STEP 2: KAFKA MODE — Send data over the network
# ═══════════════════════════════════════════════════════

def write_kafka(args):
    """
    When you run: python kafka_producer.py kafka
    This function runs. It sends records to a Kafka server instead of saving files.
    """
    
    # Try to import the Kafka library. If it's not installed, show a helpful error.
    try:
        from kafka import KafkaProducer
    except ImportError:
        raise SystemExit("kafka-python is not installed. Run: pip install kafka-python")
    
    # Create a connection to the Kafka server (the "broker")
    producer = KafkaProducer(
        bootstrap_servers=[args.broker],   # Address of the Kafka server
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
        # ^ This line automatically converts our dictionary to JSON text,
        #   then converts that text to bytes so Kafka can send it over the network.
    )
    
    fake = Faker()
    prev_record = None
    start_time = time.time()   # Remember when we started (to calculate speed)
    
    try:
        for i in range(1, args.records + 1):
            
            # Same logic as local mode: new record or duplicate?
            if prev_record is not None and random.random() < DUPLICATE_PROBABILITY:
                record = prev_record
            else:
                record = generate_record(fake)
            
            prev_record = record
            
            # ── Send the record to Kafka ──
            # This puts the message into a "topic" (like a mailbox or channel)
            producer.send(args.topic, value=record)
            
            # Show progress with speed info
            elapsed = time.time() - start_time
            speed = i / elapsed if elapsed > 0 else 0
            print(f"[{i}/{args.records}] Produced: {record['Name']} | {record['Job']} (Topic: {args.topic})")
            
            # Optional delay between messages
            if args.delay > 0:
                time.sleep(args.delay)
        
        print()  # Blank line for clean output
        
    except KeyboardInterrupt:
        # If the user presses Ctrl+C, stop gracefully instead of crashing
        print("\nStreaming interrupted by user.")
    
    finally:
        # Always run this cleanup code, even if interrupted
        print("Flushing messages...")   # Make sure all messages actually get sent
        producer.flush()                # Push any remaining messages out
        producer.close()                # Close the network connection


def build_parser() -> argparse.ArgumentParser:
    """
    This sets up the commands you can type in the terminal.
    It lets users set options like the broker, topic, and how many records to make.
    """
    
    parser = argparse.ArgumentParser(
        description="Generate synthetic data for the PySpark streaming demo."
    )
    
    parser.add_argument(
        "--broker",
        default="localhost:9092",
        help="Kafka broker address (default: localhost:9092)."
    )
    parser.add_argument(
        "--topic",
        default="synthetic_data",
        help="Kafka topic name (default: synthetic_data)."
    )
    parser.add_argument(
        "--records",
        type=int,
        default=1000,
        help="Number of records to generate (default: 1000)."
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Delay in seconds between messages (default: 0.0)."
    )
    
    return parser


def main():
    """
    This is where the program actually starts running.
    It reads your command-line input and starts the Kafka producer.
    """
    
    parser = build_parser()
    args = parser.parse_args()   # Read what the user typed
    
    # Show a summary of what we're about to do
    print(f"Broker  : {args.broker}")
    print(f"Topic   : {args.topic}")
    print(f"Records : {args.records}\n")
    
    write_kafka(args)        # Run the Kafka sender
    
    print("\nDone.")


# ═══════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    # This line checks: "Are we running this file directly?"
    # If yes, start the main() function.
    # If this file is imported by another file, main() won't run automatically.
    main()