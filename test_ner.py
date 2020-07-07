import spacy

from src import settings


if __name__ == "__main__":
    nlp = spacy.load(settings.LARGE_MODEL_NAME)
    while True:
        text = input("> ")
        doc = nlp(text)
        doc: spacy.language.Doc
        for ent in doc.ents:
            print(ent.text, ent.start_char, ent.end_char, ent.label_)
