from typing import Iterator, Optional
import json

from elevant.helpers.wikipedia_dump_reader import WikipediaDumpReader
from elevant.models.article import Article


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
    def json2article(json_dump: str) -> Article:
        """
        Transform an extracted article from JSON format to a WikipediaArticle object.
        :param json_dump: JSON string representing the extracted article
        :return: the article as WikipediaArticle object
        """
        article_data = json.loads(json_dump)
        article_id = article_data["id"].replace(".", "")
        title = article_data["date"] + " - " + article_data["text"].split("\n\n")[0]
        title = title.replace("\n", "")  # A title may not contain newlines (important for evaluation in txt format)
        article = Article(id=article_id,
                          title=title,
                          text=article_data["text"])
        return article

    @staticmethod
    def article_iterator(yield_none: Optional[bool] = False) -> Iterator[Article]:
        """
        Iterates over the articles in the given Newscrawl dump.
        :param yield_none: whether to yield None as the last object
        :return: iterator over WikipediaArticle objects
        """
        raise NotImplementedError()
