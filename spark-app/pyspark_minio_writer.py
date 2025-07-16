from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, ArrayType, TimestampType
import os
import subprocess
import json

# ----------- IMPROVED SLACK NOTIFICATION FUNCTION -----------
def send_slack_notification(message):
    webhook_url = "https://hooks.slack.com/services/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"
    payload = json.dumps({"text": message})
    try:
        # Using subprocess for better security and reliability
        result = subprocess.run(
            [
                "curl",
                "-sS",  # Silent but show errors
                "-X", "POST",
                "-H", "Content-type: application/json",
                "--data", payload,
                webhook_url
            ],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print(f"Slack notification failed: {result.stderr}", flush=True)
    except Exception as e:
        print(f"Slack notification error: {str(e)}", flush=True)
# ----------------------------------------------------------------------------------

# Ücret eşik değeri (TL cinsinden)
# PRICE_THRESHOLD = 1000 # Bu satır artık kullanılmayacak, doğrudan filter içinde 10000 kullanılıyor

os.environ['AWS_ACCESS_KEY_ID'] = 'minioadmin'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'minioadmin'
minio_endpoint = "http://minio:9000"

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
    .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
    .config("spark.streaming.kafka.allowNonConsecutiveOffsets", "true") \
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
    .option("failOnDataLoss", "false") \
    .option("minPartitions", "1")\
    .load()

parsed_df = df.select(
    from_json(col("value").cast("string"), schema).alias("data")
).select("data.*")

def process_batch(batch_df, batch_id):
    # Bu print her batch çalıştığında görünecek
    print(f"\n=== Processing batch {batch_id} ===", flush=True)

    # Batch'teki toplam satır sayısını gösterir
    print(f"Batch raw count: {batch_df.count()}", flush=True)

    # DataFrame'in içeriğini ekrana basar.
    # Bu sayede Kafka'dan hangi verinin geldiğini, TotalPrice kolonunun dolu olup olmadığını göreceğiz.
    if batch_df.isEmpty():
        print("Batch is empty, no data to process.", flush=True)
    else:
        print("Batch data (first 20 rows):", flush=True)
        batch_df.show(truncate=False) # truncate=False ile tüm kolonları kesmeden göster
        print("-" * 50, flush=True)

        # ----------- VERİ KALİTESİ KONTROLÜ VE HATALI VERİ YÖNETİMİ BAŞLANGICI -----------
        # Geçerli (Valid) kayıtları filtrele: Zorunlu alanlar boş olmamalı ve TotalPrice pozitif olmalı
        valid_df = batch_df.filter(
            (col("SessionId").isNotNull()) &
            (col("UserId").isNotNull()) &
            (col("OrderId").isNotNull()) &
            (col("TotalPrice").isNotNull()) & # TotalPrice'ın null olmaması da önemli
            (col("TotalPrice") > 0)          # TotalPrice'ın 0'dan büyük olması
        )

        # Hatalı (Invalid) kayıtları bul (valid_df'de olmayanlar invalid'dir)
        invalid_df = batch_df.subtract(valid_df)

        print(f"Valid records in batch: {valid_df.count()}", flush=True)
        print(f"Invalid records in batch: {invalid_df.count()}", flush=True)

        # Geçerli kayıtları ana MinIO bucket'a yaz
        if not valid_df.isEmpty():
            valid_df.write.mode("append").parquet("s3a://purchased-items/valid/")
            print("Valid records written to s3a://purchased-items/valid/", flush=True)
        else:
            print("No valid records to write.", flush=True)

        # Hatalı kayıtları ayrı bir MinIO bucket'a yaz
        if not invalid_df.isEmpty():
            invalid_df.write.mode("append").parquet("s3a://purchased-items/invalid/")
            print("Invalid records written to s3a://purchased-items/invalid/", flush=True)
        else:
            print("No invalid records to write.", flush=True)
        # ----------- VERİ KALİTESİ KONTROLÜ VE HATALI VERİ YÖNETİMİ SONU -----------


        # Büyük alışverişleri filtrele ve sayısını göster (Artık valid_df üzerinden devam ediyoruz)
        high_value_orders_filtered = valid_df.filter(col("TotalPrice") > 10000) # Değişiklik burada yapıldı
        print(f"High-value orders (filtered) count: {high_value_orders_filtered.count()}", flush=True)

        # Eğer filtre sonrası kayıt varsa Slack bildirimi gönder
        if not high_value_orders_filtered.isEmpty():
            print("Found high-value orders, attempting to send Slack notification...", flush=True)
            for row in high_value_orders_filtered.collect():
                message = (f"🚨 Büyük Alışveriş Uyarısı!\n"
                           f"Kullanıcı: {row.UserId}\n"
                           f"Sipariş ID: {row.OrderId}\n"
                           f"Tutar: {row.TotalPrice:.2f} TL")
                # send_slack_notification fonksiyonunu çağırıyoruz
                send_slack_notification(message)
        else:
            print("No high-value orders found in this batch.", flush=True)


query = parsed_df.writeStream \
    .foreachBatch(process_batch) \
    .option("checkpointLocation", "s3a://purchased-items/checkpoint2/") \
    .outputMode("append") \
    .start()

query.awaitTermination()
