from typing import Iterator

from src import settings
from src.paragraph import paragraph_from_json, Paragraph


class ParagraphReader:
    @staticmethod
    def _read_file(file: str) -> Iterator[Paragraph]:
        for line in open(file):
            yield paragraph_from_json(line)

    @staticmethod
    def training_paragraphs():
        return ParagraphReader._read_file(settings.TRAINING_PARAGRAPHS_FILE)

    @staticmethod
    def development_paragraphs():
        return ParagraphReader._read_file(settings.DEVELOPMENT_PARAGRAPHS_FILE)
