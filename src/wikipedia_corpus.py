from typing import Iterator

import json

from src.wikipedia_article import WikipediaArticle, article_from_json


class WikipediaCorpus:
    def __init__(self, article_file: str):
        self.article_file = article_file

    def get_articles(self) -> Iterator[WikipediaArticle]:
        for line in open(self.article_file):
            yield article_from_json(line)
