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
import json, random, time

fake = Faker()

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

GENRES = ["RPG", "Action", "FPS", "Sports", "Racing"]
PLATFORMS = ["PC", "PS5", "Xbox", "Switch"]

def generate():
    return {
        "id": fake.uuid4(),
        "game": fake.word().title(),
        "genre": random.choice(GENRES),
        "platform": random.choice(PLATFORMS),
        "price": round(random.uniform(5, 80), 2)
    }

print("Producing...")

while True:
    data = generate()
    producer.send("videogames", data)
    print(data)
    time.sleep(1)