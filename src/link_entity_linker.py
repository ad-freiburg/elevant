from src.wikipedia_article import Paragraph
from src.entity_mention import EntityMention
from src import settings


WIKI_URL_PREFIX = "https://en.wikipedia.org/wiki/"
ENTITY_PREFIX = "http://www.wikidata.org/entity/"


def get_mapping(mappings_file: str):
    print("load mappings...")
    mapping = {}
    for i, line in enumerate(open(mappings_file)):
        line = line[:-1]
        link_url, entity_url = line.split(">,<")
        link_url = link_url[1:]
        entity_url = entity_url[:-1]
        entity_name = link_url[len(WIKI_URL_PREFIX):].replace('_', ' ')
        entity_id = entity_url[len(ENTITY_PREFIX):]
        mapping[entity_name] = entity_id
    print("%i url->entity mappings" % len(mapping))
    return mapping


class LinkEntityLinker:
    LINKER_IDENTIFIER = "ARTICLE_LINK"

    def __init__(self, mappings_file: str = settings.LINKS_FILE):
        self.mapping = get_mapping(mappings_file)  # entity name -> entity id
        self.entity_names = {self.mapping[entity_name]: entity_name for entity_name in self.mapping}

    def link_entities(self, paragraph: Paragraph):
        entity_mentions = []
        for span, entity in paragraph.wikipedia_links:
            mention = EntityMention(span, recognized_by=self.LINKER_IDENTIFIER)
            if entity in self.mapping:
                mention.entity_id = self.mapping[entity]
                mention.linked_by = self.LINKER_IDENTIFIER
            entity_mentions.append(mention)
        paragraph.add_entity_mentions(entity_mentions)

    def contains_name(self, name: str) -> bool:
        return name in self.mapping

    def get_entity_id(self, name: str) -> str:
        return self.mapping[name]
