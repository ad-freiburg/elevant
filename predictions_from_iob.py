import sys

from src.models.conll_benchmark import conll_documents
from src.helpers.conll_iob_prediction_reader import ConllIobPredictionReader


if __name__ == "__main__":
    path = sys.argv[1]
    documents = conll_documents()
    prediction_iterator = ConllIobPredictionReader.document_predictions_iterator(path)
    for document, predictions in zip(documents, prediction_iterator):
        text = document.text()
        print(text)
        for span in sorted(predictions):
            prediction = predictions[span]
            snippet = text[span[0]:span[1]]
            print(span, snippet, prediction.entity_id)
