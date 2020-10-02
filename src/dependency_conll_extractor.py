from spacy.tokens import Span


class DependencyConllExtractor:
    @staticmethod
    def to_conll_7(sent: Span) -> str:
        """Puts a SpaCy-parse into CoNLL-7 format.
        """
        dep_string = ""

        for i, word in enumerate(sent):
            if word.head is word:
                head_idx = 0
            else:
                # The head id is the head id of the word - the index of the
                # first word of the sentence + 1
                head_idx = word.head.i - sent[0].i + 1

            dep = word.dep_
            if word.dep_ == "ROOT":
                dep = "root"

            # Prevent line breaks in conll string.
            if "\n" in word.text:
                dep_string += "\n"
            # Exclude spaces since they otherwise cause an assertion error in dependencygraph.py
            elif word.text.isspace():
                continue
            else:
                dep_string += ("%d\t%s\t%s\t%s\t%s\t%d\t%s\n" % (i + 1, word.text, word.text, word.tag_, word.tag_, head_idx, dep))

        return dep_string
