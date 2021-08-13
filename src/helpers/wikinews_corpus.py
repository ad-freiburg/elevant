from typing import Iterator

from src.helpers.wikinews_dump_reader import WikinewsDumpReader
from src.helpers.wikipedia_corpus import WikipediaCorpus
from src.models.wikipedia_article import WikipediaArticle
from src import settings


class WikinewsCorpus(WikipediaCorpus):
    @staticmethod
    def get_articles(path: str, n: int = -1) -> Iterator[WikipediaArticle]:
        wikinews_dump_reader = WikinewsDumpReader()
        with open(path) as file:
            for l_i, line in enumerate(file):
                article = wikinews_dump_reader.json2article(line)
                yield article
                if (l_i + 1) == n:
                    break

    @staticmethod
    def training_articles(n: int = -1) -> Iterator[WikipediaArticle]:
        return WikinewsCorpus.get_articles(settings.WIKINEWS_TRAINING_ARTICLES, n)

    @staticmethod
    def development_articles(n: int = -1) -> Iterator[WikipediaArticle]:
        return WikinewsCorpus.get_articles(settings.WIKINEWS_DEVELOPMENT_ARTICLES, n)

    @staticmethod
    def test_articles(n: int = -1) -> Iterator[WikipediaArticle]:
        return WikinewsCorpus.get_articles(settings.WIKINEWS_TEST_ARTICLES, n)
