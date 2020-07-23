from typing import Iterator, Tuple, List

from src.wikipedia_corpus import WikipediaCorpus
from src.entity_database_new import EntityDatabase
from src.conll_benchmark import conll_documents


class WikipediaExampleReader:
    def __init__(self, entity_db: EntityDatabase):
        self.entity_db = entity_db

    def iterate(self, n: int = -1) -> Iterator[Tuple[str, List[Tuple[Tuple[int, int], str]]]]:
        for article in WikipediaCorpus.development_articles(n):
            ground_truth = []
            for span, target in article.links:
                entity_id = self.entity_db.link2id(target)
                ground_truth.append((span, entity_id))
            yield article.text, ground_truth


class ConllExampleReader:
    def __init__(self, entity_db: EntityDatabase):
        self.entity_db = entity_db

    def iterate(self, n: int = -1) -> Iterator[Tuple[str, List[Tuple[Tuple[int, int], str]]]]:
        for i, document in enumerate(conll_documents()):
            if i == n:
                break
            ground_truth = []
            text_pos = -1
            inside = False
            entity_id = None
            mention_start = None
            for token in document.tokens:
                if inside and token.true_label != "I":
                    span = (mention_start, text_pos)
                    ground_truth.append((span, entity_id))
                    inside = False
                text_pos += 1  # space
                if token.true_label.startswith("Q"):
                    entity_id = token.true_label
                    mention_start = text_pos
                    inside = True
                text_pos += len(token.text)
            yield document.text(), ground_truth
