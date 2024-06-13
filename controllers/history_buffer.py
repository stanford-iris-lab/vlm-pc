import numpy as np

class HistoryBuffer:
    def __init__(self):
        self.embeddings = []
        self.actions = []
        self.outcomes = []
        self.images = []

    def add_state(self, image):
        self.images.append(image)

    def add_embed(self, embedding, action):
        self.embeddings.append(embedding)
        self.actions.append(action)

    def add_outcome(self, outcome):
        self.outcomes.append(outcome)

    def get_top_similar(self, new_embedding, top_n=3):
        similarities = [cosine_similarity(embedding, new_embedding) for embedding in self.embeddings[:-1]]
        top_indices = np.argsort(similarities)[-top_n:][::-1]
        return [(index, similarities[index]) for index in top_indices]

    def most_similar_previous(self, new_embedding):
        similarities = [cosine_similarity(embedding, new_embedding) for embedding in self.embeddings[:-1]]
        return max(similarities)