from spacy.tokens import Doc
from spacy.language import Language


@Language.component("custom_sentencizer")
def set_custom_boundaries(doc: Doc) -> Doc:
    for i, token in enumerate(doc):
        if i - 1 >= 0 and "\n" in doc[i-1].text and not token.text.isspace():
            doc[i].is_sent_start = True
        elif token.text in ("(", ")"):
            doc[i].is_sent_start = False
    return doc
