from enum import Enum

from src.utils.pronoun_finder import PronounFinder


class MentionType(Enum):
    NAMED = "NAMED"
    NOMINAL = "NOMINAL"
    PRONOMINAL = "PRONOMINAL"

    def is_coreference(self):
        return self != MentionType.NAMED


_COREF_PREFIXES = ("the ", "that ", "this ", "that ", "these ", "those ")
_COREF_PREFIXES_POSSESSIVE = ("my ", "your ", "his ", "her ", "its ", "our ", "their ")


def is_coreference(mention: str) -> bool:
    return is_pronominal(mention) or is_nominal(mention)


def is_pronominal(mention: str) -> bool:
    return PronounFinder.is_pronoun(mention)


def is_nominal(mention: str) -> bool:
    lower = mention.lower()
    for prefix in _COREF_PREFIXES + _COREF_PREFIXES_POSSESSIVE:
        # Note: not isupper() is not the same as lower(). For "2" the former is True, but the latter is False.
        if (lower.startswith(prefix)) and len(mention) > len(prefix) and not mention[len(prefix)].isupper():
            return True
    return False


def get_mention_type(mention: str) -> MentionType:
    if PronounFinder.is_pronoun(mention):
        return MentionType.PRONOMINAL
    elif is_nominal(mention):
        return MentionType.NOMINAL
    else:
        return MentionType.NAMED
