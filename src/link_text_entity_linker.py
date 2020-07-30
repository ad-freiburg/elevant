from typing import Dict

from src.entity_mention import EntityMention
from src.wikipedia_article import WikipediaArticle
from src.entity_database_reader import EntityDatabaseReader


def get_mapping():
    return EntityDatabaseReader.get_mapping()


class LinkTextEntityLinker:
    LINKER_IDENTIFIER = "LINK_TEXT_LINKER"

    def __init__(self, entity_db):
        self.mapping = get_mapping()  # entity name -> entity id
        self.entity_db = entity_db

    def add_synonyms(self, entity_id: str, synonym_dict: Dict):
        """Add all aliases of an entity to dictionary
        """
        if self.entity_db.contains_entity(entity_id):
            entity = self.entity_db.get_entity(entity_id)
            synonyms = entity.synonyms
            # print(synonyms)
            for syn in synonyms:
                # Do not append all lowercase synonyms (e.g. "it" for Italy)
                if not syn.islower():
                    synonym_dict[syn] = entity_id

    def link_entities(self, article: WikipediaArticle, doc=None):
        entity_links = dict()
        entity_synonyms = dict()
        covered_positions = set()
        entity_mentions = []

        # Link article entity to Wikidata id
        if article.title in self.mapping:
            entity_id = self.mapping[article.title]
            entity_links[article.title] = entity_id
            self.add_synonyms(entity_id, entity_synonyms)

        # Link article links to Wikidata ids
        for span, target in article.links:
            link_text = article.text[span[0]:span[1]]
            if target in self.mapping and not link_text.islower():
                entity_id = self.mapping[target]
                entity_links[link_text] = entity_id
                self.add_synonyms(entity_id, entity_synonyms)
                covered_positions.update(range(span[0], span[1]))

                # Expand entity span to end of word
                end_idx = span[1]
                while end_idx + 1 < len(article.text) and article.text[end_idx].isalpha():
                    # TODO: consider expanding only up to a certain amount of characters
                    end_idx += 1

                entity_mention = EntityMention(span=(span[0], end_idx),
                                               recognized_by=self.LINKER_IDENTIFIER,
                                               entity_id=entity_id,
                                               linked_by=self.LINKER_IDENTIFIER)
                entity_mentions.append(entity_mention)

        # Link text that has been linked to an entity before, starting with the longest text
        for link_text, entity_id in sorted(entity_links.items(), key=lambda x: len(x[0]), reverse=True) + \
                                    sorted(entity_synonyms.items(), key=lambda x: len(x[0]), reverse=True):
            search_start_idx = 0
            while True:
                start_idx = article.text.find(link_text, search_start_idx)

                # link text / synonym was not found in remaining article text
                if start_idx == -1:
                    break

                # Only add entity if its first character is the beginning of a word
                if start_idx != 0 and article.text[start_idx - 1].isalpha():
                    search_start_idx = start_idx + 1
                    continue

                # Expand entity span to end of word
                end_idx = start_idx + len(link_text)
                while end_idx + 1 < len(article.text) and article.text[end_idx].isalpha():
                    # TODO: consider expanding only up to a certain amount of characters
                    # print("Expanding mention \"%s\" by \"%s\"" % (link_text, article.text[end_idx]))
                    end_idx += 1

                # Check if the found text span does overlap with an already linked entity
                skip = False
                for i in range(start_idx, end_idx):
                    if i in covered_positions:
                        search_start_idx = end_idx
                        # print("Overlap at %d for text %s" % (i, link_text))
                        skip = True
                        break
                if skip:
                    continue

                # Add text span to entity mentions
                covered_positions.update(range(start_idx, end_idx))
                # print("Add entity %s for link text \"%s\"" % (entity_id, link_text))
                entity_mention = EntityMention(span=(start_idx, end_idx),
                                               recognized_by=self.LINKER_IDENTIFIER,
                                               entity_id=entity_id,
                                               linked_by=self.LINKER_IDENTIFIER)
                entity_mentions.append(entity_mention)
                search_start_idx = end_idx

        article.add_entity_mentions(entity_mentions)

