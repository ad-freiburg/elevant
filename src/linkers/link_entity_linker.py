from src.models.entity_mention import EntityMention
from src.models.wikipedia_article import WikipediaArticle
from src.helpers.entity_database_reader import EntityDatabaseReader


def get_mapping():
    return EntityDatabaseReader.get_wikipedia_to_wikidata_mapping()


class LinkEntityLinker:
    LINKER_IDENTIFIER = "ARTICLE_LINK"

    def __init__(self):
        self.mapping = get_mapping()  # entity name -> entity id

    def link_entities(self, article: WikipediaArticle):
        entity_mentions = []
        for span, target in article.links:
            if target in self.mapping:
                entity_id = self.mapping[target]
                entity_mention = EntityMention(span=span,
                                               recognized_by=self.LINKER_IDENTIFIER,
                                               entity_id=entity_id,
                                               linked_by=self.LINKER_IDENTIFIER,
                                               candidates={entity_id})
                entity_mentions.append(entity_mention)
        article.add_entity_mentions(entity_mentions)

    def contains_name(self, name: str) -> bool:
        return name in self.mapping

    def get_entity_id(self, name: str) -> str:
        return self.mapping[name]
