if __name__ == "__main__":
    import sys
    sys.path.append('../')
    from hl_controller import VLM_HL_Controller
else:
    from .hl_controller import VLM_HL_Controller
import time
import copy
from PIL import Image
import base64
import io
import numpy as np

def encode_image(image, output_size=(400, 300), quality=85):
    # Open the image and resize it

    with Image.fromarray(image) as img:
        img = img.resize(output_size, Image.Resampling.LANCZOS)

        # Save the resized image to a bytes buffer
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG', quality=quality)

        # Encode to base64
        return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')


def append_to_message_hist_as_user(message_hist, text=None, image=None):
    if text is not None:
        new_message = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": text
                    },
                ]
            }
        ]
        message_hist.extend(new_message)

    if image is not None:

        image_base64 = encode_image(image)

        new_message = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}",
                        },
                    }
                ]
            }
        ]
        message_hist.extend(new_message)

import os
from PIL import Image

def list_images_in_folder(folder_path):
    # Supported image extensions
    image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')

    # List all files in the folder
    files = os.listdir(folder_path)
    
    # Filter out non-image files
    images = [f for f in files if f.lower().endswith(image_extensions)]
    
    return images

def get_icl_data(folder_path):
    # Get the list of images
    images = list_images_in_folder(folder_path)
    image_tuples = []
    for image_name in images:
        # Construct the full path to the image
        image_path = os.path.join(folder_path, image_name)
        
        # Open the image using PIL
        with Image.open(image_path) as img:
            img = np.array(img)
            actions = image_name.split('.')[0]
            actions = actions.split('_')
            if len(actions) > 1:
                actions = " or ".join(actions)
            else:
                actions = actions[0]
            image_tuples.append((img, actions))

    return image_tuples
