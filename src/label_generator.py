from typing import Iterator, Tuple, Dict

from spacy.kb import KnowledgeBase
from spacy.language import Language, Doc

from src.wikipedia_corpus import WikipediaCorpus


class LabelGenerator:
    DISABLE_TRAINING = ["entity_linker", "tagger"]

    def __init__(self,
                 model: Language,
                 kb: KnowledgeBase,
                 mapping: Dict[str, str]):
        self.model = model
        self.kb = kb
        self.mapping = mapping

    def training_examples(self, n: int = -1) -> Iterator[Tuple[Doc, Dict[str, Dict[Tuple[int, int], str]]]]:
        for article in WikipediaCorpus.training_articles(n):
            link_dict = {}
            for span, link_target in article.links:
                if link_target in self.mapping:
                    entity_id = self.mapping[link_target]
                    if self.kb.contains_entity(entity_id):
                        begin, end = span
                        snippet = article.text[begin:end]
                        candidate_entities = [candidate.entity_ for candidate in self.kb.get_candidates(snippet)]
                        if entity_id in candidate_entities:
                            link_dict[span] = {candidate_id: 1.0 if candidate_id == entity_id else 0.0
                                               for candidate_id in candidate_entities}
            if len(link_dict) > 0:
                with self.model.disable_pipes(LabelGenerator.DISABLE_TRAINING):
                    doc = self.model(article.text)

                doc_entity_spans = {(e.start_char, e.end_char) for e in doc.ents}
                link_dict = {span: link_dict[span] for span in link_dict if span in doc_entity_spans}

                if len(link_dict) > 0:
                    labels = {"links": link_dict}
                    yield doc, labels
