from typing import Union
import base64
import io

from fastapi import FastAPI, File, UploadFile

from openai import OpenAI
from pydantic import BaseModel
import os


app = FastAPI()


@app.get("/")
async def read_root():

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.responses.create(
        model="gpt-4.1",
        input="Tell me a three sentence bedtime story about a unicorn."
    )

    print(response)

class CardInfo(BaseModel):
    name: Union[str, None] = None
    type: Union[str, None] = None
    cost: Union[int, None] = None
    rarity: Union[str, None] = None
    color: Union[str, None] = None
    counter: Union[int, None] = None
    trait: Union[str, None] = None
    card_number: Union[str, None] = None
    price: Union[float, None] = None
    tcgplayer_url: Union[str, None] = None


@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png"]:
        return {"error": "Only JPEG and PNG images are supported."}
    image_bytes = await file.read()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    mime_type = file.content_type
    # Encode image as base64 and create data URL
    image_base64 = base64.b64encode(image_bytes).decode()
    data_url = f"data:{mime_type};base64,{image_base64}"
    # Send image to OpenAI GPT-4o for analysis using image_url
    response = client.responses.parse(
        model="gpt-4o",
        tools= [ { "type": "web_search_preview", "search_context_size": "high" } ],
        input=[
            {"role": "system", "content": "You are a helpful assistant that describes images."},
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Analyze this image and get the details from the card. Then search the internet by searching 'tcgplayer {card name} {card number}'. Make sure you find the correct card because there are many cards that have the same name. "},
                    {"type": "input_image", "image_url": data_url}
                ]
            }
        ],
        text_format=CardInfo,
    )
    description = response.output_parsed
    print(response)
    print("======================================")
    print(description)
    return {"description": description, "filename": file.filename, "size": len(image_bytes)}


