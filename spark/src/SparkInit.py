def init_spark(name, master="spark://spark-master:7077"):
    import findspark
    findspark.init()
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.appName(name) \
        .master(master) \
        .config("spark.ui.port", "4040") \
        .getOrCreate()
    return spark