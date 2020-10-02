from spacy.tokens import Doc


class CustomSentencizer:
    @staticmethod
    def set_custom_boundaries(doc) -> Doc:
        for i, token in enumerate(doc):
            if i - 1 >= 0 and "\n" in doc[i-1].text and not token.text.isspace():
                doc[i].is_sent_start = True
            elif token.text in ("(", ")"):
                doc[i].is_sent_start = False
        return doc
