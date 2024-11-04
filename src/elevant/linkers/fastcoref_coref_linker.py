from typing import Optional, List

from spacy.tokens import Doc
from spacy.language import Language
from elevant.linkers.abstract_coref_linker import AbstractCorefLinker
from elevant.models.coref_cluster import CorefCluster
from elevant.models.article import Article
from fastcoref import FCoref


class FastcorefCorefLinker(AbstractCorefLinker):
    def __init__(self,
                 model: Optional[Language] = None):
        # Use native F-Coref instead of the spacy component, as the spacy component is significantly slower
        # (on Wiki-Fair v2.0 test set: 130s vs. 6s on GPU)
        self.model = FCoref(device='cuda:0')

    def get_clusters(self, article: Article, doc: Optional[Doc] = None) -> List[CorefCluster]:
        preds = self.model.predict(texts=[article.text])

        coref_clusters = []
        for cluster in preds[0].get_clusters(as_strings=False):
            main = cluster[0]  # Assume the first mention in the cluster is the main mention
            coref_cluster = CorefCluster(main, cluster)
            coref_clusters.append(coref_cluster)
        return coref_clusters
