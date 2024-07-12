from typing import Iterator, Tuple

from elevant.benchmark_readers.abstract_benchmark_reader import AbstractBenchmarkReader
from elevant.evaluation.groundtruth_label import GroundtruthLabel
from elevant.helpers.wikipedia_corpus import WikipediaCorpus
from elevant.models.article import Article
from elevant.models.entity_database import EntityDatabase
from elevant.utils.knowledge_base_mapper import UnknownEntity, KnowledgeBaseName, KnowledgeBaseMapper


def expand_span(text: str, span: Tuple[int, int]) -> Tuple[int, int]:
    begin, end = span
    while begin - 1 > 0 and text[begin - 1].isalpha():
        begin = begin - 1
    while end < len(text) and text[end].isalpha():
        end = end + 1
    return begin, end


class WikipediaReader(AbstractBenchmarkReader):
    def __init__(self, entity_db: EntityDatabase):
        self.entity_db = entity_db

    def article_iterator(self) -> Iterator[Article]:
        for article in WikipediaCorpus.development_articles():
            article.labels = []
            label_id_counter = 0
            for span, target in article.hyperlinks:
                span = expand_span(article.text, span)
                entity_id = KnowledgeBaseMapper.get_wikidata_qid(target, self.entity_db,
                                                                 kb_name=KnowledgeBaseName.WIKIPEDIA)
                gt_label = GroundtruthLabel(label_id_counter, span, entity_id, "Unknown")
                article.labels.append(gt_label)
                label_id_counter += 1
            yield article
