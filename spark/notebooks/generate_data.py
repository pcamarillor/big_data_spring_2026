import csv
import random
import uuid
import os
from faker import Faker
from multiprocessing import Pool, cpu_count
from datetime import datetime, timedelta

# Configuración
FILE_NAME = "streaming_logs_30GB.csv"
TARGET_SIZE_GB = 31 # Apuntamos a 31GB para estar seguros 
TARGET_SIZE_BYTES = TARGET_SIZE_GB * 1024 * 1024 * 1024

genres = ['Action', 'Comedy', 'Drama', 'Sci-Fi', 'Horror', 'Documentary', 'Romance', 'Thriller']
countries = ['US', 'MX', 'CA', 'UK', 'JP', 'BR', 'IN', 'FR', 'DE', 'AU']

def generate_batch(batch_size=50000):
    """Genera un lote de registros de logs de streaming."""
    fake = Faker()
    batch = []
    for _ in range(batch_size):
        rating = round(random.uniform(1.0, 10.0), 1) if random.random() > 0.1 else ""
        
        row = [
            str(uuid.uuid4()), 
            fake.uuid4(),      
            f"MOV-{random.randint(1000, 9999)}", 
            random.choice(genres), 
            random.choice(countries), 
            random.randint(1, 180), 
            rating, 
            fake.date_time_between(start_date='-2y', end_date='now').strftime('%Y-%m-%d %H:%M:%S') # timestamp
        ]
        batch.append(row)
    return batch

def write_to_csv():
    with open(FILE_NAME, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['log_id', 'user_id', 'movie_id', 'genre', 'country', 'watch_minutes', 'rating_given', 'timestamp'])
    
    current_size = 0
    batch_size = 100000 
    
    print(f"Iniciando generación de datos. Objetivo: {TARGET_SIZE_GB} GB")
    
    with open(FILE_NAME, 'a', newline='') as f:
        writer = csv.writer(f)
        
        while current_size < TARGET_SIZE_BYTES:
            batch = generate_batch(batch_size)
            writer.writerows(batch)
            
            current_size = os.path.getsize(FILE_NAME)
            
            if random.random() < 0.05: 
                print(f"Progreso: {current_size / (1024**3):.2f} GB / {TARGET_SIZE_GB} GB")
                
    print(f"¡Generación completa! Archivo creado: {FILE_NAME}")

if __name__ == '__main__':
    write_to_csv()