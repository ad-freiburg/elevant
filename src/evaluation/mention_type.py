from enum import Enum

from src.utils.pronoun_finder import PronounFinder


class MentionType(Enum):
    ENTITY_NAMED = "ENTITY_NAMED"
    ENTITY_OTHER = "ENTITY_OTHER"
    NOMINAL = "NOMINAL"
    PRONOMINAL = "PRONOMINAL"

    def is_coreference(self):
        return self != MentionType.ENTITY_NAMED and self != MentionType.ENTITY_OTHER


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


def is_named_entity(entity_name: str) -> bool:
    """
    Return true if the entity is of mention type "named" according to our definition:
    The entity name contains alphabetic characters and the first alphabetic
    character of the entity name is an uppercase character.
    """
    if entity_name != "Unknown":
        alpha_chars = [char for char in entity_name if char.isalpha()]
        # Check if first alphabetic character exists and is uppercase
        if len(alpha_chars) > 0 and alpha_chars[0].isupper():
            return True
    return False


def get_mention_type(mention: str, true_entity, predicted_entity) -> MentionType:
    if PronounFinder.is_pronoun(mention):
        return MentionType.PRONOMINAL
    elif is_nominal(mention):
        return MentionType.NOMINAL
    else:
        entity_name = true_entity.name if true_entity else predicted_entity.name
        if is_named_entity(entity_name):
            return MentionType.ENTITY_NAMED
        else:
            return MentionType.ENTITY_OTHER
