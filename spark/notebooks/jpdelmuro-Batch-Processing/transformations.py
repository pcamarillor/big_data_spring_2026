from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, datediff, round as spark_round, to_date,
    month, year, count, sum as spark_sum, avg, desc
)

# Iniciar sesión de Spark
spark = SparkSession.builder.appName("OrdersTransformations").getOrCreate()


# LECTURA DE DATOS
# Leemos los archivos CSV generados con Faker desde S3


INPUT_PATH = "s3://bigdata-batch-delmuro-faker-2026/raw/"
OUTPUT_PATH = "s3://bigdata-batch-delmuro-faker-2026/output/"

df = spark.read.option("header", "true").option("inferSchema", "true").csv(INPUT_PATH)

print(f"=== RAW DATA: {df.count()} rows ===")
df.printSchema()
df.show(5, truncate=False)

# 1. LIMPIEZA DE DATOS
# Eliminamos duplicados, valores nulos y registros inválidos

# Eliminar pedidos duplicados usando el identificador único
df_clean = df.dropDuplicates(["order_id"])

# Convertir fechas de entrega vacías a nulo para manejarlas correctamente
df_clean = df_clean.withColumn(
    "delivery_date",
    when((col("delivery_date") == "") | col("delivery_date").isNull(), None)
    .otherwise(col("delivery_date"))
)

# Eliminar registros con datos faltantes o inválidos
# (sin order_id, sin estado, o con cantidad menor o igual a 0)
df_clean = df_clean.filter(
    col("order_id").isNotNull() &
    col("order_status").isNotNull() &
    (col("quantity") > 0)
)

print(f"=== AFTER CLEANING: {df_clean.count()} rows ===")


# 2. DERIVACION DE COLUMNAS
# Creamos columnas nuevas a partir de las existentes


# Calcular el monto total del pedido: cantidad * precio * (1 - descuento)
df_enriched = df_clean.withColumn(
    "total_amount",
    spark_round(col("quantity") * col("unit_price") * (1 - col("discount")), 2)
)

# Calcular los días de envío: fecha de entrega - fecha del pedido
# Solo aplica para pedidos que ya fueron entregados
df_enriched = df_enriched.withColumn(
    "order_date_parsed", to_date(col("order_date"))
).withColumn(
    "delivery_date_parsed", to_date(col("delivery_date"))
).withColumn(
    "shipping_days",
    when(col("delivery_date_parsed").isNotNull(),
         datediff(col("delivery_date_parsed"), col("order_date_parsed")))
).drop("order_date_parsed", "delivery_date_parsed")

# Extraer el año y mes del pedido para poder agrupar por periodo
df_enriched = df_enriched.withColumn(
    "order_year", year(to_date(col("order_date")))
).withColumn(
    "order_month", month(to_date(col("order_date")))
)

print("=== AFTER DERIVATION ===")
df_enriched.select("order_id", "quantity", "unit_price", "discount",
                    "total_amount", "shipping_days", "order_year", "order_month").show(10)


# 3. AGREGACIONES
# Agrupamos los datos para obtener métricas de resumen


# Ingresos totales por categoría de producto
print("=== REVENUE BY CATEGORY ===")
revenue_by_category = df_enriched.groupBy("category").agg(
    count("*").alias("total_orders"),
    spark_round(spark_sum("total_amount"), 2).alias("total_revenue"),
    spark_round(avg("total_amount"), 2).alias("avg_order_value")
).orderBy(desc("total_revenue"))
revenue_by_category.show()

# Los 10 países con más ingresos
print("=== TOP 10 COUNTRIES BY REVENUE ===")
revenue_by_country = df_enriched.groupBy("country").agg(
    count("*").alias("total_orders"),
    spark_round(spark_sum("total_amount"), 2).alias("total_revenue")
).orderBy(desc("total_revenue")).limit(10)
revenue_by_country.show()

# Ingresos por mes para ver la tendencia temporal
print("=== MONTHLY REVENUE ===")
monthly_revenue = df_enriched.groupBy("order_year", "order_month").agg(
    count("*").alias("total_orders"),
    spark_round(spark_sum("total_amount"), 2).alias("total_revenue")
).orderBy("order_year", "order_month")
monthly_revenue.show(24)


# 4. FILTRADO Y ORDENAMIENTO
# Filtramos los datos para obtener subconjuntos relevantes


# Los 20 pedidos entregados con mayor monto
print("=== TOP 20 DELIVERED ORDERS BY AMOUNT ===")
delivered = df_enriched.filter(
    col("order_status") == "delivered"
).orderBy(desc("total_amount")).limit(20)
delivered.select("order_id", "customer_name", "category", "total_amount",
                 "shipping_days").show(20, truncate=False)

# Promedio de días de envío por categoría (solo pedidos entregados)
print("=== AVG SHIPPING DAYS BY CATEGORY ===")
avg_shipping = df_enriched.filter(
    col("order_status") == "delivered"
).groupBy("category").agg(
    spark_round(avg("shipping_days"), 1).alias("avg_shipping_days"),
    count("*").alias("delivered_orders")
).orderBy("avg_shipping_days")
avg_shipping.show()


# 5. PERSISTENCIA DE DATOS
# Guardamos los datos transformados en formato Parquet en S3, particionados por categoría para optimizar consultas futuras

print("=== WRITING PARQUET TO S3 ===")
df_enriched.write.mode("overwrite").partitionBy("category").parquet(OUTPUT_PATH)
print(f"=== PARQUET WRITTEN TO {OUTPUT_PATH} ===")

# Cerrar sesión de Spark
spark.stop()
