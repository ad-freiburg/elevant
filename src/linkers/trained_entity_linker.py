from typing import Dict, Tuple, List, Optional

import spacy
from spacy.tokens import Doc
from spacy.language import Language
from spacy.vocab import Vocab
from spacy.kb import KnowledgeBase, Candidate

from src.linkers.abstract_entity_linker import AbstractEntityLinker
from src.models.entity_mention import EntityMention
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
        self.global_model = False
        if type(self.loaded_model) is dict:
            self.linker_model = self.loaded_model['model']
            self.prior = self.loaded_model.get('prior', False)
            self.global_model = self.loaded_model.get('global_model', False)
            print(f"use prior probs: {self.prior}")
            print(f"global model: {self.global_model}")
        else:
            self.linker_model = self.loaded_model
        self.linker_model.eval()

    def predict(self,
                text: str,
                doc: Optional[Doc] = None,
                uppercase: Optional[bool] = False,
                linked_entities: Optional[Dict[Tuple[int, int], EntityMention]] = None) -> Dict[Tuple[int, int], EntityPrediction]:
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
            x = self.get_model_input(span, candidates, doc, linked_entities)
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
                        doc: Doc,
                        linked_entities: Optional[Dict[Tuple[int, int], EntityMention]] = None) -> torch.Tensor:
        """
        Returns the input tensor for the trained model.
        """
        # Get sentence vector
        sentence_span = OffsetConverter.get_sentence(span[0], doc)
        sentence_span = sentence_span.start_char, sentence_span.end_char
        sentence_vector = EmbeddingsExtractor.get_span_embedding(sentence_span, doc)

        # Create empty x tensor
        if self.global_model:
            n_features = sentence_vector.size(1) * 3
            mean_linked_entity_vector = self.get_mean_linked_entity_vector(linked_entities)
        else:
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
            if self.global_model:
                input_vector = torch.cat((input_vector, mean_linked_entity_vector), dim=1)
            if self.prior:
                input_vector = torch.cat((input_vector, torch.Tensor([[cand.prior_prob]])), dim=1)
            x[i] = input_vector
        return x

    def get_mean_linked_entity_vector(self, linked_entities: Optional[Dict[Tuple[int, int], EntityMention]] = None):
        """
        Retrieve mean of vectors of entities that were already linked.
        """
        if linked_entities is None:
            # TODO: should later be a random vector as in train_own_linker.py
            return torch.zeros(1, self.kb.entity_vector_length)
        else:
            linked_entity_vectors = torch.zeros(len(linked_entities), self.kb.entity_vector_length)
        for i, entity_mention in enumerate(sorted(linked_entities.values())):
            entity_vector = torch.Tensor(self.kb.get_vector(entity_mention.entity_id))
            entity_vector = entity_vector.reshape((1, entity_vector.shape[0]))
            linked_entity_vectors[i] = entity_vector
        mean_linked_entity_vector = torch.mean(linked_entity_vectors, 0)
        mean_linked_entity_vector = mean_linked_entity_vector.reshape((1, mean_linked_entity_vector.shape[0]))
        return mean_linked_entity_vector

    def has_entity(self, entity_id: str) -> bool:
        return self.kb.contains_entity(entity_id)
