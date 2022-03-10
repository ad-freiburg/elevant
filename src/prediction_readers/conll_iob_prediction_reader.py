from typing import List, Iterator, Dict, Tuple

from src.models.conll_benchmark import ConllDocument
from src.models.entity_prediction import EntityPrediction
from src.prediction_readers.abstract_prediction_reader import AbstractPredictionReader


def get_predictions(document: ConllDocument) -> List[EntityPrediction]:
    pos = 0
    inside = False
    prediction_start = None
    entity_id = None
    predictions = []
    for i, token in enumerate(document.tokens):
        if inside and token.predicted_label != "I":
            span = (prediction_start, pos)
            predictions.append(EntityPrediction(span, entity_id, candidates={entity_id}))
            inside = False
        if i > 0:
            pos += 1
        if token.predicted_label.startswith("Q") or token.predicted_label.startswith("B"):
            entity_id = token.predicted_label if token.predicted_label.startswith("Q") else None
            prediction_start = pos
            inside = True
        pos += len(token.text)
    return predictions


class ConllIobPredictionReader(AbstractPredictionReader):
    def __init__(self, input_filepath: str):
        super().__init__(input_filepath, predictions_iterator_implemented=True)

    def predictions_iterator(self) -> Iterator[Dict[Tuple[int, int], EntityPrediction]]:
        """
        Yields predictions for each article.

        :return: iterator over dictionaries with predictions for each article
        """
        next_id = 1
        for line in open(self.input_filepath):
            document = ConllDocument(line[:-1])
            if int(document.id) > next_id:
                yield {}
                next_id += 1
            predictions = get_predictions(document)
            predictions = {prediction.span: prediction for prediction in predictions}
            yield predictions
            next_id += 1
