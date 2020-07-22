from typing import Iterator

from src import settings


class ConllToken:
    def __init__(self,
                 text: str,
                 tag: str,
                 true_label: str):
        self.text = text
        self.tag = tag
        self.true_label = true_label
        self.predicted_label = None

    def get_truth(self) -> str:
        return "\\".join((self.text, self.tag, self.true_label))

    def set_predicted_label(self, label: str):
        self.predicted_label = label

    def get_predicted(self) -> str:
        return "\\".join((self.text, self.tag, self.predicted_label))


class ConllDocument:
    def __init__(self, raw: str):
        id, text = raw.split("\t")
        self.id = id
        raw_tokens = text.split()
        self.tokens = []
        for raw_token in raw_tokens:
            text, tag, label = raw_token.split("\\")
            self.tokens.append(ConllToken(text, tag, label))

    def text(self):
        return ' '.join([token.text for token in self.tokens])

    def get_truth(self):
        return ' '.join([token.get_truth() for token in self.tokens])

    def get_predicted(self):
        return ' '.join([token.get_predicted() for token in self.tokens])


def conll_documents() -> Iterator[ConllDocument]:
    for line in open(settings.CONLL_BENCHMARK_FILE):
        document = ConllDocument(line[:-1])
        yield document
