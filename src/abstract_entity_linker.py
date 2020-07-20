import abc
from typing import Dict, Tuple, Optional

from spacy.tokens import Doc

from src.entity_prediction import EntityPrediction
from src.wikipedia_article import WikipediaArticle
from src.entity_mention import EntityMention


class AbstractEntityLinker(abc.ABC):
    NER_IDENTIFIER = "NER"

    LINKER_IDENTIFIER = None

    @abc.abstractmethod
    def predict(self,
                text: str,
                doc: Optional[Doc] = None) -> Dict[Tuple[int, int], EntityPrediction]:
        raise NotImplementedError()

    @abc.abstractmethod
    def has_entity(self, entity_id: str) -> bool:
        raise NotImplementedError()

    def link_entities(self,
                      article: WikipediaArticle,
                      doc: Optional[Doc] = None):
        entity_predictions = self.predict(article.text, doc=doc)
        new_entity_mentions = []
        for span in entity_predictions:
            if not article.overlaps_entity_mention(span):
                prediction = entity_predictions[span]
                if prediction.entity_id is not None:
                    entity_mention = EntityMention(span,
                                                   recognized_by=self.NER_IDENTIFIER,
                                                   entity_id=prediction.entity_id,
                                                   linked_by=self.LINKER_IDENTIFIER)
                    new_entity_mentions.append(entity_mention)
        article.add_entity_mentions(new_entity_mentions)
