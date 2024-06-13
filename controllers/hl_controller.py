import threading
import time
from datetime import datetime
import numpy as np
from queue import Queue, Empty
from PIL import Image
import json
import os
import logging
import copy

class VLM_HL_Controller:
    """
    Vanilla Controller. New chat with the same prompt and one image each time.
    """
    def __init__(self,
                 latest_image_func,
                 vlm_query_func,
                 hl_command_handle_func,
                 opening_query_text,
                 logdir="log",
                 interval=3,
                 turn=False,
                 ):
        self.logdir = logdir + "/vlm/"

        self.interval = interval

        if not os.path.exists(self.logdir):
            os.makedirs(self.logdir)

        self.query_queue = Queue()
        self.running = True

        self.opening_query_text = opening_query_text

        self.hl_command_handle_func = hl_command_handle_func
        self.latest_image_func = latest_image_func
        self.vlm_query_func = vlm_query_func

        self.heading = 0
        self.last_query = time.time()
        self.turn = turn

    def set_reference_time(self, time):
        self.reference_time = time

    def get_last_n_words(self, text, n):
        text = text.lower().replace("*", "").replace("magnitude: ", "").replace("action: ", "")
        words = text.replace("\n", " ").replace(".", "").replace(",", "").strip().split(" ")
        return words[-n:]

    def query(self):
        while self.running:
            start_time = time.time() - self.reference_time

            while time.time() - self.last_query < self.interval:
                time.sleep(0.05)

            # Retrieve the image
            image = self.latest_image_func()

            # text = self.query_text + " Your heading is currently " + str(self.heading)
            text = self.opening_query_text
            # Query GPT4 with the image and text
            record_message_hist = []
            response = self.vlm_query_func(image, text, record_message_hist)
            result = self.get_last_n_words(response, 2)
            return_time = time.time() - self.reference_time

            self.hl_command_handle_func(result, self.turn)

            if result[0].lower() == 'right':
                self.heading += self.interval * 30
            elif result[0].lower() == 'left':
                self.heading -= self.interval * 30
            self.heading %= 360

            # Enqueue the data for logging
            self.query_queue.put((image, text, response, result, start_time, return_time, record_message_hist))
            self.last_query = time.time()

    def log_data_thread(self):
        while self.running or not self.query_queue.empty():
            try:
                log_info = self.query_queue.get(timeout=0.5)
                self.log_data(*log_info)
            except Empty:
                continue

    def log_data(self, image, text, response, result, query_time, return_time, message_history):
        # Save the image as a PNG
        img = Image.fromarray(image.astype('uint8'))
        img.save(self.logdir + "/" + f'image_{return_time}.png')
        
        # Save the text and result as JSON
        data = {
            "QueryTimestamp": query_time,
            "Text": text,
            "Response": response,
            "Result": result
        }
        with open(self.logdir + "/" + f'log_{return_time}.json', 'w') as file:
            json.dump(data, file, indent=4)
        
        try:
            if isinstance(message_history, list):
                message_history = {"chat": message_history}
            for history_name, history in message_history.items():
                with open(self.logdir + "/" + f'{history_name}_{return_time}.json', 'w') as file:
                    json.dump(history, file, indent=4)
        except TypeError as e:
            print("Cannot save history because not serializable.")

    def start(self):
        self.query_thread = threading.Thread(target=self.query)
        self.log_thread = threading.Thread(target=self.log_data_thread)

        self.query_thread.start()
        self.log_thread.start()

    def stop(self):
        self.running = False
        self.query_thread.join()
        self.log_thread.join()
