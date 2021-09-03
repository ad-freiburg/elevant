from typing import Iterator

from src.helpers.newscrawl_dump_reader import NewscrawlDumpReader
from src.helpers.wikipedia_corpus import WikipediaCorpus
from src.models.wikipedia_article import WikipediaArticle
from src import settings


class NewscrawlCorpus(WikipediaCorpus):
    @staticmethod
    def get_articles(path: str, n: int = -1) -> Iterator[WikipediaArticle]:
        with open(path) as file:
            for l_i, line in enumerate(file):
                article = NewscrawlDumpReader.json2article(line)
                yield article
                if (l_i + 1) == n:
                    break

    @staticmethod
    def training_articles(n: int = -1) -> Iterator[WikipediaArticle]:
        raise NotImplementedError()

    @staticmethod
    def development_articles(n: int = -1) -> Iterator[WikipediaArticle]:
        return NewscrawlCorpus.get_articles(settings.NEWSCRAWL_DEVELOPMENT_ARTICLES, n)

    @staticmethod
    def test_articles(n: int = -1) -> Iterator[WikipediaArticle]:
        return NewscrawlCorpus.get_articles(settings.NEWSCRAWL_TEST_ARTICLES, n)
