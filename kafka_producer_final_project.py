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

import argparse      
import json          
import random        
import time          

from faker import Faker


NULL_PROBABILITY = 0.05

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
    
    row = [
        fake.uuid4(), 
        fake.name(),                            
        fake.address().replace('\n', ', '),    
        fake.email(),                           
        fake.phone_number(),                    
        fake.job(),                             
        fake.company(),                         
        fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat(), 
        fake.credit_card_number(),              
        fake.ipv4(),                            
        fake.text(max_nb_chars=200).replace('\n', ' ')  
    ]
    
    for i in range(2, len(row)):          
        if random.random() < NULL_PROBABILITY:  
            row[i] = None                       
    
    return {
        "ID": row[0],
        "Name": row[1],
        "Address": row[2],
        "Email": row[3],
        "Phone": row[4],
        "Job": row[5],
        "Company": row[6],
        "DOB": row[7],           
        "CreditCard": row[8],
        "IP": row[9],
        "Notes": row[10]
    }



def write_kafka(args):
    """
    When you run: python kafka_producer.py kafka
    This function runs. It sends records to a Kafka server instead of saving files.
    """
    
    try:
        from kafka import KafkaProducer
    except ImportError:
        raise SystemExit("kafka-python is not installed. Run: pip install kafka-python")
    
    producer = KafkaProducer(
        bootstrap_servers=[args.broker],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    fake = Faker()
    prev_record = None
    start_time = time.time()  
    
    try:
        for i in range(1, args.records + 1): 
            if prev_record is not None and random.random() < DUPLICATE_PROBABILITY:
                record = prev_record
            else:
                record = generate_record(fake)
            
            prev_record = record
            
            producer.send(args.topic, value=record)
            
            elapsed = time.time() - start_time
            speed = i / elapsed if elapsed > 0 else 0
            print(f"[{i}/{args.records}] Produced: {record['Name']} | {record['Job']} (Topic: {args.topic})")
            
            if args.delay > 0:
                time.sleep(args.delay)
        
        print()
        
    except KeyboardInterrupt:
        print("\nStreaming interrupted by user.")
    
    finally:
        print("Flushing messages...")   
        producer.flush()                
        producer.close()


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


if __name__ == "__main__":
    main()