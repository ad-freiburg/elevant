from spacy.tokens import Span, Doc


def shorten_entities(doc: Doc) -> Doc:
    entities = list(doc.ents)
    for i, ent in enumerate(entities):
        if ent.text.startswith("the "):
            new_ent = Span(doc,
                           ent.start + 1,
                           ent.end,
                           label=ent.label_)
            entities[i] = new_ent
    doc.ents = tuple(entities)
    return doc
