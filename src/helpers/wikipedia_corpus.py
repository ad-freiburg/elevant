from typing import Iterator
from src.models.wikipedia_article import WikipediaArticle
from src.helpers.wikipedia_dump_reader import WikipediaDumpReader
from src import settings


class WikipediaCorpus:
    @staticmethod
    def get_articles(path: str, n: int = -1) -> Iterator[WikipediaArticle]:
        with open(path) as file:
            for l_i, line in enumerate(file):
                article = WikipediaDumpReader.json2article(line)
                yield article
                if (l_i + 1) == n:
                    break

    @staticmethod
    def training_articles(n: int = -1) -> Iterator[WikipediaArticle]:
        return WikipediaCorpus.get_articles(settings.TRAINING_ARTICLES, n)

    @staticmethod
    def development_articles(n: int = -1) -> Iterator[WikipediaArticle]:
        return WikipediaCorpus.get_articles(settings.DEVELOPMENT_ARTICLES, n)

    @staticmethod
    def test_articles(n: int = -1) -> Iterator[WikipediaArticle]:
        return WikipediaCorpus.get_articles(settings.TEST_ARTICLES, n)
