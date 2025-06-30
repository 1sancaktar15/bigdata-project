from faker import Faker
import httpx
import random
import asyncio
import uuid

fake = Faker()

API_URL = "http://localhost:8000"

event_names = ["PageVisited", "AddedBasket", "CheckedProductReviews"]
payment_types = ["CreditCard", "Paypal", "CashOnDelivery"]

# Tek bir Event gönder
async def send_event():
    payload = {
        "UserId": str(uuid.uuid4()),
        "SessionId": str(uuid.uuid4()),
        "EventName": random.choice(event_names),
        "TimeStamp": fake.iso8601(),
        "Attributes": {
            "ProductId": str(uuid.uuid4()),
            "Price": round(random.uniform(10, 500), 2),
            "Discount": round(random.uniform(0, 50), 2)
        }
    }
    async with httpx.AsyncClient() as client:
        resp = await client.put(f"{API_URL}/send-event", json=payload)
        print("Event:", resp.json())

# Birden fazla Purchase gönder
async def send_purchases():
    purchases = []
    for _ in range(random.randint(1, 3)):
        products = []
        for _ in range(random.randint(1, 4)):
            products.append({
                "ProductId": str(uuid.uuid4()),
                "ItemCount": random.randint(1, 5),
                "ItemPrice": round(random.uniform(20, 300), 2),
                "ItemDiscount": round(random.uniform(0, 30), 2)
            })
        purchases.append({
            "SessionId": str(uuid.uuid4()),
            "TimeStamp": fake.iso8601(),
            "UserId": str(uuid.uuid4()),
            "TotalPrice": sum(p["ItemPrice"] * p["ItemCount"] for p in products),
            "OrderId": str(uuid.uuid4()),
            "PaymentType": random.choice(payment_types),
            "Products": products
        })
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{API_URL}/purchased-items", json=purchases)
        print("Purchases:", resp.json())

# Sürekli veri üret
async def main_loop():
    while True:
        await send_event()
        await send_purchases()
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main_loop())
