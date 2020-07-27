from typing import List, Iterator, Dict, Tuple

from src.conll_benchmark import ConllDocument
from src.entity_prediction import EntityPrediction


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


class ConllIobPredictionReader:
    @staticmethod
    def document_predictions_iterator(prediction_file_path: str) -> Iterator[Dict[Tuple[int, int], EntityPrediction]]:
        next_id = 1
        for line in open(prediction_file_path):
            document = ConllDocument(line[:-1])
            if int(document.id) > next_id:
                yield {}
                next_id += 1
            predictions = get_predictions(document)
            predictions = {prediction.span: prediction for prediction in predictions}
            yield predictions
            next_id += 1
