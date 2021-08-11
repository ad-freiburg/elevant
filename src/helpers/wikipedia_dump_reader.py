from typing import Iterator, Dict, Tuple, List, Optional

import os
import json
import re
from urllib.parse import unquote

from src.models.wikipedia_article import WikipediaArticle
from src import settings


class WikipediaDumpReader:
    _link_start_tag_open = "<a href=\""
    _tag_re = re.compile("<([/]?)([^<>]*)>")

    @staticmethod
    def _file_iterator(extracted_corpus_dir: str) -> Iterator[str]:
        """
        Iterates over all files of a Wikipedia corpus extracted by the WikiExtractor in JSON or text format.
        Assumes that the files are located at depth two at the given directory.
        The usual directory structure is:
        json_dir
        ↳ AA
          ↳ wiki_00

        :param extracted_corpus_dir: path to the directory where the corpus was extracted to
        :return: iterator over full paths to the files
        """
        for subdir in sorted(os.listdir(extracted_corpus_dir)):
            subdir_path = os.path.join(extracted_corpus_dir, subdir)
            for file in sorted(os.listdir(subdir_path)):
                file_path = os.path.join(subdir_path, file)
                yield file_path

    @staticmethod
    def _extract_link_target(link_html: str) -> str:
        """
        Get the link target for an HTML link start tag with the format
          <a href="...">
        where the '...' is the link target.

        :param link_html: HTML snippet representing a link start tag
        :return: link target
        """
        if link_html.startswith(WikipediaDumpReader._link_start_tag_open):
            target_end = link_html.find("\"", len(WikipediaDumpReader._link_start_tag_open))
            target = link_html[len(WikipediaDumpReader._link_start_tag_open):target_end]
            target = unquote(target)
            return target
        else:
            print("WARNING: could not parse link '%s'." % link_html)
            return ""

    @staticmethod
    def _process_tagged_text(text_with_tags: str) -> Tuple[str, List[Tuple[Tuple[int, int], str]],
                                                           List[Tuple[int, int]]]:
        """
        Replace HTML links by their link texts and keep the link positions and targets.
        Additionally keep texts that were printed in bold.

        :param text_with_tags: A text that may contain HTML links.
        :return: first: The text where the HTML links are replaced by the link texts.
                 second: A list of the links, as tuples (span, target), where span is the start and end position
                     of the link in the returned text, and target is the link target.
                 third: A list of spans of title synonyms (text in the first article paragraph printed in bold)
        """
        text_position = 0
        text = ""
        links = []
        title_synonyms = []
        bold_open_pos = -1
        link_open_pos = -1
        link_target = ""
        for tag_match in WikipediaDumpReader._tag_re.finditer(text_with_tags):
            # Check whether it's an opening or closing tag
            open_tag = False
            if not tag_match.group(1):
                open_tag = True

            # Expand text up until current tag start
            text += text_with_tags[text_position:tag_match.start()]

            if open_tag:
                # Keep track of tag opening positions
                if tag_match.group(2) == "b":
                    bold_open_pos = len(text)
                elif tag_match.group(2).startswith("a "):
                    link_open_pos = len(text)
                    link_target = WikipediaDumpReader._extract_link_target(tag_match.group(0))
            else:
                # Add link or title synonym
                tag_end_pos = len(text)
                if tag_match.group(2) == "b":
                    if text.count("\n\n") < 2 and bold_open_pos >= 0:
                        # Extract title synonyms from bold text in the first paragraph
                        title_synonyms.append((bold_open_pos, tag_end_pos))
                    bold_open_pos = -1
                elif tag_match.group(2) == "a":
                    if link_open_pos >= 0:
                        links.append(((link_open_pos, tag_end_pos), link_target))
                    link_open_pos = -1

            # Update current text position
            text_position = tag_match.end()

        # Append remaining text
        text += text_with_tags[text_position:]

        return text, links, title_synonyms

    @staticmethod
    def json_iterator(yield_none: Optional[bool] = False) -> Iterator[str]:
        """
        Iterate over all articles in JSON format.

        :param yield_none: whether to yield None as last element
        :return: iterator over JSON strings representing articles
        """
        for line in open(settings.ARTICLE_JSON_FILE):
            yield line
        if yield_none:
            yield None

    @staticmethod
    def json2article(json_dump: str) -> WikipediaArticle:
        """
        Transform an extracted article from JSON format to a WikipediaArticle object.

        :param json_dump: JSON string representing the extracted article
        :return: the article as WikipediaArticle object
        """
        article_data = json.loads(json_dump)
        article_data: Dict
        text, links, title_synonyms = WikipediaDumpReader._process_tagged_text(article_data["text"])
        article = WikipediaArticle(id=article_data["id"],
                                   title=article_data["title"],
                                   text=text,
                                   links=links,
                                   title_synonyms=title_synonyms,
                                   url=article_data["url"])
        return article

    @staticmethod
    def article_iterator(yield_none: Optional[bool] = False) -> Iterator[WikipediaArticle]:
        """
        Iterates over the articles in the given extracted Wikipedia dump.

        :param yield_none: whether to yield None as the last object
        :return: iterator over WikipediaArticle objects
        """
        for line in WikipediaDumpReader.json_iterator():
            article = WikipediaDumpReader.json2article(line)
            yield article
        if yield_none:
            yield None
