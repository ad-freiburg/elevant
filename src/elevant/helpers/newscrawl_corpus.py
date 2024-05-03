from typing import Iterator

from elevant.helpers.newscrawl_dump_reader import NewscrawlDumpReader
from elevant.helpers.wikipedia_corpus import WikipediaCorpus
from elevant.models.article import Article
from elevant import settings


class NewscrawlCorpus(WikipediaCorpus):
    @staticmethod
    def get_articles(path: str, n: int = -1) -> Iterator[Article]:
        with open(path) as file:
            for l_i, line in enumerate(file):
                article = NewscrawlDumpReader.json2article(line)
                yield article
                if (l_i + 1) == n:
                    break

    @staticmethod
    def training_articles(n: int = -1) -> Iterator[Article]:
        raise NotImplementedError()

    @staticmethod
    def development_articles(n: int = -1) -> Iterator[Article]:
        return NewscrawlCorpus.get_articles(settings.NEWSCRAWL_DEVELOPMENT_ARTICLES, n)

    @staticmethod
    def test_articles(n: int = -1) -> Iterator[Article]:
        return NewscrawlCorpus.get_articles(settings.NEWSCRAWL_TEST_ARTICLES, n)
