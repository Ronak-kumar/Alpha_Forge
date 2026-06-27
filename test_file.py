import asyncio
import httpx
import requests

async def ping_data_service():
    for i in range(10):  # Try for 10 attempts
        payload = {
        "asset_class": "FNO",
        "year": 2020,
        "month": i + 1,
        "symbol": "NIFTY",
        "exchange": "NSE"
        }

        # response = requests.post(
        #     "http://localhost:8000/data/month",
        #     json=payload,
        #     timeout=30
        # )

        # print("Status:", response.status_code)
        # print("Response:", response.json())

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/data/month",
                json=payload,
                timeout=60
            )

            print("Status:", response.status_code)
            print(response.json())


if __name__ == "__main__":
    asyncio.run(ping_data_service())