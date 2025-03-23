from fastapi import FastAPI, Request
import httpx
from pydantic import BaseModel
import os

app = FastAPI()

# Replace these with your own WhatsApp Business credentials
WHATSAPP_API_URL = "https://graph.facebook.com/v17.0/{phone_number_id}/messages"
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
PHONE_NUMBER_ID = "YOUR_PHONE_NUMBER_ID"

# Model for WhatsApp message
class WhatsAppMessage(BaseModel):
    object: str
    entry: list

# Webhook to receive incoming messages from WhatsApp
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    message_data = WhatsAppMessage(**data)
    
    if message_data.entry and message_data.entry[0]["changes"]:
        messages = message_data.entry[0]["changes"][0]["value"]["messages"]
        if messages:
            for message in messages:
                if message.get("text"):  # Check if message is text
                    user_message = message["text"]["body"]
                    user_phone = message["from"]

                    # Logic to handle user input and respond
                    if user_message.lower() == "hi":
                        await send_message(user_phone, "Hello! Welcome to our service. Reply with '1' for Info, '2' for Support, or '3' to submit a request.")
                    elif user_message == "1":
                        await send_message(user_phone, "Here is the info you requested.")
                    elif user_message == "2":
                        await send_message(user_phone, "Our support team will reach out to you soon.")
                    elif user_message == "3":
                        await send_message(user_phone, "Please submit your text, image, or audio request.")
                    else:
                        await send_message(user_phone, "I did not understand that. Please choose from the options: 1, 2, or 3.")

    return {"status": "success"}

# Function to send a message using WhatsApp API
async def send_message(to: str, text: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            WHATSAPP_API_URL.format(phone_number_id=PHONE_NUMBER_ID),
            headers={
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": text}
            }
        )
    if response.status_code == 200:
        print(f"Message sent to {to}: {text}")
    else:
        print(f"Failed to send message. Status code: {response.status_code}")

# Endpoint to verify webhook with WhatsApp
@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode and token and mode == "subscribe" and token == "YOUR_VERIFY_TOKEN":
        return challenge
    return {"error": "Invalid verification token"}
