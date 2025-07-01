from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, ArrayType, TimestampType
import os

# MinIO konfigürasyonu
os.environ['AWS_ACCESS_KEY_ID'] = 'minioadmin'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'minioadmin'

spark = SparkSession.builder \
    .appName("KafkaToMinIO") \
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

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

df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "PurchasedItem") \
    .option("startingOffsets", "earliest") \
    .load()

parsed_df = df.select(
    from_json(col("value").cast("string"), schema).alias("data")
).select("data.*")

query = parsed_df.writeStream \
    .format("parquet") \
    .option("path", "s3a://purchased-items/") \
    .option("checkpointLocation", "s3a://purchased-items/checkpoint/") \
    .outputMode("append") \
    .start()

query.awaitTermination()
