import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, round, sum, count

def main():
    # 1. Inicializar Spark Session
    spark = SparkSession.builder \
        .appName("Ecommerce_Batch_Pipeline") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")

    # Rutas de S3
    input_path = "s3://proyecto-batch-processing/raw-data/*.csv"
    output_path = "s3://proyecto-batch-processing/curated-data/"

    print("Iniciando lectura de datos desde S3...")
    df_raw = spark.read.option("header", "true").csv(input_path)

    # Convertimos tipos de datos críticos para las operaciones matemáticas
    df_raw = df_raw.withColumn("price", col("price").cast("double")) \
                   .withColumn("quantity", col("quantity").cast("int"))

    print("1. Aplicando Data Cleaning...")
    df_clean = df_raw.dropDuplicates(["transaction_id"]) \
                     .dropna(subset=["user_id"]) \
                     .fillna({"price": 0.0})

    print("2. Aplicando Joins (Catálogo de Impuestos)...")
    tax_data = [
        ("Electronics", 0.16), ("Clothing", 0.08), ("Home & Garden", 0.16), 
        ("Books", 0.00), ("Health", 0.00), ("Automotive", 0.16), 
        ("Toys", 0.16), ("Sports", 0.16)
    ]
    df_taxes = spark.createDataFrame(tax_data, ["category", "tax_rate"])
    df_joined = df_clean.join(df_taxes, on="category", how="left")

    print("3. Aplicando Column Derivation...")
    df_derived = df_joined.withColumn("subtotal", round(col("price") * col("quantity"), 2)) \
                          .withColumn("tax_amount", round(col("subtotal") * col("tax_rate"), 2)) \
                          .withColumn("total_sale_with_tax", round(col("subtotal") + col("tax_amount"), 2))

    print("4. Aplicando Filtering and Sorting...")
    df_filtered = df_derived.filter(col("order_status") == "Completed") \
                            .orderBy(col("timestamp").desc())

    print("5. Aplicando Aggregations...")
    df_metrics = df_filtered.groupBy("region") \
                            .agg(
                                sum("total_sale_with_tax").alias("total_regional_revenue"),
                                count("transaction_id").alias("total_successful_orders")
                            )
    df_metrics.show()

    print("Exportando datos curados a S3...")
    # Escribimos el resultado detallado particionado por región
    df_filtered.write.mode("overwrite").partitionBy("region").parquet(output_path)
    
    print("¡Pipeline completado con éxito!")
    spark.stop()

if __name__ == "__main__":
    main()