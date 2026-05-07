"""
Descripción de la Aplicación Productora (Producer Application):

Este script simula ser una fuente de datos en tiempo real (streaming). 
Su función principal es generar información ficticia sobre transacciones 
de videojuegos de manera continua. 

Para lograrlo, utiliza la librería 'Faker' y selecciona datos al azar 
como el nombre del juego, el género, la plataforma, el precio y la hora 
exacta de la creación del registro. Cada segundo, el script empaqueta 
esta información en formato JSON y la envía de forma segura al tópico 
llamado "videogames" dentro de Kafka, asegurándose de que el servidor 
confirme la recepción de cada mensaje.
"""

from kafka import KafkaProducer
from faker import Faker
import json
import random
import time
from datetime import datetime

fake = Faker()

# Asegúrate de que el bootstrap_servers coincida exactamente con la configuración de tu consumidor.
# Si usan Docker Compose, podría ser 'kafka-1:9092'. Si todo es local sin Docker, 'localhost:9092'.
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

GENRES = ["RPG", "Action", "FPS", "Sports", "Racing", "Survival Horror", "Simulator"]
PLATFORMS = ["PC", "PS5", "Xbox", "Switch"]

def generate():
    return {
        "id": fake.uuid4(),
        "game": fake.word().title(),
        "genre": random.choice(GENRES),
        "platform": random.choice(PLATFORMS),
        "price": round(random.uniform(5, 80), 2),
        # Se agrega el timestamp en formato ISO para que la validación de PySpark no falle
        "timestamp": datetime.utcnow().isoformat() 
    }

print("Producing streaming data to 'videogames' topic...")

while True:
    data = generate()
    producer.send("videogames", data)
    print(f"Sent: {data}")
    time.sleep(1) # Simula el flujo continuo de datos