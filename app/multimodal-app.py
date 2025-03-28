from fastapi import FastAPI, Request, BackgroundTasks, status
import httpx
from pydantic import BaseModel
import os
import requests
from dotenv import load_dotenv
from io import BytesIO
import base64
from PIL import Image
from fastapi.responses import JSONResponse

load_dotenv()
app = FastAPI()


# Replace with your own WhatsApp Business credentials
# MEDIA_URL="https://graph.facebook.com/v20.0/{media_id}"

WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL")
MEDIA_URL = "https://graph.facebook.com/v20.0/{media_id}"
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
AGENT_URL = os.getenv("AGENT_URL")

# Model for WhatsApp message
class WhatsAppMessage(BaseModel):
    object: str
    entry: list

# Webhook to receive incoming messages from WhatsApp
@app.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    # print("pong")
    message_data = WhatsAppMessage(**data)
    print(message_data)
    if message_data.entry and message_data.entry[0]["changes"] and "messages" in message_data.entry[0]["changes"][0]["value"].keys() :
        messages = message_data.entry[0]["changes"][0]["value"]["messages"]
        print(messages)
        if messages:    
        # for message in messages:
            message = messages[-1]
            user_phone = message["from"]

            # Handling Text Message
            if message.get("text"):
                user_message = message["text"]["body"]

                # Respond based on the text input
                if user_message.lower() == "hi":
                    background_tasks.add_task(trigger,user_phone)

                if user_message[:6].lower() == "order:":
                    query=user_message[6:]
                    api_url = AGENT_URL + "/order_based_on_name"
                    timeout = (15,60)
                    payload = {"query": query}
                    headers={"Authorization": f"Bearer {ACCESS_TOKEN}","Content-Type": "application/json"}
                    response = requests.post(api_url, json=payload, headers=headers, timeout=timeout)
                    await send_message(user_phone, response.json()["response"]["content"])

                return JSONResponse(content={"status": "ok"}),200

            elif message.get("image"):
                media_id = message["image"]["id"]
                media_url = await fetch_media(media_id)
                print(media_url)
                async with httpx.AsyncClient() as client:
                    headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
                    response = await client.get(media_url,headers=headers)
                    response.raise_for_status()  # Ensure the request was successful
                
                # Convert the image content to base64
                image = Image.open(BytesIO(response.content))
                buffered = BytesIO()
                image.save(buffered, format="JPEG")  # You can change the format if needed
                image.save("./test.jpeg", format="JPEG")
                base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
                
                background_tasks.add_task(llm_call,base64_image,user_phone)
                return JSONResponse(content={"status": "ok"}),200

            # Handling Audio Message
            elif message.get("audio"):
                media_id = message["audio"]["id"]
                media_url = await fetch_media(media_id)
                await send_message(user_phone, f"Audio received. Download URL: {media_url}")

    return "",200

async def trigger(user_phone:str):
    await send_message(user_phone, "Hello! Welcome to CurePharmAI. Please send image of the prescription or the medicine.")
    return None

async def llm_call(image:str, user_phone:str):
    api_url = AGENT_URL + "/generate_info_from_image"
    timeout = (15,60)
    payload = {"image_message":image, "language":"Hindi"}
    headers={"Authorization": f"Bearer {ACCESS_TOKEN}","Content-Type": "application/json"}
    response = requests.post(api_url, json=payload, headers=headers, timeout=timeout)
    await send_message(user_phone, response.json()["response"])
    return None

async def order_by_name(user_phone, name:str):
    api_url = AGENT_URL + "/order_based_on_name"
    timeout = (15,60)
    payload = {"query": name}
    headers={"Authorization": f"Bearer {ACCESS_TOKEN}","Content-Type": "application/json"}
    response = requests.post(api_url, json=payload, headers=headers, timeout=timeout)
    await send_message(user_phone, response.json()["response"]["content"])
    return None

# Function to send a message using WhatsApp API
async def send_message(to: str, text: str):
    response = requests.post(WHATSAPP_API_URL,headers={"Authorization": f"Bearer {ACCESS_TOKEN}","Content-Type": "application/json"},json={"messaging_product": "whatsapp","recipient_type": "individual","to": to,"type": "text","text": {"body": text}})
    
    if response.status_code == 200:
        print(f"Message sent to {to}: {text}")
    else:
        print(f"Failed to send message. Status code: {response.status_code}")

# Function to fetch media (image or audio) using the media ID
async def fetch_media(media_id: str):
    print("Entered fetch media", media_id)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            MEDIA_URL.format(media_id=media_id),
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
        )
    if response.status_code == 200:
        media_data = response.json()
        media_url = media_data.get("url")
        return media_url
    else:
        print(f"Failed to fetch media. Status code: {response.status_code}")
        return None

# Endpoint to verify webhook with WhatsApp
# @app.get("/webhook")
# async def verify_webhook(request: Request):
#     mode = request.query_params.get("hub.mode")
#     token = request.query_params.get("hub.verify_token")
#     challenge = request.query_params.get("hub.challenge")
#     print(mode)
#     print(token)
#     print(challenge)

#     # if mode and token and mode == "subscribe" and token == "1234":
#         # return {"hub_verfiy_mode":mode,"hub_verify_token":token, "hub_verify_challange":challenge }
#     # return token

#     return int(challenge)
#     # return {"error": "Invalid verification token"}
