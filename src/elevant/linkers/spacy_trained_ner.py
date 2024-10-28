from typing import Dict, Any, Optional, Tuple

import spacy

from elevant.linkers.abstract_entity_linker import AbstractEntityLinker
from elevant.models.entity_database import EntityDatabase
from elevant.models.entity_prediction import EntityPrediction

class SpacyTrainedNER(AbstractEntityLinker):
    def __init__(self, entity_db: EntityDatabase, config: Dict[str, Any]):
        self.entity_db = entity_db

        # Get config variables
        self.linker_identifier = "Spacy_trained_NER"

        self.model = spacy.load("/local/data-ssd/prangen/src/spacy-ner-training/finetuned-model/model-last/")
        # self.model.add_pipe("custom_sentencizer", before="parser")
        # self.model.add_pipe("ner_postprocessor", after="ner")

    def predict(self, text: str, doc=None, uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
            doc = self.model(text)
            predictions = {}
            for ent in doc.ents:
                span = (ent.start_char, ent.end_char)
                entity_id = ent.label_
                predictions[span] = EntityPrediction(span, entity_id, {entity_id})
            return predictions

    def has_entity(self, entity_id: str) -> bool:
        return True