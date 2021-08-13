from typing import Iterator, Optional
import json

from src.helpers.entity_database_reader import EntityDatabaseReader
from src.helpers.wikipedia_dump_reader import WikipediaDumpReader
from src.models.wikipedia_article import WikipediaArticle
from src import settings


class WikinewsDumpReader(WikipediaDumpReader):
    def __init__(self):
        self.wikinews_category_to_wikipedia = EntityDatabaseReader().get_wikinews_category_to_wikipedia_mapping()

    @staticmethod
    def json_iterator(yield_none: Optional[bool] = False) -> Iterator[str]:
        """
        Iterate over all articles in JSON format.

        :param yield_none: whether to yield None as last element
        :return: iterator over JSON strings representing articles
        """
        for line in open(settings.WIKINEWS_ARTICLE_JSON_FILE):
            yield line
        if yield_none:
            yield None

    def json2article(self, json_dump: str) -> WikipediaArticle:
        """
        Transform an extracted article from JSON format to a WikipediaArticle object.

        :param json_dump: JSON string representing the extracted article
        :return: the article as WikipediaArticle object
        """
        article_data = json.loads(json_dump)
        text, links, title_synonyms = WikipediaDumpReader._process_tagged_text(article_data["text"])
        # WikiNews links can be WikiNews-internal, links to Wikipedia or to other Wikimedia projects.
        cleaned_links = []
        for span, target in links:
            if ":" not in target and target in self.wikinews_category_to_wikipedia:
                # The link is a internal WikiNews link. Get mapping to Wikipedia title
                target = self.wikinews_category_to_wikipedia[target]
                cleaned_links.append((span, target))
            elif target.startswith("w:") or target.startswith("wikipedia:"):
                # See here for list of interwiki link prefixes: https://meta.wikimedia.org/wiki/Help:Interwiki_linking
                split_index = target.find(":")
                target = target[split_index + 1:]
                cleaned_links.append((span, target))

        article = WikipediaArticle(id=article_data["id"],
                                   title=article_data["title"],
                                   text=text,
                                   links=cleaned_links,
                                   title_synonyms=title_synonyms,
                                   url=article_data["url"])
        return article

    def article_iterator(self, yield_none: Optional[bool] = False) -> Iterator[WikipediaArticle]:
        """
        Iterates over the articles in the given extracted Wikipedia dump.

        :param yield_none: whether to yield None as the last object
        :return: iterator over WikipediaArticle objects
        """
        for line in WikinewsDumpReader.json_iterator():
            article = self.json2article(line)
            yield article
        if yield_none:
            yield None
