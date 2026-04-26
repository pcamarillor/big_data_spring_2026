import csv
import os
import uuid
import random
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
OUTPUT_FILE = "ecommerce_test.csv"
TARGET_MB = 100
TARGET_BYTES = TARGET_MB * 1024 * 1024

CATEGORIES = ['Electronics', 'Clothing', 'Home & Garden', 'Books', 'Health', 'Automotive', 'Toys', 'Sports']
REGIONS = ['North America', 'Europe', 'Asia', 'South America', 'Africa', 'Oceania']
STATUSES = ['Completed', 'Completed', 'Completed', 'Pending', 'Cancelled', 'Refunded']

def generate_dirty_data():
    print(f"--- Generando archivo de prueba: {TARGET_MB} MB con 'suciedad' ---")
    
    recent_rows = [] # Búfer para generar duplicados reales
    current_size = 0
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Escribimos los encabezados
        writer.writerow([
            "transaction_id", "user_id", "timestamp", "product_id", 
            "category", "price", "quantity", "region", "order_status"
        ])
        
        rows_batch = []
        
        while current_size < TARGET_BYTES:
            # 5% de probabilidad de insertar un DUPLICADO EXACTO
            if recent_rows and random.random() < 0.05:
                row = random.choice(recent_rows)
            else:
                # Generación de datos normales
                t_id = str(uuid.uuid4())
                u_id = random.randint(100000, 999999)
                ts = (datetime(2025, 1, 1) + timedelta(minutes=random.randint(0, 525600))).isoformat()
                p_id = f"PRD-{random.randint(1000, 9999)}"
                cat = random.choice(CATEGORIES)
                price = round(random.uniform(5.0, 1500.0), 2)
                qty = random.randint(1, 10)
                reg = random.choice(REGIONS)
                stat = random.choice(STATUSES)
                
                # 5% de probabilidad de inyectar NULOS
                if random.random() < 0.05:
                    u_id = ""  # Usuario nulo
                if random.random() < 0.05:
                    price = "" # Precio nulo
                    
                row = [t_id, u_id, ts, p_id, cat, price, qty, reg, stat]
                
                # Guardamos la fila en el búfer por si se necesit duplicar más adelante
                recent_rows.append(row)
                if len(recent_rows) > 500:
                    recent_rows.pop(0) # Mantenemos el búfer pequeño para no saturar la RAM
            
            rows_batch.append(row)
            
            # Escribimos en lotes de 10,000 para optimizar el disco
            if len(rows_batch) >= 10000:
                writer.writerows(rows_batch)
                rows_batch = []
                f.flush() # Forzamos la escritura para poder medir el peso real
                current_size = os.path.getsize(OUTPUT_FILE)
                print(f"Progreso: {current_size / (1024*1024):.2f} MB / {TARGET_MB} MB", end='\r')

        # Escribimos cualquier registro sobrante
        if rows_batch:
            writer.writerows(rows_batch)
            
    print(f"\n¡Listo! Archivo '{OUTPUT_FILE}' generado con éxito.")

if __name__ == "__main__":
    generate_dirty_data()