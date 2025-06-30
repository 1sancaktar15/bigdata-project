from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from kafka import KafkaProducer
import json
import time

app = FastAPI()

# Kafka bağlantısını retry loop ile kur
producer = None
while producer is None:
    try:
        producer = KafkaProducer(
            bootstrap_servers='kafka:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        print("✅ Kafka bağlantısı kuruldu.")
    except Exception as e:
        print("❌ Kafka hazır değil, tekrar denenecek...")
        time.sleep(5)

# MODELLER

class Attributes(BaseModel):
    ProductId: str
    Price: float
    Discount: float

class Event(BaseModel):
    UserId: str
    SessionId: str
    EventName: str
    TimeStamp: str
    Attributes: Attributes

class Product(BaseModel):
    ProductId: str
    ItemCount: int
    ItemPrice: float
    ItemDiscount: float

class Purchase(BaseModel):
    SessionId: str
    TimeStamp: str
    UserId: str
    TotalPrice: float
    OrderId: str
    PaymentType: str
    Products: List[Product]

# ENDPOINTLER

@app.put("/send-event")
async def send_event(event: Event):
    producer.send("UserEvents", event.dict())
    return {"status": "event sent"}

@app.post("/purchased-items")
async def purchased_items(purchases: List[Purchase]):
    for item in purchases:
        producer.send("PurchasedItem", item.dict())
    return {"status": f"{len(purchases)} items sent"}
