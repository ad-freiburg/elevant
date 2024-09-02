from elevant.evaluation.mention_type import is_non_named_entity


def convert_to_filename(string: str):
    """
    Return lowercased version of the given string with non-alphanumerical
    characters replaced by underscore (except for "-").
    """
    return "".join(c if c.isalnum() or c == "-" else "_" for c in string.lower())


def compute_num_words(doc):
    num_words = 0
    for tok in doc:
        if not tok.is_punct and not tok.is_space:
            num_words += 1
    return num_words


def compute_lowercase_words(doc):
    num_words = 0
    for tok in doc:
        if not tok.is_punct and not tok.is_space and is_non_named_entity(tok.text):
            num_words += 1
    return num_words


def compute_no_lowercase_words(doc):
    num_words = 0
    for tok in doc:
        if not tok.is_punct and not tok.is_space and not is_non_named_entity(tok.text):
            num_words += 1
    return num_words
