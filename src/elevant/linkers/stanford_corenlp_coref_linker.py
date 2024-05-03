import logging
from typing import Optional, List

import stanza
from stanza.server import CoreNLPClient
from spacy.tokens import Doc

from elevant.linkers.abstract_coref_linker import AbstractCorefLinker
from elevant.models.coref_cluster import CorefCluster
from elevant.models.article import Article

logger = logging.getLogger("main." + __name__.split(".")[-1])


class StanfordCoreNLPCorefLinker(AbstractCorefLinker):
    def __init__(self):
        self.client = CoreNLPClient(properties={'annotators': "tokenize,ssplit,pos,lemma,ner,parse,coref",
                                                'coref.algorithm': 'neural'}, timeout=100000, memory='16G')

    def get_clusters(self, article: Article, doc: Optional[Doc] = None) -> List[CorefCluster]:
        coref_clusters = []
        try:
            annotations = self.client.annotate(article.text)
            chains = annotations.corefChain
            for index_chain, chain in enumerate(chains):
                mentions = []
                for m in chain.mention:
                    start_idx = annotations.sentence[m.sentenceIndex].token[m.beginIndex].beginChar
                    end_idx = annotations.sentence[m.sentenceIndex].token[m.endIndex - 1].endChar
                    mentions.append((start_idx, end_idx))
                mentions.sort()
                coref_cluster = CorefCluster(mentions[0], mentions)
                coref_clusters.append(coref_cluster)
        except stanza.server.client.TimeoutException as e:
            logger.error(e)
        return coref_clusters
