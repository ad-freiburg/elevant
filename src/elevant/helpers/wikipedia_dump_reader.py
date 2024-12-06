import logging
from typing import Iterator, Dict, Tuple, List, Optional

import os
import json
import re
from urllib.parse import unquote

from elevant.models.article import Article, ABSTRACT_INDICATOR
from elevant import settings

logger = logging.getLogger("main." + __name__.split(".")[-1])


class WikipediaDumpReader:
    _link_start_tag_open = "<a href=\""
    _tag_re = re.compile("<([/]?)([^<>]*)>")
    _section_re = re.compile("\nSection::::([^\n]*)$", re.MULTILINE)

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
            logger.debug("Could not parse link '%s'." % link_html)
            return ""

    @staticmethod
    def _process_extractor_text(extractor_text: str) -> Tuple[str, List[Tuple[Tuple[int, int], str]],
                                                              List[Tuple[int, int]], List[Tuple[Tuple[int, int], str]]]:
        """
        Replace HTML links by their link texts and keep the link positions and targets.
        Additionally keep texts that were printed in bold.
        Remove section headers marked with 'Section::::' by the WikiExtractor from the text and return section info.

        :param extractor_text: A text that may contain HTML links.
        :return: first: The text where the HTML links are replaced by the link texts.
                 second: A list of the links, as tuples (span, target), where span is the start and end position
                     of the link in the returned text, and target is the link target.
                 third: A list of spans of title synonyms (text in the first article paragraph printed in bold)
                 fourth: A list of the sections, as tuples (span, section_title).
        """
        text_position = 0
        text = ""

        # tag vars
        hyperlinks = []
        title_synonyms = []
        bold_open_pos = -1
        link_open_pos = -1
        link_target = ""

        # section vars
        sections = []
        section_start = 0
        section_title = ABSTRACT_INDICATOR

        tag_iterator = WikipediaDumpReader._tag_re.finditer(extractor_text)
        section_iterator = WikipediaDumpReader._section_re.finditer(extractor_text)

        tag_match = next(tag_iterator, None)
        section_match = next(section_iterator, None)
        while tag_match or section_match:
            if tag_match and (not section_match or section_match.start() > tag_match.start()):
                # Process tag match
                # Expand text up until current tag start
                text += extractor_text[text_position:tag_match.start()]

                # Check whether it's an opening or closing tag
                open_tag = False
                if not tag_match.group(1):
                    open_tag = True

                if open_tag:
                    # Keep track of tag opening positions
                    if tag_match.group(2) == "b":
                        bold_open_pos = len(text)
                    elif tag_match.group(2).startswith("a "):
                        link_open_pos = len(text)
                        link_target = WikipediaDumpReader._extract_link_target(tag_match.group(0))
                    elif tag_match.group(2).startswith(" ") and tag_match.group(2).endswith(" "):
                        # Probably not a tag, so ignore match.
                        # Undo expansion of text until current tag start, otherwise it's added twice
                        added_text_length = tag_match.start() - text_position
                        text = text[:-added_text_length]
                        tag_match = next(tag_iterator, None)
                        continue
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
                            hyperlinks.append(((link_open_pos, tag_end_pos), link_target))
                        link_open_pos = -1

                # Update current text position
                text_position = tag_match.end()

                # Get next tag match
                tag_match = next(tag_iterator, None)

            else:
                # Process section match
                # Ignore tags within section headers (yes, this does happen)
                while tag_match and tag_match.start() < section_match.end():
                    tag_match = next(tag_iterator, None)

                # Expand text up until current section start
                text += extractor_text[text_position:section_match.start()]

                # Add section to section list. +1 so the newline character
                # after the section header is part of the previous section.
                section_end = len(text) + 1
                sections.append(((section_start, section_end), section_title))

                # Set title and start for the next section
                section_title = section_match.group(1)
                section_start = section_end

                # Update current text position
                text_position = section_match.end()

                # Get next section match
                section_match = next(section_iterator, None)

        # Append remaining text
        text += extractor_text[text_position:]

        # Append last section
        sections.append(((section_start, len(text)), section_title))

        return text, hyperlinks, title_synonyms, sections

    @staticmethod
    def json_iterator(yield_none: Optional[bool] = False) -> Iterator[str]:
        """
        Iterate over all articles in JSON format.

        :param yield_none: whether to yield None as last element
        :return: iterator over JSON strings representing articles
        """
        for line in open(settings.EXTRACTED_WIKIPEDIA_ARTICLES):
            yield line
        if yield_none:
            yield None

    @staticmethod
    def json2article(json_dump: str) -> Article:
        """
        Transform an extracted article from JSON format to a WikipediaArticle object.

        :param json_dump: JSON string representing the extracted article
        :return: the article as WikipediaArticle object
        """
        article_data = json.loads(json_dump)
        article_data: Dict
        text, hyperlinks, title_synonyms, sections = WikipediaDumpReader._process_extractor_text(article_data["text"])
        article = Article(id=article_data["id"],
                          title=article_data["title"],
                          text=text,
                          hyperlinks=hyperlinks,
                          title_synonyms=title_synonyms,
                          url=article_data["url"],
                          sections=sections)
        return article

    @staticmethod
    def article_iterator(yield_none: Optional[bool] = False) -> Iterator[Article]:
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
