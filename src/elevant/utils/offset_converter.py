from typing import List, Tuple, Optional

from spacy.tokens import Doc, Token, Span


class OffsetConverter:
    @staticmethod
    def get_token_idx(offset: int, doc: Doc, left: Optional[int] = None, right: Optional[int] = None) -> int:
        """
        Performs binary search on the list of token indices in the doc to find
        the token that contains the character at position offset. If the offset
        is not found, returns None.
        """
        if left is None:
            left = 0
        if right is None:
            right = len(doc) - 1
        while left <= right:
            mid = (right + left) // 2
            # If the index (thus the -1 !) of the last character of the current token is
            # smaller than the offset we're looking for, search in right part.
            if doc[mid].idx + len(doc[mid].text) - 1 < offset:
                left = mid + 1
            # If the index of the first character of the current token is
            # greater than the offset we're looking for, search in left part.
            # Additionally, check if the offset is in the gap between the
            # current token and the previous one
            elif doc[mid].idx > offset and (mid-1 < 0 or doc[mid-1].idx + len(doc[mid-1].text) > offset):
                right = mid - 1
            # Offset is present at mid
            else:
                return mid

    @staticmethod
    def get_token(offset: int, doc: Doc) -> Token:
        """
        Get the token that contains the character at position offset.
        """
        token_index = OffsetConverter.get_token_idx(offset, doc)
        if token_index is not None:
            return doc[token_index]

    @staticmethod
    def get_tokens_in_span(span: Tuple[int, int], doc: Doc) -> List[Token]:
        """
        Get all tokens that are fully contained in the given span.
        """
        # Get the index of the token that contains the start of the span
        left_i = OffsetConverter.get_token_idx(span[0], doc)
        # We only want fully contained tokens, i.e. no tokens that start before the span starts
        left_i = left_i if doc[left_i].idx >= span[0] else left_i + 1
        # Get the index of the token that contains the end of the span
        right_i = OffsetConverter.get_token_idx(span[1] - 1, doc)  # -1 because right end of span is exclusive
        if right_i is None:
            return doc[left_i:]
        # We only want fully contained tokens, i.e. no tokens that end after the span ends
        right_i = right_i if doc[right_i].idx + len(doc[right_i].text) <= span[1] else right_i - 1
        # Get all contained tokens
        tokens = doc[left_i:right_i + 1]  # + 1 because the token at right_i is fully contained in the span
        return tokens

    @staticmethod
    def get_sentence(offset: int, doc: Doc) -> Span:
        """
        Get the span of the sentence that contains the character at position
        offset. Binary search is not possible here, since doc.sents is an
        iterator, so getting the length of doc.sents is in O(n).
        """
        for i, sent in enumerate(doc.sents):
            if sent.end_char >= offset:
                return sent

    @staticmethod
    def get_token_idx_in_sent(offset: int, doc: Doc) -> int:
        """
        For the token that contains the character at position offset, get the
        token index within the sentence that contains it. I.e. if it's the
        first token in the sentence return 0.
        """
        token = OffsetConverter.get_token(offset, doc)
        if token:
            for i, tok in enumerate(token.sent):
                if tok.idx >= offset:
                    return i
