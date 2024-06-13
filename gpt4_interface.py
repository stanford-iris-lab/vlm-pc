import os
import openai
import base64
from PIL import Image
import io
import logging
import numpy as np
import requests
import time
# import sys

openai.api_key = os.getenv('OPENAI_API_KEY')


def encode_image(image, output_size=(400, 300), quality=85):
    # Open the image and resize it

    logging.info(image.shape)

    with Image.fromarray(image) as img:
        img = img.resize(output_size, Image.Resampling.LANCZOS)

        # Save the resized image to a bytes buffer
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG', quality=quality)

        # Encode to base64
        return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

def curl_openai(payload, max_retries=3):
    retry_delay = 15  # Starting timeout
    retry_count = 0
    
    headers = {
        "Authorization": "Bearer " + GPT4V_KEY,  # Replace YOUR_API_KEY with your actual API key
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4o",
        "messages": payload['messages'],
        "temperature": payload['temperature'],
        "top_p": payload['top_p'],
        "max_tokens": payload['max_tokens'],
    }

    while retry_count < max_retries:
        try:
            response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data, timeout=retry_delay)
            response.raise_for_status()  # Raise error for non-2xx status codes
            return response.json()['choices'][0]['message']['content']  # Return JSON response
        except requests.exceptions.RequestException as e:
            print("Error:", e)  # Log error
            retry_count += 1
            if retry_count < max_retries:
                print(f"Retrying in a second, limit={retry_delay} seconds...")
                time.sleep(1)
                retry_delay *= 2  # Exponential backoff
    return None


def get_response_openai(payload):
    return openai.ChatCompletion.create(
            model="gpt-4o",
            messages=payload['messages'],
            temperature=payload['temperature'],
            top_p=payload['top_p'],
            max_tokens=payload['max_tokens'],
            request_timeout=5
        ).choices[0].message['content']


def query_gpt4v(image, text, message_history=None):
    if message_history is None:
        message_history = []

    

    # Create the new message to be added
    if image is not None or text is not None:
        image_base64 = encode_image(image)
        new_message = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": text
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}",
                        },
                    }
                ]
            }
        ]

    # message_history.insert(0, map_message[0])
    # Append the new message to the message history
    message_history.extend(new_message)

    # Payload for the request
    payload = {
        "messages": message_history,
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": 800
    }

    print("OpenAI API querying...")
    logging.info("OpenAI API querying...")
    # Send request using the OpenAI Python package
    try:
        # response = get_response_openai(payload)
        assistant_message = curl_openai(payload)
        # Append assistant's response to the message history
        message_history.append({"role": "assistant", "content": assistant_message})
    except openai.OpenAIError as e:
        raise SystemExit(f"Failed to make the request. Error: {e}")

    print(assistant_message)
    return assistant_message


def query_gpt4v_mult(images, text, message_history=None):
    if message_history is None:
        message_history = []

    # Encode all images
    encoded_images = []
    for image in images:
        image_base64 = encode_image(image)
        encoded_images.append(f"data:image/jpeg;base64,{image_base64}")

    # Create the new message to be added
    new_message = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": text
                },
                *[
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_base64,
                        },
                    }
                    for image_base64 in encoded_images
                ]
            ]
        }
    ]

    # message_history.insert(0, map_message[0])
    # Append the new message to the message history
    message_history.extend(new_message)

    # Payload for the request
    payload = {
        "messages": message_history,
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": 800
    }

    print("OpenAI API querying...")
    logging.info("OpenAI API querying...")
    # Send request using the OpenAI Python package
    try:
        # response = get_response_openai(payload)
        assistant_message = curl_openai(payload)
        # Append assistant's response to the message history
        message_history.append({"role": "assistant", "content": assistant_message})
    except openai.OpenAIError as e:
        raise SystemExit(f"Failed to make the request. Error: {e}")

    return assistant_message
