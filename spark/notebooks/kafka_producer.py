import json
import time
import random
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    key_serializer=lambda k: str(k).encode('utf-8'),
    acks='all',
    retries=3
)

def generate_mock_data():
    """Genera un diccionario simulando la información de la Parte I."""
    return {
        "user_id": random.randint(1, 1000),
        "game_id": random.randint(100, 500),
        "action": random.choice(["play", "purchase", "review"]),
        "timestamp": int(time.time()),
        "session_duration_sec": random.randint(10, 3600)
    }

TOPIC_NAME = "proyecto_streaming"

if __name__ == "__main__":
    print(f"Iniciando producer...")
    try:
        while True:
            payload = generate_mock_data()
            
            future = producer.send(
                topic=TOPIC_NAME,
                key=payload["user_id"],
                value=payload
            )
            
            record_metadata = future.get(timeout=10)
            print(f"Mensaje enviado -> Partición: {record_metadata.partition} | Offset: {record_metadata.offset} | Data: {payload}")
            
            time.sleep(0.5) 
            
    except KeyboardInterrupt:
        print("\nCerrando productor")
        producer.close()