from typing import List, Tuple

from spacy.tokens import Doc, Token, Span


class OffsetConverter:
    @staticmethod
    def get_token(offset: int, doc: Doc) -> Token:
        for token in doc:
            if offset < token.idx + len(token.text):
                return token

    @staticmethod
    def get_sentence(offset: int, doc: Doc) -> Span:
        for i, sent in enumerate(doc.sents):
            if sent.end_char >= offset:
                return sent

    @staticmethod
    def get_sentence_idx(offset: int, doc: Doc) -> int:
        for i, sent in enumerate(doc.sents):
            if sent.end_char >= offset:
                return i

    @staticmethod
    def get_containing_sents(offset: int, doc: Doc, sents_before=4) -> List[Span]:
        containing_sents = []
        for i, sent in enumerate(doc.sents):
            if len(containing_sents) > sents_before:
                containing_sents.pop(0)
            containing_sents.append(sent)
            if sent.end_char > offset:
                return containing_sents

    @staticmethod
    def get_tokens_in_span(span: Tuple[int, int], doc: Doc) -> List[Token]:
        tokens = []
        for token in doc:
            if token.idx >= span[0] and token.idx + len(token.text) <= span[1]:
                tokens.append(token)
        return tokens

    @staticmethod
    def get_token_idx(offset: int, doc: Doc) -> Token:
        for i, token in enumerate(doc):
            if offset < token.idx + len(token.text):
                return i

    @staticmethod
    def get_token_idx_in_sent(offset: int, doc: Doc) -> int:
        for sent in doc.sents:
            for i, tok in enumerate(sent):
                if tok.idx >= offset:
                    return i
