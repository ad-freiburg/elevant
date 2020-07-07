import abc
from typing import Dict, Tuple, Optional

from spacy.tokens import Doc

from src.entity_prediction import EntityPrediction
from src.paragraph import Paragraph
from src.entity_mention import EntityMention


class AbstractEntityLinker(abc.ABC):
    NER_IDENTIFIER = "NER"

    LINKER_IDENTIFIER = None

    @abc.abstractmethod
    def predict(self,
                text: str,
                doc: Optional[Doc] = None) -> Dict[Tuple[int, int], EntityPrediction]:
        raise NotImplementedError()

    def link_entities(self,
                      paragraph: Paragraph,
                      doc: Optional[Doc] = None):
        entity_predictions = self.predict(paragraph.text, doc=doc)
        new_entities = []
        for span in entity_predictions:
            if paragraph.overlaps_entity(span):
                continue
            prediction = entity_predictions[span]
            if prediction.entity_id is not None:
                entity_mention = EntityMention(span, recognized_by=self.NER_IDENTIFIER, entity_id=prediction.entity_id,
                                               linked_by=self.LINKER_IDENTIFIER)
                new_entities.append(entity_mention)
        paragraph.add_entity_mentions(new_entities)
