from typing import Iterator

import sys

from src.wikipedia_corpus import WikipediaCorpus
from src.entity_database import EntityDatabase
from src.entity_database_reader import EntityDatabaseReader
from src.paragraph import Paragraph, paragraph_from_json
from src import settings


def entity_text(paragraph: Paragraph, entities: EntityDatabase):
    """Returns the paragraph text where entity mentions are annotated."""
    text = paragraph.text
    for entity in reversed(paragraph.entity_mentions):
        begin, end = entity.span
        entity_text_snippet = text[begin:end]
        if entity.is_linked():
            entity_id = entity.entity_id
            entity_name = entities.get(entity_id).name if entities.contains(entity_id) else ""
            linker_identifier = entity.linked_by.lower()
            linked_entity_text = "%s;%s;%s|" % (entity_id, entity_name, linker_identifier)
        else:
            linked_entity_text = ""
        entity_string = "[%s%s]" % (linked_entity_text, entity_text_snippet)
        text = text[:begin] + entity_string + text[end:]
    return text


def corpus_paragraphs(in_file: str) -> Iterator[Paragraph]:
    corpus = WikipediaCorpus(settings.DATA_DIRECTORY + in_file)
    for article in corpus.get_articles():
        for paragraph in article.paragraphs:
            yield paragraph


def file_paragraphs(in_file: str) -> Iterator[Paragraph]:
    for line in open(settings.DATA_DIRECTORY + in_file):
        paragraph = paragraph_from_json(line)
        yield paragraph


def print_help():
    print("Usage:\n"
          "    python3 print_paragraphs_with_entities.py <in_file> [-p]")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
        exit(1)

    in_file = sys.argv[1]
    is_paragraph_file = "-p" in sys.argv
    paragraphs = file_paragraphs(in_file) if is_paragraph_file else corpus_paragraphs(in_file)

    entity_db = EntityDatabaseReader.read_entity_database(verbose=False)

    for paragraph in paragraphs:
        print(entity_text(paragraph, entity_db))
