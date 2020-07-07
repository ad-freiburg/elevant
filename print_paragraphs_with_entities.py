import sys

from src.wikipedia_corpus import WikipediaCorpus
from src.entity_database import EntityDatabase
from src.entity_database_reader import EntityDatabaseReader
from src.paragraph import Paragraph
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


def print_help():
    print("Usage:\n"
          "    python3 print_paragraphs_with_entities.py <corpus_file>\n"
          "\n"
          "Examples:\n"
          "    python3 print_paragraphs_with_entities.py"
          " ~/wikipedia/wikipedia_2020-06-08/1000_articles_with_links_mapped+NERed+names.txt\n"
          "    python3 print_paragraphs_with_entities.py"
          " /local/data/hertelm/wikipedia_2020-06-08/articles_with_links_mapped+NERed+names.txt")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print_help()
        exit(1)

    corpus_file = sys.argv[1]

    corpus = WikipediaCorpus(settings.DATA_DIRECTORY + corpus_file)
    entity_db = EntityDatabaseReader.read_entity_database()

    for article in corpus.get_articles():
        for paragraph in article.paragraphs:
            print(entity_text(paragraph, entity_db))
