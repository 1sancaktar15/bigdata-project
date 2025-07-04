from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, ArrayType, TimestampType
import os

# MinIO konfigürasyonu (bazı Spark sürümlerinde gerekebilir)
os.environ['AWS_ACCESS_KEY_ID'] = 'minioadmin'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'minioadmin'

# Eğer Spark Docker'da ise endpoint "http://minio:9000" olmalı
# Eğer Spark kendi bilgisayarında ise endpoint "http://localhost:9000" olmalı
minio_endpoint = "http://localhost:9000"

spark = SparkSession.builder \
    .appName("KafkaToMinIO") \
    .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,"
            "org.apache.hadoop:hadoop-aws:3.3.4,"
            "com.amazonaws:aws-java-sdk-bundle:1.12.262") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.endpoint", minio_endpoint) \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

# PurchasedItem JSON şeması
schema = StructType([
    StructField("SessionId", StringType()),
    StructField("TimeStamp", TimestampType()),
    StructField("UserId", StringType()),
    StructField("TotalPrice", DoubleType()),
    StructField("OrderId", StringType()),
    StructField("PaymentType", StringType()),
    StructField("Products", ArrayType(
        StructType([
            StructField("ProductId", StringType()),
            StructField("ItemCount", IntegerType()),
            StructField("ItemPrice", DoubleType()),
            StructField("ItemDiscount", DoubleType()),
        ])
    ))
])

# Kafka'dan okuma
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "PurchasedItem") \
    .option("startingOffsets", "earliest") \
    .load()

# JSON parse
parsed_df = df.select(
    from_json(col("value").cast("string"), schema).alias("data")
).select("data.*")

# MinIO'ya Parquet olarak yaz
query = parsed_df.writeStream \
    .format("parquet") \
    .option("path", "s3a://purchased-items/") \
    .option("checkpointLocation", "s3a://purchased-items/checkpoint/") \
    .outputMode("append") \
    .start()

query.awaitTermination()
