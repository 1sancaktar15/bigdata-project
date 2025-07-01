from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from kafka import KafkaConsumer
from pymongo import MongoClient
import json
import time
import os
import sys

# "my_project" klasörünün tam yolu
project_root = r"C:\Users\Elif\Desktop\bigdata-project"

if project_root not in sys.path:
    sys.path.append(project_root)

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

def kafka_to_mongo():
    consumer = KafkaConsumer(
        'UserEvents',
        bootstrap_servers='kafka:9092',
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='airflow-user-events-group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        consumer_timeout_ms=10000
    )
    # DÜZELTİLEN SATIR:
    mongo_client = MongoClient('mongodb://mongo:27017/')
    db = mongo_client.bigdata
    collection = db.user_events_raw

    batch = []
    batch_size = 100
    start_time = time.time()

    for message in consumer:
        data = message.value
        batch.append(data)
        if len(batch) >= batch_size:
            collection.insert_many(batch)
            batch = []
            print(f"Inserted {batch_size} documents")
        if time.time() - start_time > 50:
            break

    if batch:
        collection.insert_many(batch)
        print(f"Inserted {len(batch)} documents")

    consumer.close()
    mongo_client.close()

def aggregate_events():
    # DÜZELTİLEN SATIR:
    mongo_client = MongoClient('mongodb://mongo:27017/')
    db = mongo_client.bigdata
    raw_collection = db.user_events_raw
    agg_collection = db.user_events_aggregated

    pipeline = [
        {"$group": {
            "_id": {"UserId": "$UserId", "EventName": "$EventName"},
            "EventCount": {"$sum": 1}
        }},
        {"$project": {
            "UserId": "$_id.UserId",
            "EventName": "$_id.EventName",
            "EventCount": 1,
            "_id": 0
        }}
    ]

    results = list(raw_collection.aggregate(pipeline))

    for doc in results:
        agg_collection.update_one(
            {"UserId": doc["UserId"], "EventName": doc["EventName"]},
            {"$set": {"EventCount": doc["EventCount"]}},
            upsert=True
        )

    print(f"Aggregated {len(results)} user-event combinations")
    mongo_client.close()

with DAG(
    dag_id='user_events_ingest_dag',
    default_args=default_args,
    description='Ingest UserEvents from Kafka to MongoDB',
    schedule_interval=timedelta(minutes=2),
    start_date=datetime(2025, 6, 30),
    catchup=False
) as dag:

    ingest_task = PythonOperator(
        task_id='kafka_to_mongo_task',
        python_callable=kafka_to_mongo
    )

    aggregate_task = PythonOperator(
        task_id='aggregate_events_task',
        python_callable=aggregate_events
    )

    ingest_task >> aggregate_task
