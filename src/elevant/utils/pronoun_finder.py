from typing import Set, Tuple
from spacy.tokens import Doc

from elevant.models.gender import Gender


class PronounFinder:
    pronoun_genders = {"i": Gender.UNKNOWN, "my": Gender.UNKNOWN, "me": Gender.UNKNOWN, "myself": Gender.UNKNOWN,
                       "mine": Gender.UNKNOWN,
                       "you": Gender.UNKNOWN, "your": Gender.UNKNOWN, "yourself": Gender.UNKNOWN,
                       "yours": Gender.UNKNOWN,
                       "he": Gender.MALE, "his": Gender.MALE, "him": Gender.MALE, "himself": Gender.MALE,
                       "she": Gender.FEMALE, "her": Gender.FEMALE, "herself": Gender.FEMALE, "hers": Gender.FEMALE,
                       "it": Gender.NEUTRAL, "its": Gender.NEUTRAL, "itself": Gender.NEUTRAL,
                       "we": Gender.UNKNOWN, "us": Gender.UNKNOWN, "our": Gender.UNKNOWN, "ourselves": Gender.UNKNOWN,
                       "ours": Gender.UNKNOWN,
                       "yourselves": Gender.UNKNOWN,
                       "they": Gender.UNKNOWN, "their": Gender.UNKNOWN, "them": Gender.UNKNOWN,
                       "themselves": Gender.UNKNOWN, "theirs": Gender.UNKNOWN}

    @classmethod
    def is_pronoun(cls, text: str) -> bool:
        # Do not match "US" or "IT" but match "I"
        return text.lower() in cls.pronoun_genders and (not text.isupper() or text.lower() == "i")

    @classmethod
    def find_pronouns(cls, doc: Doc) -> Set[Tuple[int, int]]:
        pronoun_spans = set()
        for tok in doc:
            if cls.is_pronoun(tok.text):
                span = (tok.idx, tok.idx + len(tok))
                pronoun_spans.add(span)
        return pronoun_spans

    @classmethod
    def is_first_person_singular(cls, text: str) -> bool:
        return text in ("I", "my", "me")
