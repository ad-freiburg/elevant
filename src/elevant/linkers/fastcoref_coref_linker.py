from typing import Optional, List

import spacy
from spacy.tokens import Doc
from spacy.language import Language
from elevant import settings
from elevant.linkers.abstract_coref_linker import AbstractCorefLinker
from elevant.models.coref_cluster import CorefCluster
from elevant.models.article import Article


class FastcorefCorefLinker(AbstractCorefLinker):
    def __init__(self,
                 model: Optional[Language] = None):
        if model is None:
            self.model = spacy.load(settings.LARGE_MODEL_NAME, disable=["lemmatizer"])
        else:
            self.model = model
        self.model.add_pipe("fastcoref")
        # The fastcoref module could also be further configured by replacing the line above with something like this:
        # self.model.add_pipe("fastcoref", config={'model_architecture': 'LingMessCoref', 'model_path': 'biu-nlp/lingmess-coref', 'device': 'cpu'})

    def get_clusters(self, article: Article, doc: Optional[Doc] = None) -> List[CorefCluster]:
        doc = self.model(article.text)

        coref_clusters = []
        for cluster in doc._.coref_clusters:
            main = cluster[0]  # Assume the first mention in the cluster is the main mention
            coref_cluster = CorefCluster(main, cluster)
            coref_clusters.append(coref_cluster)
        return coref_clusters
