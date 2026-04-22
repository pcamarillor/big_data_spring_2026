from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, avg, count

# Spark (EMR)
spark = SparkSession.builder \
    .appName("VideogamePipeline") \
    .getOrCreate()

# Leer CSV sin limpiar desde S3 
df = spark.read \
    .option("header", "false") \
    .option("inferSchema", "false") \
    .option("mode", "PERMISSIVE") \
    .csv("s3://iteso-projecto/proyectoUno/data/videogames/")

# Forzar esquema 
columns = [
    "id", "timestamp", "name", "game", "genre",
    "platform", "country", "price", "quantity", "rating"
]
df = df.toDF(*columns)

# Quitar filas basura (headers mezclados / strings)
df = df.filter(col("price").rlike("^[0-9.]+$"))

# Cast
df = df.withColumn("price", col("price").cast("double")) \
       .withColumn("rating", col("rating").cast("double")) \
       .withColumn("quantity", col("quantity").cast("int"))

# Limpieza
df = df.dropna(subset=["price", "quantity"])
df_clean = df.fillna({"price": 0, "rating": 0})

# Filtro
df_filtered = df_clean.filter(col("price") > 0)

# Columna derivada
df_enriched = df_filtered.withColumn(
    "price_category",
    when(col("price") < 20, "LOW")
    .when((col("price") >= 20) & (col("price") < 50), "MEDIUM")
    .otherwise("HIGH")
)

# Agregación
df_agg = df_enriched.groupBy("genre", "price_category") \
    .agg(
        count("*").alias("total_games"),
        avg("price").alias("avg_price")
    )

# Persistencia (parquet)
df_agg.write \
    .mode("overwrite") \
    .partitionBy("genre") \
    .parquet("s3://iteso-projecto/output/videogames_parquet/")