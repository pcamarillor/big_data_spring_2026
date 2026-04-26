import csv
import os
import uuid
import random
import time
import boto3
from datetime import datetime, timedelta
from multiprocessing import Process, cpu_count, Value

# --- CONFIGURACIÓN PRINCIPAL ---
LOCAL_TMP_DIR = "/opt/spark/work-dir/data/tmp"
TARGET_GB = 31
TARGET_BYTES = TARGET_GB * 1024**3
RECORDS_PER_FILE = 1_000_000  # Generamos en lotes manejables para no saturar la RAM
S3_BUCKET = "proyecto-batch-processing"
S3_PREFIX = "raw-data/"

CATEGORIES = ['Electronics', 'Clothing', 'Home & Garden', 'Books', 'Health', 'Automotive', 'Toys', 'Sports']
REGIONS = ['North America', 'Europe', 'Asia', 'South America', 'Africa', 'Oceania']
STATUSES = ['Completed', 'Completed', 'Completed', 'Pending', 'Cancelled', 'Refunded']

def generate_dirty_batch(file_id, shared_bytes_counter):
    local_path = os.path.join(LOCAL_TMP_DIR, f"ecommerce_batch_{file_id}.csv")
    s3_client = boto3.client('s3')
    recent_rows = [] # Búfer para generar duplicados
    
    try:
        # 1. Generar el archivo sucio localmente
        with open(local_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "transaction_id", "user_id", "timestamp", "product_id", 
                "category", "price", "quantity", "region", "order_status"
            ])
            
            for _ in range(RECORDS_PER_FILE):
                # 5% de probabilidad de DUPLICADO
                if recent_rows and random.random() < 0.05:
                    row = random.choice(recent_rows)
                else:
                    u_id = random.randint(100000, 999999)
                    price = round(random.uniform(5.0, 1500.0), 2)
                    
                    # 5% de probabilidad de NULOS
                    if random.random() < 0.05: u_id = "" 
                    if random.random() < 0.05: price = ""

                    row = [
                        str(uuid.uuid4()), u_id,
                        (datetime(2025, 1, 1) + timedelta(minutes=random.randint(0, 525600))).isoformat(),
                        f"PRD-{random.randint(1000, 9999)}",
                        random.choice(CATEGORIES), price, random.randint(1, 10),
                        random.choice(REGIONS), random.choice(STATUSES)
                    ]
                    
                    # Actualizamos el búfer
                    recent_rows.append(row)
                    if len(recent_rows) > 500: 
                        recent_rows.pop(0)

                writer.writerow(row)
                
        # 2. Medir peso
        file_size = os.path.getsize(local_path)
        
        # 3. Subir a AWS S3
        s3_client.upload_file(local_path, S3_BUCKET, f"{S3_PREFIX}ecommerce_batch_{file_id}.csv")
        
        # 4. Actualizar contador global
        with shared_bytes_counter.get_lock():
            shared_bytes_counter.value += file_size
            
        # 5. ELIMINAR DEL EC2 (Evita que se llene el disco)
        os.remove(local_path)
        
    except Exception as e:
        print(f"Error en proceso {file_id}: {e}")

if __name__ == "__main__":
    if not os.path.exists(LOCAL_TMP_DIR):
        os.makedirs(LOCAL_TMP_DIR)
        
    print(f"--- Iniciando generación masiva: {TARGET_GB} GB con datos sucios ---")
    print(f"Destino: s3://{S3_BUCKET}/{S3_PREFIX}")
    start_time = time.time()
    
    file_id = 1
    shared_bytes = Value('d', 0.0) 
    
    while shared_bytes.value < TARGET_BYTES:
        active_processes = []
        cores = cpu_count()
        
        for _ in range(cores):
            p = Process(target=generate_dirty_batch, args=(file_id, shared_bytes))
            active_processes.append(p)
            p.start()
            file_id += 1
            
        for p in active_processes:
            p.join()
            
        gb_generados = shared_bytes.value / (1024**3)
        print(f"Progreso: {gb_generados:.2f} GB / {TARGET_GB} GB subidos a S3...")
        
    elapsed_time = round((time.time() - start_time) / 60, 2)
    print(f"¡Éxito! Pipeline finalizado en {elapsed_time} minutos.")