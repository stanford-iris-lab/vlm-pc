from .hl_controller import VLM_HL_Controller
import time
from history_buffer import HistoryBuffer
import torch
import clip
from PIL import Image
import numpy as np
import copy

#TODO: this code was slightly broken before moved to this folder. Need to fix
class VLM_HL_Controller_Adaptive_History(VLM_HL_Controller):
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
        super(VLM_HL_Controller_Adaptive_History, self).__init__(latest_image_func, vlm_query_func, hl_command_handle_func, 
                                                                 logdir, interval, query_text, turn)

        self.batch_imgs = batch_imgs
        if batch_imgs:
            self.query_text_history = query_text_multiple_img
        else:
            self.query_text_history = query_text_history
        self.message_history = []
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load("ViT-B/32", device=device)
        self.history_buffer = HistoryBuffer()
        self.vlm_query_func_mult = vlm_query_func_mult
        self.turn = turn

    def encode_image_clip(self, image, device='cpu'):
        image = self.preprocess(Image.fromarray(image)).unsqueeze(0).to(device)
        with torch.no_grad():
            image_features = self.model.encode_image(image)
        return image_features

    def cosine_similarity(self, embedding1, embedding2):
        dot_product = np.dot(embedding1, embedding2.T)
        norm_embedding1 = np.linalg.norm(embedding1)
        norm_embedding2 = np.linalg.norm(embedding2)
        similarity = dot_product / (norm_embedding1 * norm_embedding2)
        return similarity.item()

    def most_frequent(self, lst):
        counter = Counter(lst)
        most_common_entry, most_common_frequency = counter.most_common(1)[0]
        return most_common_entry, most_common_frequency

    def get_last_n_words(self, text, n):
        words = text.replace("\n", " ").replace(".", "").split(" ")
        return words[-n:]

    def decide_action(self, new_embedding, previous_embedding):
        top_similar = self.history_buffer.get_top_similar(new_embedding)

        # Get most similar previous state
        most_similar_prev = self.history_buffer.most_similar_previous(previous_embedding)
        similarity_prev = cosine_similarity(previous_embedding, new_embedding)
        if similarity_prev > most_similar_prev:
            return None
        else:
            # If the new image is more similar to a previous state
            successful_actions = [self.history_buffer.actions[idx] for idx, sim in top_similar if
                                  self.history_buffer.outcomes[idx]]
            best_action, best_action_freq = self.most_frequent(successful_actions)
            if best_action_freq > len(top_similar) / 2:
                return action

    def query(self):
        count = 0
        while self.running:
            start_time = time.time() - self.reference_time

            while time.time() - self.last_query < self.interval:
                time.sleep(0.05)

            image = self.latest_image_func()
            current_embed = self.encode_image_clip(image)

            if count >= 1:
                # text = self.query_text_history + " Your heading is currently " + str(self.heading)
                text = self.query_text_history
                result = None
                if count >= 2:
                    result = self.decide_action(current_embed, prev_embed)
                    response = "using previous result."
                if result is None:
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
                    outcome = result[0]
                    result = result[1:]
                    self.history_buffer.add_outcome(True if outcome == "yes" else "no")
                self.history_buffer.add_state(image)
                self.history_buffer.add_embed(current_embed, result)
            else:
                # text = self.query_text + " Your heading is currently " + str(self.heading)
                text = self.query_text
                record_message_hist = []
                response = self.vlm_query_func(image, text, record_message_hist)
                result = self.get_last_n_words(response, 2)
                self.history_buffer.add_state(image)
                count += 1
                if count == 1:
                    self.history_buffer.add_embed(current_embed, result)
            prev_embed = current_embed
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


class VLM_HL_Controller_Text_History(VLM_HL_Controller):
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
                 turn=True,
                 ):
        super(VLM_HL_Controller_Text_History, self).__init__(latest_image_func, vlm_query_func, 
                                                             hl_command_handle_func, logdir, interval, query_text, turn)
        
        self.batch_imgs = batch_imgs
        self.history_buffer = HistoryBuffer()
        self.vlm_query_func_mult = vlm_query_func_mult
        if batch_imgs:
            self.query_text_history = query_text_multiple_img
        else:
            self.query_text_history = query_text_history

        self.summary = ""
        self.turn = turn

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
                if count >= 2:
                    text = "Here is a summary of what has happened so far: " + self.summary + "\n\n" + self.query_text_history
                else:
                    text = self.query_text_history
                text = text.replace("fill_action", " ".join(self.history_buffer.actions[-1]))
                if not self.batch_imgs:
                    images = [self.history_buffer.images[-1], image]
                    record_message_hist = []
                    response = self.vlm_query_func_mult(images, text, record_message_hist)
                    self.summary += "\n\n" + response
                    result = self.get_last_n_words(response, 3)
                else:
                    images = self.history_buffer.images[-3:]
                    images.append(image)
                    record_message_hist = []
                    response = self.vlm_query_func_mult(images, text, record_message_hist)
                    self.summary += "\n\n" + response
                    result = self.get_last_n_words(response, 3)
                result = result[1:]
                self.history_buffer.add_state(image)
                self.history_buffer.add_embed(None, result)
                count += 1
            else:
                # text = self.query_text + " Your heading is currently " + str(self.heading)
                text = self.query_text
                record_message_hist = []
                response = self.vlm_query_func(image, text, record_message_hist)
                result = self.get_last_n_words(response, 2)
                count += 1
                if count == 1:
                    self.history_buffer.add_state(image)
                    self.history_buffer.add_embed(None, result)

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
