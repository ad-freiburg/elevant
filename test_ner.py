import spacy

from src import settings
from src.ner_postprocessing import shorten_entities


if __name__ == "__main__":
    nlp = spacy.load(settings.LARGE_MODEL_NAME)
    nlp.add_pipe(shorten_entities, after="ner")
    while True:
        text = input("> ")
        doc = nlp(text)
        doc: spacy.language.Doc
        for ent in doc.ents:
            print(ent.text, ent.start_char, ent.end_char, ent.label_)
