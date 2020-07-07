import spacy

from src.wikipedia_article import Paragraph
from src.entity_mention import EntityMention


class SpacyNamedEntityRecognizer:
    IDENTIFIER = "SPACY"

    def __init__(self):
        self.nlp = spacy.load("en", disable=['parser', 'tagger', 'textcat'])

    def recognize(self, paragraph: Paragraph):
        #print([(paragraph.text[entity.span[0]:entity.span[1]], entity) for entity in paragraph.entity_mentions])
        doc = self.nlp(paragraph.text)
        new_entities = []
        for ent in doc.ents:
            #print(ent.text, ent.start_char, ent.end_char, ent.label_)
            span = (ent.start_char, ent.end_char)
            overlaps = paragraph.get_overlapping_entity(span)
            if overlaps is None:
                new_entities.append(EntityMention(span, recognized_by=self.IDENTIFIER))
        paragraph.entity_mentions = sorted(paragraph.entity_mentions + new_entities)
