from typing import Tuple
from spacy.tokens import Doc

import torch

from src.utils.offset_converter import OffsetConverter


class EmbeddingsExtractor:

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
