from spacy.tokens import Span, Doc
from spacy.language import Language

from elevant.models.entity_database import EntityDatabase


@Language.factory("ner_postprocessor")
def ner_postprocessor(nlp, name):
    return NERPostprocessor()


class NERPostprocessor:
    def __init__(self):
        self.entity_db = EntityDatabase()
        self.entity_db.load_name_to_entities()

    def __call__(self, doc: Doc) -> Doc:
        entities = list(doc.ents)
        for i, ent in enumerate(entities):
            if ent.text.startswith("the ") or \
                    (ent.text.startswith("The ") and
                     not self.entity_db.contains_entity_name(ent.text) and
                     self.entity_db.contains_entity_name(ent.text[4:])):
                new_ent = Span(doc,
                               ent.start + 1,
                               ent.end,
                               label=ent.label_)
                entities[i] = new_ent
        doc.ents = tuple(entities)
        return doc
