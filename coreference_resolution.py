import spacy
import neuralcoref
from src import settings


if __name__ == "__main__":
    nlp = spacy.load(settings.LARGE_MODEL_NAME)
    neuralcoref.add_to_pipe(nlp)
    while True:
        text = input("> ")
        doc = nlp(text)
        for cluster in doc._.coref_clusters:
            print(cluster)
