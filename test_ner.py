import spacy

from src import settings
from src.ner.ner_postprocessing import NERPostprocessor
from src.models.entity_database import EntityDatabase


if __name__ == "__main__":
    entity_db = EntityDatabase()
    entity_db.load_entities_big()

    nlp = spacy.load(settings.LARGE_MODEL_NAME)
    ner_postprocessor = NERPostprocessor(entity_db)
    nlp.add_pipe(ner_postprocessor, after="ner")

    while True:
        text = input("> ")
        doc = nlp(text)
        doc: spacy.language.Doc
        for ent in doc.ents:
            print(ent.text, ent.start_char, ent.end_char, ent.label_)
