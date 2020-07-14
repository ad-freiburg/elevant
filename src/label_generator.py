from typing import Iterator, Tuple, List, Dict

from spacy.kb import KnowledgeBase
from spacy.language import Language, Doc

from src import settings


class LabelGenerator:
    DISABLE_TRAINING = ["entity_linker", "tagger"]

    def __init__(self, model: Language, kb: KnowledgeBase):
        self.model = model
        self.kb = kb

    def _labeled_examples(self,
                          file_name: str,
                          disable: List[str]) -> Iterator[Tuple[Doc, Dict[Tuple[int, int], str]]]:
        for line in open(settings.DATA_DIRECTORY + file_name):
            paragraph = paragraph_from_json(line)
            link_dict = {}
            for entity_mention in paragraph.entity_mentions:
                entity_id = entity_mention.entity_id
                if entity_mention.is_linked() and self.kb.contains_entity(entity_id):
                    begin, end = entity_mention.span
                    snippet = paragraph.text[begin:end]
                    candidate_entities = [candidate.entity_ for candidate in self.kb.get_candidates(snippet)]
                    if entity_id in candidate_entities:
                        link_dict[entity_mention.span] = {candidate_id: 1.0 if candidate_id == entity_id else 0.0
                                                          for candidate_id in candidate_entities}
            if len(link_dict) > 0:
                with self.model.disable_pipes(disable):
                    doc = self.model(paragraph.text)

                doc_entity_spans = {(e.start_char, e.end_char) for e in doc.ents}
                link_dict = {span: link_dict[span] for span in link_dict if span in doc_entity_spans}

                if len(link_dict) > 0:
                    labels = {"links": link_dict}
                    yield doc, labels

    def training_examples(self):
        return self._labeled_examples("training.txt", self.DISABLE_TRAINING)

    def development_examples(self):
        return self._labeled_examples("development.txt", [])

    def test_examples(self):
        return self._labeled_examples("test.txt", [])
