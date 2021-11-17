import logging
from typing import Dict, Tuple, List, Optional

import spacy
from spacy.tokens import Doc
from spacy.language import Language
from spacy.vocab import Vocab
from spacy.kb import KnowledgeBase, Candidate

from src.linkers.abstract_entity_linker import AbstractEntityLinker
from src.models.entity_mention import EntityMention
from src.models.entity_prediction import EntityPrediction
from src.models.neural_net import NeuralNet
from src.settings import NER_IGNORE_TAGS
from src.models.entity_database import EntityDatabase
from src.ner.ner_postprocessing import NERPostprocessor
from src.utils.dates import is_date
from src.utils.embeddings_extractor import EmbeddingsExtractor
from src import settings

import torch
import gensim

logger = logging.getLogger("main." + __name__.split(".")[-1])


class TrainedEntityLinker(AbstractEntityLinker):
    LINKER_IDENTIFIER = "VANILLA_LOCAL_LINKER"

    def __init__(self,
                 linker_model: NeuralNet,
                 entity_db: EntityDatabase,
                 model: Optional[Language] = None,
                 kb_name: Optional[str] = None,
                 prior: Optional[bool] = False,
                 global_model: Optional[bool] = False,
                 rdf2vec: Optional[bool] = False):
        if model is None:
            self.model = spacy.load(settings.LARGE_MODEL_NAME)
        else:
            self.model = model

        if not self.model.has_pipe("ner_postprocessor"):
            ner_postprocessor = NERPostprocessor(entity_db)
            self.model.add_pipe(ner_postprocessor, name="ner_postprocessor", after="ner")

        logger.info("Loading knowledge base...")
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

        self.linker_model = linker_model
        self.linker_model.eval()

        self.prior = prior
        self.global_model = global_model
        logger.info(f"Use prior probabilities: {prior}")
        logger.info(f"Use a global model: {global_model}")
        logger.info(f"Use RDF2Vec as entity vectors: {rdf2vec}")

        # Load rdf2vec model
        rdf2vec_model = None
        if rdf2vec:
            logger.info("Loading RDF2Vec model...")
            rdf2vec_model = gensim.models.Word2Vec.load(settings.RDF2VEC_MODEL_PATH, mmap='r')

        # Determine the dimensionality of an entity vector
        self.entity_vector_length = rdf2vec_model.wv.vector_size if rdf2vec else self.kb.entity_vector_length

        self.embedding_extractor = EmbeddingsExtractor(self.entity_vector_length, self.kb, rdf2vec_model)

    def predict(self,
                text: str,
                doc: Optional[Doc] = None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        return self.predict_globally(text, doc, uppercase)

    def predict_globally(self,
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
        sentence_vector = self.embedding_extractor.get_sentence_vector(span, doc)

        # Create empty input tensor
        n_features = self.determine_n_features(sentence_vector.shape[1])
        x = torch.empty(size=(len(candidates), n_features))

        if self.global_model:
            if linked_entities:
                linked_entity_ids = [em.entity_id for span, em in sorted(linked_entities.items())]
            else:
                linked_entity_ids = []
            global_entity_vector = self.embedding_extractor.get_global_entity_vector(linked_entity_ids)

        # Build input data
        for i, cand in enumerate(candidates):
            entity_vector = self.embedding_extractor.get_entity_vector(cand.entity_)

            input_vector = torch.cat((sentence_vector, entity_vector), dim=1)
            if self.global_model:
                input_vector = torch.cat((input_vector, global_entity_vector), dim=1)
            if self.prior:
                input_vector = torch.cat((input_vector, torch.Tensor([[cand.prior_prob]])), dim=1)
            x[i] = input_vector
        return x

    def determine_n_features(self, token_vector_length: int) -> int:
        """
        Determine the number of features of the input vector.
        """
        if self.global_model:
            # Vector of candidate entity, mean vector of already linked entities, sentence vector
            n_features = self.entity_vector_length * 2 + token_vector_length
        else:
            # Vector of candidate entity, sentence vector
            n_features = self.entity_vector_length + token_vector_length

        if self.prior:
            n_features += 1
        return n_features

    def has_entity(self, entity_id: str) -> bool:
        return self.kb.contains_entity(entity_id)
