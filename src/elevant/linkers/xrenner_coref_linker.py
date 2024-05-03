from typing import Optional, Dict, Tuple, List

import warnings
import re
from collections import defaultdict
from numpy import VisibleDeprecationWarning
from xrenner import Xrenner
from xrenner.modules.get_models import check_models
from spacy.tokens import Doc
from spacy_conll import init_parser

from elevant.linkers.abstract_coref_linker import AbstractCorefLinker
from elevant.models.coref_cluster import CorefCluster
from elevant.models.article import Article


warnings.filterwarnings("ignore", category=VisibleDeprecationWarning)


class XrennerCorefLinker(AbstractCorefLinker):
    """
    Xrenner has a dependency conflict with the REL linker:
        radboud-el 0.0.1 depends on flair>=0.11
        xrenner 2.2.0.0 depends on flair==0.6.1
    Therefore Xrenner can't be used out of the box anymore.
    """
    def __init__(self):
        self.model = init_parser("en_core_web_lg", "spacy", parser_opts={}, include_headers=True)
        check_models()
        self.xrenner = Xrenner()

    def get_clusters(self, article: Article, doc: Optional[Doc] = None) -> List[CorefCluster]:
        # Replace rare non-breaking-spaces with normal spaces since xrenner can't handle them
        text = article.text.replace(" ", " ")
        doc = self.model(text)
        conll = doc._.conll_str
        processed_conll = self.fix_conll_newlines(conll)
        onto_results = self.xrenner.analyze(processed_conll, "conll")
        clusters = self.build_clusters_from_onto_string(onto_results, doc)
        coref_clusters = []
        for _, span_list in clusters.items():
            coref_cluster = CorefCluster(span_list[0], span_list)
            coref_clusters.append(coref_cluster)
        return coref_clusters

    @staticmethod
    def fix_conll_newlines(conll_string: str) -> str:
        """Denote newline characters with <br>, otherwise, the conll data is
        malformed and xrenner can't handle it.
        """
        processed_conll = ""
        newline = False
        for line in conll_string.split("\n"):
            if line:
                if len(line.split("\t")) == 2:
                    newline = True
                    processed_conll += line + "<br>"
                else:
                    processed_conll += line + "\n"
                    newline = False
            elif newline:
                processed_conll += "<br>"
            else:
                processed_conll += "\n"
        return processed_conll

    @staticmethod
    def build_clusters_from_onto_string(onto_string: str, doc: Doc) -> Dict[str, List[Tuple[int, int]]]:
        """Parse ONTO coreference result string and build coreference clusters.
        """
        clusters = defaultdict(list)
        curr_corefs = dict()
        for line in onto_string.split("\n"):
            if line.startswith("#") or not line:
                continue

            idx, text, coref = line.split("\t")
            idx = int(idx)
            coref = coref.strip()

            if coref == "_":
                continue

            coref_starts = re.finditer(r"\((\d+)(?!\)\d])", coref)
            coref_ends = re.finditer(r"(?!\(\d)(\d+)\)", coref)

            start = doc[idx].idx
            end_idx = idx
            if "<br>" in text:
                end_idx = idx - 1
            end = doc[end_idx].idx + len(doc[end_idx].text)

            for match in coref_starts:
                curr_corefs[match.group(1)] = start

            for match in coref_ends:
                coref_id = match.group(1)
                start = curr_corefs[coref_id]
                del curr_corefs[coref_id]
                clusters[coref_id].append((start, end))
        return clusters
