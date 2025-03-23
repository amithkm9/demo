import httpx
from fastapi import FastAPI

app = FastAPI()

@app.get("/ok")
async def send_message():
    url = "https://graph.facebook.com/v20.0/<media-id>/messages"
    
    payload = {
        "messaging_product": "whatsapp",
        "to": "<num>",  # Include country code, e.g., "1234567890"
        "type": "text",
        "text": {
            "body": "Hello! This is a test message."
        }
    }
    
    headers = {
        "Authorization": "Bearer <token>",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        print(response.json())

    return response.json()
# Run the function
# res = await send_message()