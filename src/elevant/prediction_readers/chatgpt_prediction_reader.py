import re
from typing import Iterator, Tuple, Dict

from elevant.models.entity_database import EntityDatabase
from elevant.models.entity_prediction import EntityPrediction

import logging

from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper
from elevant.prediction_readers.abstract_prediction_reader import AbstractPredictionReader

logger = logging.getLogger("main." + __name__.split(".")[-1])


class ChatGPTPredictionReader(AbstractPredictionReader):
    def __init__(self, input_filepath: str, entity_db: EntityDatabase):
        self.entity_db = entity_db
        super().__init__(input_filepath, predictions_iterator_implemented=True)

    def predictions_iterator(self) -> Iterator[Dict[Tuple[int, int], EntityPrediction]]:
        """
        Yields predictions for each disambiguation result in the disambiguation
        file with one line per article.

        :return: iterator over dictionaries with predictions for each article
        """
        counter = 1
        predictions = {}
        doc_texts = []
        with open(self.input_filepath, "r", encoding="utf8") as file:
            for line in file:
                if line.startswith("SENTENCE"):
                    doc_text = re.sub(r"SENTENCE [0-9]+ ", "", line)
                    doc_texts.append(doc_text)
                    continue
                doc_id, mention, wikipedia_url = line.strip("\n").split("\t")
                doc_id = int(doc_id)
                if doc_id > counter:
                    yield predictions
                    predictions = {}
                    counter += 1
                doc_text = doc_texts[doc_id - 1]
                start = doc_text.find(mention)
                span = start, start + len(mention)
                entity_id = KnowledgeBaseMapper.get_wikidata_qid(wikipedia_url, self.entity_db, verbose=False)
                candidates = {entity_id}  # ChatGPT does not provide information about candidates
                predictions[span] = EntityPrediction(span, entity_id, candidates)

        yield predictions
