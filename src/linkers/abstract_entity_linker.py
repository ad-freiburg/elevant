import abc
from typing import Dict, Tuple, Optional

from spacy.tokens import Doc

from src.models.entity_mention import EntityMention
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

    def predict_globally(self,
                         text: str,
                         doc: Optional[Doc] = None,
                         uppercase: Optional[bool] = False,
                         linked_entities: Optional[Dict[Tuple[int, int], EntityMention]] = None) -> Dict[Tuple[int, int], EntityPrediction]:
        """
        Predict entities with regard to already linked entities in the article.
        If not supported by the entity linker, a local prediction is performed.
        """
        print("Global prediction is not supported for the selected linker. Performing local prediction.")
        return self.predict(text, doc, uppercase)

    @abc.abstractmethod
    def has_entity(self, entity_id: str) -> bool:
        raise NotImplementedError()

    def link_entities(self,
                      article: WikipediaArticle,
                      doc: Optional[Doc] = None,
                      uppercase: Optional[bool] = False,
                      globally: Optional[bool] = False):
        if globally:
            entity_predictions = self.predict_globally(article.text, doc=doc, uppercase=uppercase,
                                                       linked_entities=article.entity_mentions)
        else:
            entity_predictions = self.predict(article.text, doc=doc, uppercase=uppercase)

        article.link_entities(entity_predictions, self.NER_IDENTIFIER, self.LINKER_IDENTIFIER)
