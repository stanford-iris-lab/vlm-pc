import time
from .hl_controller import VLM_HL_Controller
from .history_buffer import HistoryBuffer
import copy


class StaticMessageHist_VLM_HL_Controller(VLM_HL_Controller):
    def __init__(self,
                 latest_image_func,
                 vlm_query_func,
                 vlm_query_func_mult,
                 hl_command_handle_func,
                 logdir="log",
                 interval=3,
                 query_text=None,
                 query_text_multiple_img=None,
                 query_text_history=None,
                 batch_imgs=False,
                 turn=True
                 ):
        super(StaticMessageHist_VLM_HL_Controller, self).__init__(latest_image_func, vlm_query_func, hl_command_handle_func, 
                                                        logdir, interval, query_text, turn)
        self.message_history = []
        self.batch_imgs = batch_imgs
        self.history_buffer = HistoryBuffer()
        self.vlm_query_func_mult = vlm_query_func_mult
        self.turn = turn
        if batch_imgs:
            self.query_text_history = query_text_multiple_img
        else:
            self.query_text_history = query_text_history

    def get_last_n_words(self, text, n):
        words = text.replace("\n", " ").replace(".", "").split(" ")
        return words[-n:]

    def query(self):
        count = 0
        while self.running:
            start_time = time.time() - self.reference_time

            while time.time() - self.last_query < self.interval:
                time.sleep(0.05)

            image = self.latest_image_func()

            if count >= 1:
                # text = self.query_text_history + " Your heading is currently " + str(self.heading)
                text = self.query_text_history
                if not self.batch_imgs:
                    response = self.vlm_query_func(image, text, self.message_history)
                    result = self.get_last_n_words(response, 3)
                    record_message_hist = copy.deepcopy(self.message_history)
                else:
                    images = self.history_buffer.images[-3:]
                    images.append(image)
                    record_message_hist = []
                    response = self.vlm_query_func_mult(images, text, record_message_hist)
                    result = self.get_last_n_words(response, 3)
                result = result[1:]
                self.history_buffer.add_state(image)
            else:
                # text = self.query_text + " Your heading is currently " + str(self.heading)
                text = self.query_text
                response = self.vlm_query_func(image, text, self.message_history)
                record_message_hist = copy.deepcopy(self.message_history)
                result = self.get_last_n_words(response, 2)
                count += 1
                if count == 1:
                    self.history_buffer.add_state(image)

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
