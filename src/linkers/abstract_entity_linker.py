import abc
from typing import Dict, Tuple, Optional

from spacy.tokens import Doc

from src.models.entity_prediction import EntityPrediction
from src.models.wikipedia_article import WikipediaArticle


class AbstractEntityLinker(abc.ABC):
    NER_IDENTIFIER = "NER"
    LINKER_IDENTIFIER = None

    @abc.abstractmethod
    def predict(self,
                text: str,
                doc: Optional[Doc] = None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        raise NotImplementedError()

    @abc.abstractmethod
    def has_entity(self, entity_id: str) -> bool:
        raise NotImplementedError()

    def link_entities(self,
                      article: WikipediaArticle,
                      doc: Optional[Doc] = None,
                      uppercase: Optional[bool] = False):
        entity_predictions = self.predict(article.text, doc=doc, uppercase=uppercase)
        article.link_entities(entity_predictions, self.NER_IDENTIFIER, self.LINKER_IDENTIFIER)
