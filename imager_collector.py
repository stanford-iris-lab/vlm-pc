import pyrealsense2 as rs
import threading
import time
import numpy as np
from PIL import Image
from queue import Queue
import os

class ImageCollector:
    def __init__(self, logdir="log", save_every_n=1):
        """
        logdir = None turns off logging
        """
        
        self.logdir = logdir
        self.save_every_n = save_every_n

        # Camera setup
        self.pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.color, 640, 480, rs.format.rgb8, 30)
        self.pipeline.start(config)

        # Threading and synchronization
        self.active = False
        self.capture_thread = threading.Thread(target=self._capture_run)
        if self.logdir is not None:
            self.logdir = self.logdir + "/im_stream/"
            if not os.path.exists(self.logdir):
                os.makedirs(self.logdir)
            self.log_thread = threading.Thread(target=self._log_run)
            self.queue = Queue()


        # Lock for thread-safe access to the latest image
        self.lock = threading.Lock()
        self.count = 0
        self.start_time = time.time()

        # The latest image captured
        self.latest_image = None

    def resize(self, image_array):
        image = Image.fromarray(image_array)

        # Calculate the new dimensions
        new_width = int(image.width / 2.0)
        new_height = int(image.height / 2.0)

        # Resize the image
        resized_image = image.resize((new_width, new_height))

        # Convert the resized image back to numpy array
        resized_image_array = np.array(resized_image)
        return resized_image_array

    def set_reference_time(self, time):
        self.reference_time = time

    def start(self):
        """Starts both the capture and log threads."""
        self.start_time = time.time()
        self.active = True
        self.capture_thread.start()
        if self.logdir is not None:
            self.log_thread.start()

    def stop(self):
        """Stops both threads and waits for them to finish."""
        self.active = False
        self.capture_thread.join()
        if self.logdir is not None:
            self.log_thread.join()
        self.pipeline.stop()
        print("Collected " + str(self.count) + " images in " + str(time.time() - self.start_time) + " seconds")

    def _capture_run(self):
        """Capture thread for collecting images and timestamps."""
        while self.active:
            frames = self.pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame:
                continue
            timestamp = time.time() - self.reference_time

            image = np.asanyarray(color_frame.get_data())
            
            #with self.lock:
            self.latest_image = self.resize(image)

            if self.logdir is not None:
                self.queue.put((image, timestamp))

            time.sleep(0.05)  # Maintain approximately 20 Hz rate TODO: make more accurate if desired

    def _log_run(self):
        """Logging thread for saving images and timestamps."""
        while self.active or not self.queue.empty():
            image, timestamp = self.queue.get()
            self.count += 1
            image_pil = Image.fromarray(image)
            filename = f"image_{timestamp:.3f}.png"
            # save only one in ten images
            if self.count % self.save_every_n == 0:
                image_pil.save(self.logdir + filename)

    def get_latest_image(self):
        """Get the latest image captured by the camera."""
        #with self.lock:
        return self.latest_image

if __name__ == '__main__':
    # Usage
    collector = ImageCollector()
    collector.start()

    # Example to run for a certain period then stop
    time.sleep(10)  # Collect and log data for 10 seconds
    collector.stop()
