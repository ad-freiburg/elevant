from typing import Optional, List

import spacy
import neuralcoref
from spacy.tokens import Doc
from spacy.language import Language
from src import settings
from src.linkers.abstract_coref_linker import AbstractCorefLinker
from src.models.coref_cluster import CorefCluster
from src.models.article import Article


class NeuralcorefCorefLinker(AbstractCorefLinker):
    def __init__(self,
                 model: Optional[Language] = None):
        if model is None:
            self.model = spacy.load(settings.LARGE_MODEL_NAME)
        else:
            self.model = model
        neuralcoref.add_to_pipe(self.model, max_dist=50, max_dist_match=100)

    def get_clusters(self, article: Article, doc: Optional[Doc] = None) -> List[CorefCluster]:
        doc = self.model(article.text)

        coref_clusters = []
        for cluster in doc._.coref_clusters:
            mentions = [(m.start_char, m.end_char) for m in cluster.mentions]
            main = cluster.main.start_char, cluster.main.end_char
            coref_cluster = CorefCluster(main, mentions)
            coref_clusters.append(coref_cluster)
        return coref_clusters
