import zmq
import json
import zlib
from PIL import Image
import base64
import io

def send_dictionary(dictionary, host='127.0.0.1', port=12345):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://{host}:{port}")

    json_data = json.dumps(dictionary).encode('utf-8')
    compressed_data = zlib.compress(json_data)
    socket.send(compressed_data)

    compressed_response = socket.recv()
    decompressed_response = zlib.decompress(compressed_response).decode('utf-8')
    response_dict = json.loads(decompressed_response)
    return response_dict

def encode_image(image, output_size=(400, 300), quality=85):
    # Open the image and resize it

    with Image.fromarray(image) as img:
        img = img.resize(output_size, Image.Resampling.LANCZOS)

        # Save the resized image to a bytes buffer
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG', quality=quality)

        # Encode to base64
        return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')


class QueryClient:

    def __init__(self, host="192.168.123.42", port=12345) -> None:

        self.host = host
        self.port = port

    def query(self, text=None, image=None, message_history=None):

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

        message_history.extend(new_message)

        response = send_dictionary(message_history, host=self.host, port=self.port)

        message_history.append({"role": "assistant", "content": response['response']})

        return response['response']



