import abc
from typing import Iterator

from elevant.models.article import Article


class AbstractBenchmarkReader(abc.ABC):

    @abc.abstractmethod
    def article_iterator(self) -> Iterator[Article]:
        """
        Yields all articles for the benchmark.
        """
        raise NotImplementedError()

    def iterate(self, n: int = -1) -> Iterator[Article]:
        """
        Yields n or all articles from the benchmark.
        """
        for i, article in enumerate(self.article_iterator()):
            if i == n:
                break
            yield article
