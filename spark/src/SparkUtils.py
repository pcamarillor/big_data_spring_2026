from pyspark.sql.functions import when, count, isnull

class SparkUtils:
    @staticmethod
    def count_nulls(df):
        return df.select([count(when(isnull(c), c)).alias(c) for c in df.columns])
        