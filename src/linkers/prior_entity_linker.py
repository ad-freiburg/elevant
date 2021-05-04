from typing import Optional, Dict, Tuple, List
from os.path import isfile

import spacy
from spacy.tokens import Doc
from spacy.vocab import Vocab
from spacy.kb import KnowledgeBase, Candidate

from src import settings
from src.settings import NER_IGNORE_TAGS
from src.linkers.abstract_entity_linker import AbstractEntityLinker
from src.models.entity_mention import EntityMention
from src.models.entity_prediction import EntityPrediction
from src.models.entity_database import EntityDatabase
from src.ner.ner_postprocessing import NERPostprocessor
from src.utils.dates import is_date


class PriorEntityLinker(AbstractEntityLinker):
    LINKER_IDENTIFIER = "BERT_LINKER"

    def __init__(self,
                 entity_db: EntityDatabase):
        self.model = spacy.load(settings.LARGE_MODEL_NAME)

        if not self.model.has_pipe("ner_postprocessor"):
            ner_postprocessor = NERPostprocessor(entity_db)
            self.model.add_pipe(ner_postprocessor, name="ner_postprocessor", after="ner")

        print("Loading knowledge base ...")
        vocab_path = settings.VOCAB_DIRECTORY
        kb_path = settings.KB_FILE
        vocab = Vocab().from_disk(vocab_path)
        self.kb = KnowledgeBase(vocab=vocab)
        self.kb.load_bulk(kb_path)
        print("Ready.")

    def predict(self,
                text: str,
                doc: Optional[Doc] = None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        if doc is None:
            doc = self.model(text)
        predictions = {}

        for ent in doc.ents:
            if ent.label_ in NER_IGNORE_TAGS:
                continue
            # The token span of the mention
            token_span = (ent.start, ent.end)
            snippet = ent.text
            if uppercase and snippet.islower():
                continue
            if is_date(snippet):
                continue
            candidates = self.kb.get_candidates(snippet)
            if not candidates:
                continue

            prediction = candidates[0]
            for candidate in candidates[1:]:
                if candidate.prior_prob > prediction.prior_prob:
                    prediction = candidate

            entity_id = prediction.entity_
            candidates = {cand.entity_ for cand in candidates}
            span = (ent.start_char, ent.end_char)

            predictions[span] = EntityPrediction(span, entity_id, candidates)

        return predictions

    def has_entity(self, entity_id: str) -> bool:
        return self.kb.contains_entity(entity_id)
