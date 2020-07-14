from src.entity_mention import EntityMention
from src.wikipedia_article import WikipediaArticle
from src import settings


WIKI_URL_PREFIX = "https://en.wikipedia.org/wiki/"
ENTITY_PREFIX = "http://www.wikidata.org/entity/"


def get_mapping(mappings_file: str = settings.WIKI_MAPPING_FILE):
    mapping = {}
    for i, line in enumerate(open(mappings_file)):
        line = line[:-1]
        link_url, entity_url = line.split(">,<")
        link_url = link_url[1:]
        entity_url = entity_url[:-1]
        entity_name = link_url[len(WIKI_URL_PREFIX):].replace('_', ' ')
        entity_id = entity_url[len(ENTITY_PREFIX):]
        mapping[entity_name] = entity_id
    return mapping


class LinkEntityLinker:
    LINKER_IDENTIFIER = "ARTICLE_LINK"

    def __init__(self, mappings_file: str = settings.WIKI_MAPPING_FILE):
        self.mapping = get_mapping(mappings_file)  # entity name -> entity id
        self.entity_names = {self.mapping[entity_name]: entity_name for entity_name in self.mapping}

    def link_entities(self, article: WikipediaArticle):
        raise NotImplementedError()

    def contains_name(self, name: str) -> bool:
        return name in self.mapping

    def get_entity_id(self, name: str) -> str:
        return self.mapping[name]
