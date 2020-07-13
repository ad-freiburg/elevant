from typing import Iterator, Dict, Tuple, List

import os
import json
import re
from urllib.parse import unquote

from src.wikipedia_article import WikipediaArticle


class WikipediaDumpReader:
    _link_re = re.compile("<a href=\"[^>]*>[^<]*</a>")
    _link_start_tag_open = "<a href=\""
    _link_end_tag = "</a>"

    @staticmethod
    def _file_iterator(json_dir: str) -> Iterator[str]:
        for subdir in sorted(os.listdir(json_dir)):
            subdir_path = os.path.join(json_dir, subdir)
            for file in sorted(os.listdir(subdir_path)):
                file_path = os.path.join(subdir_path, file)
                yield file_path

    @staticmethod
    def _extract_link_target_and_text(link_html: str) -> Tuple[str, str]:
        if link_html.startswith(WikipediaDumpReader._link_start_tag_open) and \
                link_html.endswith(WikipediaDumpReader._link_end_tag):
            target_end = link_html.find("\"", len(WikipediaDumpReader._link_start_tag_open))
            target = link_html[len(WikipediaDumpReader._link_start_tag_open):target_end]
            target = unquote(target)
            text = link_html[(target_end + 2):-len(WikipediaDumpReader._link_end_tag)]
            return target, text
        else:
            print("Warning: could not parse link '%s'." % link_html)
            return link_html, link_html

    @staticmethod
    def _get_text_and_links(text_with_links: str) -> Tuple[str, List[Tuple[Tuple[int, int], str]]]:
        text_position = 0
        text = ""
        links = []
        for link_match in WikipediaDumpReader._link_re.finditer(text_with_links):
            link_snippet = text_with_links[link_match.start():link_match.end()]
            link_target, link_text = WikipediaDumpReader._extract_link_target_and_text(link_snippet)
            text += text_with_links[text_position:link_match.start()]
            link_start_pos = len(text)
            text += link_text
            link_end_pos = len(text)
            links.append(((link_start_pos, link_end_pos), link_target))
            text_position = link_match.end()
        text += text_with_links[text_position:]
        return text, links

    @staticmethod
    def article_iterator(json_dir: str,
                         yield_none: bool = False) -> Iterator[WikipediaArticle]:
        """
        Iterates over the articles in the given extracted Wikipedia dump.

        :param json_dir: path to the extracted JSON dump
        :param yield_none: whether to yield None as the last object
        :return: iterator over WikipediaArticle objects
        """
        for file in WikipediaDumpReader._file_iterator(json_dir):
            for line in open(file):
                article_data = json.loads(line)
                article_data: Dict
                text, links = WikipediaDumpReader._get_text_and_links(article_data["text"])
                article = WikipediaArticle(id=article_data["id"],
                                           title=article_data["title"],
                                           text=text,
                                           links=links)
                yield article
        if yield_none:
            yield None
