from typing import List

import re

from src.wikipedia_article import WikipediaArticle
from src.markup_special_characters import SPECIAL_CHARACTERS
from src.paragraph import Paragraph


def split_markup(text: str) -> List[str]:
    """
    Split the markup from the non-markup text.

    :param text: input text
    :return: list with snippets which are either markup or non-markup
    """
    splits = []
    markup_level = False
    i = 0
    split_begin = 0
    while i < len(text):
        if i == len(text) - 1 and i > split_begin:
            splits.append(text[split_begin:])
        inside_markup = markup_level > 0
        two_chars = text[i:(i + 2)]
        if two_chars == "[[":
            markup_level += 1
            i += 2
        elif two_chars == "]]":
            markup_level -= 1
            i += 2
        else:
            i += 1
        if (inside_markup and markup_level == 0) or (not inside_markup and markup_level == 1):
            split_end = i if inside_markup else (i - 2)
            split = text[split_begin:split_end]
            splits.append(split)
            split_begin = split_end
    return splits


def is_markup(text: str):
    """Check if a text snippet starts and ends with markup brackets."""
    return text.startswith("[[") and text.endswith("]]")


def get_inner(markup: str):
    """Return the part between markup brackets. (Asserts that the given snippet starts and ends with [[ and ]]."""
    return markup[2:-2]


def is_headline(text: str):
    """Check if a single line is a headline."""
    return len(text) > 1 and text.startswith("=") and text.endswith("=")


def join_lines(lines: List[str]) -> str:
    """Make the lines a single text, where the lines are separated by spaces."""
    return ' '.join(lines)


def split_paragraphs(text: str):
    """Split a text into paragraphs.
    It gets split at line breaks, then lines are merged again if they are not separated by empty lines.
    Exceptions are made for headlines, which become single-line paragraphs."""
    paragraphs = []
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    paragraph_start_line = 0
    for i, line in enumerate(lines):
        if is_headline(line):
            if i > paragraph_start_line:
                paragraphs.append(join_lines(lines[paragraph_start_line:i]))
            paragraphs.append(line)
            paragraph_start_line = i + 1
        elif line == '':
            if i > paragraph_start_line:
                paragraphs.append(join_lines(lines[paragraph_start_line:i]))
            paragraph_start_line = i + 1
    if paragraph_start_line <= len(lines):
        paragraph = ' '.join(lines[paragraph_start_line:])
        paragraphs.append(paragraph)
    return paragraphs


filter_regex = re.compile("[{}<>*]|\[\[\[|\]\]\]|#REDIRECT|File:|Image:|Category:|--|&")


def contains_filter_pattern(text: str):
    """Check if one of the disallowed patterns occurs in the text."""
    return bool(filter_regex.search(text))


def filter_texts(texts: List[str]) -> List[str]:
    """Remove texts that contain markup."""
    filtered = []
    for text in texts:
        if len(text) == 0 or contains_filter_pattern(text) or is_headline(text) or not text[0].isalnum():
            pass
            # print("FILTERED: %s" % text)
        else:
            filtered.append(text)
    return filtered


SHARP_BRACKET_CODES = (("&lt;", "<"),
                       ("&gt;", ">"))


def insert_sharp_brackets(text: str):
    """Inserts < and >."""
    for code, value in SHARP_BRACKET_CODES:
        text = text.replace(code, value)
    return text


def insert_special_characters(text: str):
    """Inserts special characters from here: https://en.wikipedia.org/wiki/Help:Wikitext"""
    for code, value in SPECIAL_CHARACTERS:
        text = text.replace(code, value)
        return text


remove_regex = re.compile("''+")


def remove_patterns(text):
    """Remove multiple occurences of '."""
    return remove_regex.sub('', text)


multispace_regex = re.compile("  +")


def single_space(text: str) -> str:
    """Replace multi-spaces by single spaces."""
    return multispace_regex.sub(' ', text)


def preprocess_text(text: str) -> str:
    """
    Unify the style of a text, by
    - removing signs for italic and bold text
    - unifying the spacing
    - replacing special character codes with the characters

    :param text: input text
    :return: preprocessed text
    """
    text = remove_patterns(text)
    text = single_space(text)
    text = insert_sharp_brackets(text)
    text = insert_special_characters(text)
    return text


class MarkupProcessor:
    def __init__(self):
        self.n_paragraphs_extracted = 0
        self.n_paragraphs_filtered = 0

    def filter_markup_and_link_entities(self, article: WikipediaArticle):
        """
        Splits a Wikipedia article into paragraphs and adds Wikipedia-internal links to it.
        Currently, most paragaphs containing markup are simply ignored.

        :param article: wikipedia article
        """
        paragraphs = split_paragraphs(article.text)
        paragraphs = [preprocess_text(paragraph) for paragraph in paragraphs]
        n_paragraphs_all = len(paragraphs)
        paragraphs = filter_texts(paragraphs)
        self.n_paragraphs_extracted += len(paragraphs)
        self.n_paragraphs_filtered += n_paragraphs_all - len(paragraphs)
        article.paragraphs = []
        for paragraph in paragraphs:
            splits = split_markup(paragraph)
            text = ""
            paragraph_links = []
            for split in splits:
                if is_markup(split):
                    inner = get_inner(split)
                    values = inner.split("|")
                    entity_name = values[0]
                    entity_text = values[-1]
                    paragraph_links.append(((len(text), len(text) + len(entity_text)), entity_name))
                    text += entity_text
                else:
                    text += split
            article.paragraphs.append(
                Paragraph(text=paragraph,
                          wikipedia_links=paragraph_links)
            )
