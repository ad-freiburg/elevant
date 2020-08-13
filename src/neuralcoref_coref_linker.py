from typing import Optional

import spacy
import neuralcoref
from spacy.tokens import Doc
from spacy.language import Language
from src import settings
from src.abstract_coref_linker import AbstractCorefLinker
from src.wikipedia_article import WikipediaArticle


class NeuralcorefCorefLinker(AbstractCorefLinker):
    def __init__(self,
                 model: Optional[Language] = None):
        if model is None:
            self.model = spacy.load(settings.LARGE_MODEL_NAME)
        else:
            self.model = model
        neuralcoref.add_to_pipe(self.model, max_dist=50, max_dist_match=100)

    def get_clusters(self, article: WikipediaArticle, doc: Optional[Doc] = None):
        if doc is None:
            doc = self.model(article.text)
        return doc._.coref_clusters
