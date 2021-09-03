from typing import Iterator, Optional
import json

from src.helpers.wikipedia_dump_reader import WikipediaDumpReader
from src.models.wikipedia_article import WikipediaArticle


class NewscrawlDumpReader(WikipediaDumpReader):
    @staticmethod
    def json_iterator(yield_none: Optional[bool] = False) -> Iterator[str]:
        """
        Iterate over all articles in JSON format.
        :param yield_none: whether to yield None as last element
        :return: iterator over JSON strings representing articles
        """
        raise NotImplementedError()

    @staticmethod
    def json2article(json_dump: str) -> WikipediaArticle:
        """
        Transform an extracted article from JSON format to a WikipediaArticle object.
        :param json_dump: JSON string representing the extracted article
        :return: the article as WikipediaArticle object
        """
        article_data = json.loads(json_dump)
        title = article_data["date"] + " - " + article_data["text"].split("\n\n")[0]
        article = WikipediaArticle(id=article_data["id"],
                                   title=title,
                                   text=article_data["text"],
                                   links=[])
        return article

    @staticmethod
    def article_iterator(yield_none: Optional[bool] = False) -> Iterator[WikipediaArticle]:
        """
        Iterates over the articles in the given Newscrawl dump.
        :param yield_none: whether to yield None as the last object
        :return: iterator over WikipediaArticle objects
        """
        raise NotImplementedError()
