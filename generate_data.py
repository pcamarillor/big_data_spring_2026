

import csv
import os
import multiprocessing as mp
from faker import Faker
import time
import random

# Tamaño objetivo en bytes por archivo (3 GB)
TARGET_SIZE = 3 * 1024 * 1024 * 1024   # 3 GB por archivo (10 archivos = 30 GB en total)

def generate_chunk(num_records):

    # Inicializamos Faker dentro del proceso trabajador para evitar problemas de compartición de estado
    fake = Faker()
    chunk = []
    
    prev_row = None
    
    for _ in range(num_records):
        # 5% de probabilidad de duplicar la fila anterior exactamente
        if prev_row is not None and random.random() < 0.05:
            chunk.append(prev_row)
            continue

        # Creación de una fila con datos realistas
        row = [
            fake.uuid4(),                           # ID único
            fake.name(),                            # Nombre
            fake.address().replace('\n', ', '),     # Dirección (sin saltos de línea)
            fake.email(),                           # Correo electrónico
            fake.phone_number(),                    # Número de teléfono
            fake.job(),                             # Puesto de trabajo
            fake.company(),                         # Empresa
            fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat(), # Fecha de nacimiento
            fake.credit_card_number(),              # Número de tarjeta de crédito
            fake.ipv4(),                             # Dirección IP
            fake.text(max_nb_chars=200).replace('\n', ' ') # Notas/Texto aleatorio
        ]
        
        # Introducción de valores nulos (representados como cadenas vacías en el CSV)
        # Empezamos el bucle en el índice 2 para que 'ID' y 'Nombre' siempre tengan datos
        for i in range(2, len(row)):
            # 5% de probabilidad de que cualquier campo no identificador sea nulo
            if random.random() < 0.05:
                row[i] = ""
                
        chunk.append(row)
        prev_row = row
        
    return chunk

def main():

    # Encabezados de las columnas del CSV
    headers = [
        "ID", "Name", "Address", "Email", "Phone", 
        "Job", "Company", "DOB", "CreditCard", "IP", "Notes"
    ]
    
    print(f"Iniciando generación de datos sintéticos. Objetivo por archivo: {TARGET_SIZE / (1024**3):.2f} GB")
    print("Incluye ~5% de probabilidad de registros duplicados y ~5% de valores nulos por campo.")
    
    # Configuración del tamaño del lote y el número de procesos
    chunk_size = 10_000
    num_processes = mp.cpu_count()
    pool = mp.Pool(num_processes)
    
    overall_start_time = time.time()
    
    try:
        # Generar una serie de archivos (en este caso configurado para los índices 1 a 9)
        for file_idx in range(1, 10):
            file_name = f'synthetic_data_{file_idx}.csv'
            print(f"\n--- Generando Archivo {file_idx}/9: {file_name} ---")
            
            # Inicializar el archivo con los encabezados
            with open(file_name, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                
            current_size = 0
            file_start_time = time.time()
            
            # Abrir en modo 'append' para ir añadiendo los datos generados
            with open(file_name, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                while current_size < TARGET_SIZE:
                    # Generar lotes de datos en paralelo usando todos los núcleos disponibles
                    results = pool.map(generate_chunk, [chunk_size] * num_processes)
                    
                    # Escribir los resultados en el archivo
                    for chunk in results:
                        writer.writerows(chunk)
                        
                    f.flush() # Asegurar que los datos se escriban físicamente en el disco
                    current_size = os.path.getsize(file_name)
                    
                    # Cálculo de progreso y velocidad
                    elapsed = time.time() - file_start_time
                    speed = current_size / (1024*1024) / elapsed if elapsed > 0 else 0
                    
                    print(f"Archivo {file_idx}: Generados {current_size / (1024**3):.3f} GB / {TARGET_SIZE / (1024**3):.3f} GB ({speed:.2f} MB/s)...", end='\r')

            final_size_gb = os.path.getsize(file_name) / (1024**3)
            print(f"\n¡Archivo {file_idx} completado! Tamaño final: {final_size_gb:.3f} GB")

    except KeyboardInterrupt:
        print("\nGeneración interrumpida por el usuario.")
    finally:
        # Cerrar el pool de procesos correctamente
        pool.close()
        pool.join()
        
    print(f"\n¡Proceso finalizado! Tiempo total transcurrido: {time.time() - overall_start_time:.2f} segundos")

if __name__ == "__main__":
    main()

