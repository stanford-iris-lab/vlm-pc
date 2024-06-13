from .hl_controller import VLM_HL_Controller
import time
import copy

class NoHist_VLM_HL_Controller(VLM_HL_Controller):

    def __init__(self, latest_image_func, vlm_query_func,
                 hl_command_handle_func, opening_query_text,
                 sucessive_text, logdir="log", interval=3, turn=False):
        super().__init__(latest_image_func, vlm_query_func, hl_command_handle_func,
                         opening_query_text, logdir, interval, turn)
        self.successive_text = sucessive_text

    def query(self):
        count = 0
        message_history = []
        while self.running:
            start_time = time.time() - self.reference_time

            while time.time() - self.last_query < self.interval:
                time.sleep(0.05)

            image = self.latest_image_func()

            text = self.opening_query_text

            response = self.vlm_query_func(image, text, [])
            result = self.get_last_n_words(response, 2)

            print(response, result)

            record_message_hist = copy.deepcopy(message_history)

            return_time = time.time() - self.reference_time

            self.query_queue.put((image, text, response, result, start_time, return_time, record_message_hist))

            self.hl_command_handle_func(result, self.turn)

            if result[0].lower() == 'right':
                self.heading += self.interval * 30
            elif result[0].lower() == 'left':
                self.heading -= self.interval * 30
            self.heading %= 360

            # Enqueue the data for logging

            self.last_query = time.time()

            count += 1
