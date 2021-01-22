from typing import Tuple, Optional, List

from spacy.kb import KnowledgeBase
from spacy.tokens import Doc
from gensim.models.word2vec import Word2Vec

import torch

from src.models.entity_mention import EntityMention
from src.utils.offset_converter import OffsetConverter


class EmbeddingsExtractor:
    def __init__(self,
                 entity_vector_length: int,
                 kb: KnowledgeBase,
                 rdf2vec: Optional[Word2Vec] = None):
        self.entity_vector_length = entity_vector_length
        self.kb = kb
        self.rdf2vec = rdf2vec

    @staticmethod
    def get_span_embedding(span: Tuple[int, int], doc: Doc) -> torch.Tensor:
        """
        Get span embedding as average of tokens within the span (e.g. the sentence).
        """
        sentence_tokens = OffsetConverter.get_tokens_in_span(span, doc)
        embedding_size = len(sentence_tokens[0].vector)
        sentence_vector = torch.zeros(1, embedding_size)
        for tok in sentence_tokens:
            sentence_vector += tok.vector
        sentence_vector = sentence_vector / len(sentence_tokens)
        return sentence_vector

    def get_sentence_vector(self, span: Tuple[int, int], doc: Doc) -> torch.Tensor:
        """
        Retrieve the vector representing the sentence that contains the entity
        mention.
        """
        sentence_span = OffsetConverter.get_sentence(span[0], doc)
        sentence_span = sentence_span.start_char, sentence_span.end_char
        sentence_vector = EmbeddingsExtractor.get_span_embedding(sentence_span, doc)
        return sentence_vector

    def get_entity_vector(self, entity_id: str) -> torch.Tensor:
        """
        Return the vector of size (1, n_features) that represents the entity
        with the given id.
        """
        if self.rdf2vec:
            entity_url = "http://www.wikidata.org/entity/" + entity_id
            if entity_url in self.rdf2vec.wv.vocab:
                entity_vector = torch.Tensor(self.rdf2vec.wv.get_vector(entity_url))
                entity_vector = entity_vector.reshape((1, entity_vector.shape[0]))
            else:
                entity_vector = torch.FloatTensor(1, self.entity_vector_length).uniform_(-1, 1)
        else:
            entity_vector = torch.Tensor(self.kb.get_vector(entity_id))
            entity_vector = entity_vector.reshape((1, entity_vector.shape[0]))

            # Uncomment for fair comparison between rdf2vec and spacy entity vector:
            # entity_url = "http://www.wikidata.org/entity/" + entity_id
            # if entity_url not in self.rdf2vec.wv.vocab:
            #     entity_vector = torch.FloatTensor(1, entity_vector.shape[1]).uniform_(-1, 1)

        return entity_vector

    def get_global_entity_vector(self, linked_entities: List[str]) -> torch.Tensor:
        """
        Retrieve mean of vectors of entities that were already linked.
        """
        if not linked_entities:
            return torch.FloatTensor(1, self.entity_vector_length).uniform_(-1, 1)
        else:
            linked_entity_vectors = torch.zeros(len(linked_entities), self.entity_vector_length)
        for i, entity_id in enumerate(linked_entities):
            entity_vector = self.get_entity_vector(entity_id)
            linked_entity_vectors[i] = entity_vector
        global_entity_vector = torch.mean(linked_entity_vectors, 0)
        global_entity_vector = global_entity_vector.reshape((1, global_entity_vector.shape[0]))
        return global_entity_vector
