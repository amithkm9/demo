from fastapi import FastAPI
import hackathon_final_SDK
import uvicorn
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
import json
from SSL_ import no_ssl_verification

class Quant_and_Image(BaseModel):
    quantity : int
    image : str

class Image_Message(BaseModel):
    image_message :  str
    language : str

class Text_Message(BaseModel):
    query : str

app = FastAPI()

#nfo_based_on_image_prescription
@app.post("/generate_info_from_image_prescription")
def generate_info(image_message : Image_Message):
    with no_ssl_verification():
        print("API called")
        ## Query formating
        try:
            
            response = hackathon_final_SDK.info_based_on_image_prescription(image_message.image_message, image_message.language)
            return {"response" : response}
        except Exception as e:
            print("Exception occured at API call", e)
            return {"response" : {"content" : "Something went wrong try again."}, "status" : "InternalServerError"}




@app.post("/order_on_image")
def order_from_image(quant_and_image : Quant_and_Image):
    with no_ssl_verification():
        print("API called")
        ## Query formating
        
        try:
        
            response = hackathon_final_SDK.order_based_on_image(quant_and_image.quantity, quant_and_image.image)
            return {"response" : response}
        except Exception as e:
            print("Exception occured at API call", e)
            return {"response" : {"content" : "Something went wrong try again."}, "status" : "InternalServerError"}
        

@app.post("/generate_info_from_image")
def generate_info(image_message : Image_Message):
    with no_ssl_verification():
        print("API called")
        ## Query formating
        try:
            
            response = hackathon_final_SDK.info_based_on_image(image_message.image_message, image_message.language)
            return {"response" : response}
        except Exception as e:
            print("Exception occured at API call", e)
            return {"response" : {"content" : "Something went wrong try again."}, "status" : "InternalServerError"}

@app.post("/order_based_on_name")
def order_text(text_mssg : Text_Message):
    with no_ssl_verification():
        print("API CALLED")
        try:
            response = hackathon_final_SDK.order_based_on_name(text_mssg.query)
            return {"response" : response}
        except Exception as e:
            print("Exception occured at API call", e)
            return {"response" : {"content" : "Something went wrong try again."}, "status" : "InternalServerError"}
        
@app.post("/order_on_image_prescription")
def order_from_image(quant_and_image : Image_Message):
    with no_ssl_verification():
        print("API called")
        ## Query formating
        
        try:
        
            response = hackathon_final_SDK.order_based_on_image_prescription(quant_and_image.image_message)
            return {"response" : response}
        except Exception as e:
            print("Exception occured at API call", e)
            return {"response" : {"content" : "Something went wrong try again."}, "status" : "InternalServerError"}

if __name__ == '__main__':
    uvicorn.run(app, port=8000, host='0.0.0.0')