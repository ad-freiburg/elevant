from typing import Tuple, List, Iterator

import os
import spacy
import pickle

from elevant import settings


class VectorGenerator:
    def __init__(self):
        self.model = spacy.load(settings.LARGE_MODEL_NAME)

    def get_vector(self, text: str):
        return self.model(text).vector


class VectorLoader:
    @staticmethod
    def iterate(vector_directory: str = settings.VECTORS_DIRECTORY) -> Iterator[Tuple[str, List[int]]]:
        for file in os.listdir(vector_directory):
            with open(vector_directory + file, "rb") as f:
                vectors = pickle.load(f)
            for entity_id, vector in vectors:
                yield entity_id, vector
