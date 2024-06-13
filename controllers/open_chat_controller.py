from .hl_controller import VLM_HL_Controller
import time
import copy
import random
from .util import append_to_message_hist_as_user, get_icl_data



class OpenChat_VLM_HL_Controller(VLM_HL_Controller):

    def __init__(self, latest_image_func, vlm_query_func,
                  hl_command_handle_func, opening_query_text,
                    sucessive_text, logdir="log", interval=3, turn=False, repeat_full_instruction=6, icl=None):
        super().__init__(latest_image_func, vlm_query_func, hl_command_handle_func,
                          opening_query_text, logdir, interval, turn)
        self.successive_text = sucessive_text
        self.repeat_full_instruction = repeat_full_instruction
        self.icl=icl

    def query(self):
        count = 0
        message_history = []
        while self.running:
            start_time = time.time() - self.reference_time

            while time.time() - self.last_query < self.interval:
                time.sleep(0.05)

            image = self.latest_image_func()

            if count == 0:
                if self.icl is not None:
                    append_to_message_hist_as_user(message_history, text=self.opening_query_text.split('<ICL>')[0])
                    append_to_message_hist_as_user(message_history, text="Now I will show you some examples.")
                    icl_data = get_icl_data(self.icl)
                    for img, action in icl_data:
                        append_to_message_hist_as_user(message_history, text=f"If you see the following, you should command {action}", image=img)
                    text = self.opening_query_text.split('<ICL>')[1]
                else:
                    text = self.opening_query_text.replace("<ICL>", "")
            else:
                if count % self.repeat_full_instruction == 0:
                    text = "As a reminder, y" + self.opening_query_text[1:].replace("<ICL>", "")
                else:  
                    text = self.successive_text

            if self.opening_query_text == "":
                result = [None, None]
                response = "random choice"
                result[0] = random.choice(["walk", "backward", "left", "right", "crawl", "climb"])
                result[1] = "small"
            else:
                response = self.vlm_query_func(image, text, message_history)
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
