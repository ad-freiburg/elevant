from typing import Iterator, Tuple, Dict

from src.models.entity_database import EntityDatabase
from src.models.entity_prediction import EntityPrediction

import json


class NeuralELPredictionReader:

    def __init__(self, entity_db: EntityDatabase):
        self.entity_db = entity_db

    def _get_prediction_from_jsonl(self, string: str) -> Dict[Tuple[int, int], EntityPrediction]:
        """
        Extract entity predictions from a string that is the output of the
        Neural EL system by Gupta et al.
        """
        link_json = json.loads(string)
        links = link_json["predictions"]
        predictions = {}
        count = 0
        for link in links:
            label = link["label"]
            label = label.replace("_", " ")
            entity_id = self.entity_db.link2id(label)
            if not entity_id and label != "<unk wid>":
                print("\nNo mapping to Wikidata found for label '%s'" % label)
                count += 1
            start = link["start_char"]
            end = link["end_char"]
            span = (start, end)
            candidates = {entity_id}
            predictions[span] = EntityPrediction(span, entity_id, candidates)
        if count > 0:
            print("\n%d entity labels could not be matched to any Wikidata id." % count)
        return predictions

    def article_predictions_iterator(self, file_path: str) \
            -> Iterator[Dict[Tuple[int, int], EntityPrediction]]:
        """
        Yields predictions for each Neural EL disambiguation result in the
        given file, with one line per article.
        """
        with open(file_path, "r", encoding="utf8") as file:
            for line in file:
                predictions = self._get_prediction_from_jsonl(line)
                yield predictions
