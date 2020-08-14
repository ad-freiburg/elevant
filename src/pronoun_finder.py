from typing import Set, Tuple
from spacy.tokens import Doc

from src.gender import Gender


class PronounFinder:
    pronouns = {"i": Gender.UNKNOWN, "my": Gender.UNKNOWN, "me": Gender.UNKNOWN, "you": Gender.UNKNOWN,
                "your": Gender.UNKNOWN, "he": Gender.MALE, "his": Gender.MALE, "him": Gender.MALE, "she": Gender.FEMALE,
                "her": Gender.FEMALE, "it": Gender.NEUTRAL, "its": Gender.NEUTRAL, "us": Gender.UNKNOWN,
                "our": Gender.UNKNOWN, "they": Gender.UNKNOWN, "their": Gender.UNKNOWN, "them": Gender.UNKNOWN}

    @classmethod
    def find_pronouns(cls, doc: Doc) -> Set[Tuple[int, int]]:
        pronoun_spans = set()
        for tok in doc:
            if tok.text.lower() in cls.pronouns and not tok.text.isupper():  # do not match "US"
                span = (tok.idx, tok.idx + len(tok))
                pronoun_spans.add(span)
        return pronoun_spans
