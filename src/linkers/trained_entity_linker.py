from typing import Dict, Tuple, List, Optional

import spacy
from spacy.tokens import Doc
from spacy.language import Language
from spacy.vocab import Vocab
from spacy.kb import KnowledgeBase, Candidate

from src.linkers.abstract_entity_linker import AbstractEntityLinker
from src.models.entity_prediction import EntityPrediction
from src.settings import NER_IGNORE_TAGS
from src.models.entity_database import EntityDatabase
from src.ner.ner_postprocessing import NERPostprocessor
from src.utils.dates import is_date
from src import settings

import torch

from src.utils.embeddings_extractor import EmbeddingsExtractor
from src.utils.offset_converter import OffsetConverter


class TrainedEntityLinker(AbstractEntityLinker):
    LINKER_IDENTIFIER = "VANILLA_LOCAL_LINKER"

    def __init__(self,
                 linker_model_name: str,
                 entity_db: EntityDatabase,
                 model: Optional[Language] = None,
                 kb_name: Optional[str] = None):
        if model is None:
            self.model = spacy.load(settings.LARGE_MODEL_NAME)
        else:
            self.model = model

        if not self.model.has_pipe("ner_postprocessor"):
            ner_postprocessor = NERPostprocessor(entity_db)
            self.model.add_pipe(ner_postprocessor, name="ner_postprocessor", after="ner")

        print("loading knowledge base...")
        if kb_name is None:
            vocab_path = settings.VOCAB_DIRECTORY
            kb_path = settings.KB_FILE
        else:
            load_path = settings.KB_DIRECTORY + kb_name + "/"
            vocab_path = load_path + "vocab"
            kb_path = load_path + "kb"
        vocab = Vocab().from_disk(vocab_path)
        self.kb = KnowledgeBase(vocab=vocab)
        self.kb.load_bulk(kb_path)

        print("loading trained entity linking model...")
        self.loaded_model = torch.load(linker_model_name)
        self.prior = False
        if type(self.loaded_model) is dict:
            self.linker_model = self.loaded_model['model']
            self.prior = self.loaded_model.get('prior', False)
            print(f"use prior probs: {self.prior}")
        else:
            self.linker_model = self.loaded_model
        self.linker_model.eval()

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
            span = (ent.start_char, ent.end_char)
            snippet = text[span[0]:span[1]]
            candidates = self.kb.get_candidates(snippet)
            if not candidates:
                continue
            x = self.get_model_input(span, candidates, doc)
            prediction = self.linker_model(x)
            entity_idx = torch.argmax(prediction).item()
            entity_id = candidates[entity_idx].entity_
            if uppercase and snippet.islower():
                continue
            if is_date(snippet):
                continue
            candidates = {cand.entity_ for cand in candidates}
            predictions[span] = EntityPrediction(span, entity_id, candidates)
        return predictions

    def get_model_input(self,
                        span: Tuple[int, int],
                        candidates: List[Candidate],
                        doc: Doc) -> torch.Tensor:
        """
        Returns the input tensor for the trained model.
        """
        # Get sentence vector
        sentence_span = OffsetConverter.get_sentence(span[0], doc)
        sentence_span = sentence_span.start_char, sentence_span.end_char
        sentence_vector = EmbeddingsExtractor.get_span_embedding(sentence_span, doc)

        # Create empty x tensor
        n_features = sentence_vector.size(1) * 2
        if self.prior:
            n_features += 1
        x = torch.empty(size=(len(candidates), n_features))

        # Compute probability for each candidate given sentence vector
        for i, cand in enumerate(candidates):
            # Get entity vector
            entity_vector = torch.Tensor(self.kb.get_vector(cand.entity_))
            entity_vector = entity_vector.reshape((1, entity_vector.shape[0]))
            input_vector = torch.cat((sentence_vector, entity_vector), dim=1)
            if self.prior:
                input_vector = torch.cat((input_vector, torch.Tensor([[cand.prior_prob]])), dim=1)
            x[i] = input_vector
        return x

    def has_entity(self, entity_id: str) -> bool:
        return self.kb.contains_entity(entity_id)
