from typing import Dict
import sys

from src.wikipedia_article import WikipediaArticle, article_from_json
from src.entity_database_reader import EntityDatabaseReader
from src.wikidata_entity import WikidataEntity


def entity_text(article: WikipediaArticle, entities: Dict[str, WikidataEntity]):
    """Annotate entity mentions in the article's text."""
    text = article.text
    for span in sorted(article.entity_mentions, reverse=True):
        begin, end = span
        entity_mention = article.entity_mentions[span]
        entity_text_snippet = text[begin:end]
        if entity_mention.is_linked():
            entity_id = entity_mention.entity_id
            entity_name = entities[entity_id].name if entity_id in entities else ""
            linker_identifier = entity_mention.linked_by.lower()
            linked_entity_text = "%s;%s;%s|" % (entity_id, entity_name, linker_identifier)
        else:
            linked_entity_text = ""
        entity_string = "[%s%s]" % (linked_entity_text, entity_text_snippet)
        text = text[:begin] + entity_string + text[end:]
    return text


def print_help():
    print("Usage:\n"
          "    python3 print_linked_entities.py <in_file>")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print_help()
        exit(1)

    in_file = sys.argv[1]

    entities = EntityDatabaseReader.read_entity_database()

    for line in open(in_file):
        article = article_from_json(line)
        text = entity_text(article, entities)
        print("***** %s (%i) *****" % (article.title, article.id))
        print(text)
