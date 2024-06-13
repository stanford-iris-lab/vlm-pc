import os
import imageio
import json
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def get_sorted_vlm_times(directory):
    # List to store the time values
    times = []
    
    # Iterate through each file in the directory
    for filename in os.listdir(directory):
        if filename.startswith('image_') and filename.endswith('.png'):
            # Strip off the 'image_' prefix and '.png' suffix and extract the time part
            time_str = filename[len('image_'):-len('.png')]
            try:
                # Convert the time string to a float and add it to the list
                times.append(float(time_str))
            except ValueError:
                # Handle the case where the conversion to float fails
                print(f"Skipping invalid filename: {filename}")
    
    # Sort the list of times
    times.sort()
    
    return times

def get_last_vlm_time(input_time, times):
     # Initialize the last time to None
    last_time = None
    
    # Iterate through the sorted times to find the last time before the input time
    for time in times:
        if time < input_time:
            last_time = time
        else:
            break
    
    return last_time

import cv2
import numpy as np

def add_text(input_image, text, position=(50, 50), font_scale=1, color=(255, 255, 255), thickness=2, font=cv2.FONT_HERSHEY_SIMPLEX):
    """
    Adds text to an image using OpenCV with default parameters.

    Args:
    input_image (numpy.array): The input image array (BGR format).
    text (str): Text to add to the image.
    position (tuple, optional): Bottom-left corner of the text in the image (x, y), default is (50, 50).
    font_scale (float, optional): Font scale (size of the text), default is 1.
    color (tuple, optional): Color of the text in BGR (blue, green, red), default is white (255, 255, 255).
    thickness (int, optional): Thickness of the line used to draw the text, default is 2.
    font (int, optional): Font type from OpenCV fonts, default is cv2.FONT_HERSHEY_SIMPLEX.

    Returns:
    numpy.array: The image array with text added.
    """
    # Put text on the image
    cv2.putText(input_image, text, position, font, font_scale, color, thickness)

    return input_image


def create_movie(folder, fps=5):
    image_folder = folder + "/im_stream"
    vlm_times = get_sorted_vlm_times(folder + "/vlm")

    # Retrieve a sorted list of image files
    image_files = sorted([img for img in os.listdir(image_folder) if img.startswith("image_") and img.endswith(".png")], key=lambda x: float(x[:-4].split('_')[1]))
    # Initialize the writer with the desired output file and fps
    writer = imageio.get_writer(folder + "/movie.mp4", fps=fps)

    # Iterate over each file in the sorted list of images
    for filename in image_files:
        print(filename)
        image_path = os.path.join(image_folder, filename)
        time = float(filename[:-4].split("_")[1])
        last_vlm_time = get_last_vlm_time(time, vlm_times)
        print(last_vlm_time)
        # Read each image file

        try:
            image = imageio.imread(image_path)
        except:
            continue
        if last_vlm_time is not None:
            with open(f'{folder}/vlm/log_{last_vlm_time}.json', 'r') as file:
                data = json.load(file)
                hl_command = data.get('Result', None)
                if isinstance(hl_command, list):
                    hl_command = " ".join(hl_command)
        
            image = add_text(image, hl_command)
        # Append the image to the output video
        writer.append_data(image)
        
    # Close the writer to finalize the video file
    writer.close()
    print(f"Movie created")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--logdir", required=True)

    args = parser.parse_args()

    create_movie("log/" + args.logdir)
