from typing import Iterator
from elevant.models.article import Article
from elevant.helpers.wikipedia_dump_reader import WikipediaDumpReader
from elevant import settings


class WikipediaCorpus:
    @staticmethod
    def get_articles(path: str, n: int = -1) -> Iterator[Article]:
        with open(path) as file:
            for l_i, line in enumerate(file):
                article = WikipediaDumpReader.json2article(line)
                yield article
                if (l_i + 1) == n:
                    break

    @staticmethod
    def training_articles(n: int = -1) -> Iterator[Article]:
        return WikipediaCorpus.get_articles(settings.WIKIPEDIA_TRAINING_ARTICLES, n)

    @staticmethod
    def development_articles(n: int = -1) -> Iterator[Article]:
        return WikipediaCorpus.get_articles(settings.WIKIPEDIA_DEVELOPMENT_ARTICLES, n)

    @staticmethod
    def test_articles(n: int = -1) -> Iterator[Article]:
        return WikipediaCorpus.get_articles(settings.WIKIPEDIA_TEST_ARTICLES, n)
