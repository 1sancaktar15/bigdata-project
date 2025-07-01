README dosyan için temel ve açıklayıcı bir şablon hazırladım. Ödev PDF’ini görmediğim için genel büyük veri projesi ve senin anlattıkların üzerinden uyarladım. İstersen, PDF’den önemli detayları paylaşırsan daha spesifik hale getirebilirim.

# Big Data Project

Bu proje, büyük veri teknolojileri kullanarak **MinIO üzerinde saklanan satın alma verilerinin** analizi ve sonuçların PostgreSQL veritabanına kaydedilmesini kapsamaktadır. Proje kapsamında Apache Kafka, Spark, Airflow, MongoDB, MinIO ve Jupyter Notebook gibi araçlar Docker ortamında entegre edilmiştir.

## İçindekiler

- `docker-compose.yaml`: Proje bileşenlerinin Docker ile kurulumu ve konfigürasyonu  
- `notebooks/minio_parquet_read.ipynb`: MinIO’dan Parquet dosyalarının okunması, verilerin Spark ile analizi ve PostgreSQL’e yazılması  
- `fastapi-app/`: Kafka ile entegre çalışan FastAPI uygulaması  
- `airflow/`: Apache Airflow DAG’ları ve konfigürasyonu  

## Proje Adımları

1. **MinIO’dan Veri Okuma:** Satın alma verileri Parquet formatında MinIO S3 bucket’ından PySpark ile okunur.  
2. **Veri Analizi:**  
   - En çok satılan ürünler  
   - En çok tercih edilen ödeme tipi  
   - Son 1 saatte en yüksek tutarlı siparişi veren top 10 müşteri  
   - Aynı ürünü birden çok kez satın alan müşteriler ve birden çok aldıkları ürünler  
3. **Veri Kaydetme:** Analiz sonuçları PostgreSQL veritabanındaki tablolara yazılır.  
4. **SQL Sorguları:** PostgreSQL’de en çok tekrar tekrar satın alınan en popüler ilk 10 ürün sorgusu yazılır ve sonuçlar Jupyter Notebook’ta gösterilir.  

## Kullanılan Teknolojiler

- Apache Kafka  
- Apache Spark (PySpark)  
- Apache Airflow  
- PostgreSQL  
- MongoDB  
- MinIO  
- FastAPI  
- Jupyter Notebook  
- Docker & Docker Compose  

## Çalıştırma Talimatları

1. Proje dizininde `docker-compose up -d` komutu ile tüm servisleri başlatın.  
2. `notebooks/minio_parquet_read.ipynb` dosyasını Jupyter Notebook üzerinden açarak analizleri çalıştırın.  
3. PostgreSQL veritabanına yazılan sonuçları kontrol edin.  
4. Airflow arayüzü ile DAG’ların durumunu takip edin.  

## İletişim

Proje ile ilgili sorularınız için [GitHub Issues](https://github.com/1sancaktar15/bigdata-project/issues) üzerinden iletişime geçebilirsiniz.
