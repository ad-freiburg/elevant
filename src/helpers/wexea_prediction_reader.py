from typing import Iterator, Tuple, Dict

from src.models.entity_database import EntityDatabase
from src.models.entity_prediction import EntityPrediction

import os
import re


class WexeaPredictionReader:
    _link_re = re.compile(r"\[\[([^\[].*?)\|(.*?)\|.*?[^\]]\]\]")

    def __init__(self, entity_db: EntityDatabase):
        self.entity_db = entity_db

    def _get_prediction_from_file(self, file_path: str) -> Dict[Tuple[int, int], EntityPrediction]:
        """
        Extract entity predictions from a file that is the output of the WEXEA
        entity annotator.
        """
        linked_file = open(file_path, "r", encoding='utf8')
        linked_text = ''.join(linked_file.readlines())
        text_position = 0
        text = ""
        predictions = dict()
        for link_match in WexeaPredictionReader._link_re.finditer(linked_text):
            link_target = link_match.group(1)
            link_text = link_match.group(2)
            text += linked_text[text_position:link_match.start()]
            link_start_pos = len(text)
            text += link_text
            link_end_pos = len(text)
            span = (link_start_pos, link_end_pos)
            text_position = link_match.end()
            entity_id = self.entity_db.link2id(link_target)
            candidates = {entity_id}
            predictions[span] = EntityPrediction(span, entity_id, candidates)
        text += linked_text[text_position:]
        return predictions

    def article_predictions_iterator(self, disambiguation_dir: str) \
            -> Iterator[Dict[Tuple[int, int], EntityPrediction]]:
        """
        Yields predictions for each WEXEA disambiguation result file in the
        given directory.
        """
        for file in sorted(os.listdir(disambiguation_dir)):
            file_path = os.path.join(disambiguation_dir, file)
            predictions = self._get_prediction_from_file(file_path)
            yield predictions
