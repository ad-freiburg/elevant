from typing import List
import warnings

import re

from src.wikipedia_article import WikipediaArticle
from src.markup_special_characters import SPECIAL_CHARACTERS
from src.paragraph import Paragraph


def separate_links(text: str) -> List[str]:
    """
    Separates the article links from the rest of the text.

    :param text: markup text
    :return: list with snippets which are either links (starting and ending with double square brackets) or no links
    """
    splits = []
    link_level = 0
    i = 0
    split_begin = 0
    while i < len(text):
        if i == len(text) - 1 and i > split_begin:
            splits.append(text[split_begin:])
        inside_link = link_level > 0
        two_chars = text[i:(i + 2)]
        if two_chars == "[[":
            link_level += 1
            i += 2
        elif two_chars == "]]":
            link_level -= 1
            i += 2
        else:
            i += 1
        if (inside_link and link_level == 0) or (not inside_link and link_level == 1):
            split_end = i if inside_link else (i - 2)
            split = text[split_begin:split_end]
            splits.append(split)
            split_begin = split_end
    return splits


def split_markup(text: str) -> List[str]:
    warnings.warn("Function split_markup is deprecated because of wrong naming. Use separate_links instead.",
                  DeprecationWarning)
    return separate_links(text)


def is_link(text: str) -> bool:
    """Checks if a text snippet is an article link, indicated by double square brackets."""
    return text.startswith("[[") and text.endswith("]]")


def is_markup(text: str) -> bool:
    warnings.warn("Function is_markup is deprecated because of wrong naming. Use is_link instead.", DeprecationWarning)
    return is_link(text)


def get_inner(link_markup: str):
    """Returns the part between markup link brackets.
    Asserts that the given snippet starts and ends with [[ and ]]."""
    return link_markup[2:-2]


def is_headline(text: str):
    """Checks if a single line is a headline."""
    return len(text) > 1 and text.startswith("=") and text.endswith("=")


def join_lines(lines: List[str]) -> str:
    """Transforms the lines into a string without newlines, where the lines are separated by spaces."""
    return ' '.join(lines)


def split_paragraphs(text: str):
    """
    Splits a text into paragraphs.
    It gets split at line breaks, then lines are merged again if they are not separated by empty lines.
    Exceptions are made for headlines, which become single-line paragraphs.
    """
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
    """
    Checks if one of the disallowed markup patterns occurs in the text.
    These patterns are:
    - curly brackets (templates)
    - sharp brackets (html)
    - asterisk (list)
    - three opening or closing square brackets
    - #REDIRECT
    - File:
    - Image:
    - Category:
    - --
    - & (mark for special character, that was not replaced)
    """
    return bool(filter_regex.search(text))


def filter_texts(texts: List[str]) -> List[str]:
    """Removes texts that contain markup other than links."""
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
    warnings.warn("Function insert_sharp_brackets is deprecated, since its functionality is now integrated into"
                  "insert_special_characters.", DeprecationWarning)
    for code, value in SHARP_BRACKET_CODES:
        text = text.replace(code, value)
    return text


def insert_special_characters(text: str):
    """
    Replaces special character marks by the corresponding special characters.
    Marks and characters are taken from https://en.wikipedia.org/wiki/Help:Wikitext
    (section 'special characters', plus non-breaking space and sharp brackets).
    """
    for code, value in SPECIAL_CHARACTERS:
        text = text.replace(code, value)
        return text


remove_regex = re.compile("''+")


def remove_patterns(text):
    """Remove multiple occurrences of '."""
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
    text = insert_special_characters(text)
    return text


class MarkupProcessor:
    def __init__(self):
        self.n_paragraphs_extracted = 0
        self.n_paragraphs_filtered = 0

    def filter_markup_and_link_entities(self, article: WikipediaArticle):
        """
        Splits a Wikipedia article into paragraphs and adds Wikipedia-internal links to it.
        For simplicity, most paragraphs containing markup are removed.

        The articles' markup is split into paragraphs. Paragraphs with frequent markup tags, except for article links,
        are filtered out.
        After processing, the article's property 'paragraphs' is a list of Paragraph objects, which contain text and
        article links.

        :param article: WikipediaArticle, where the property 'text' is a markup string
        """
        paragraphs = split_paragraphs(article.text)
        paragraphs = [preprocess_text(paragraph) for paragraph in paragraphs]
        n_paragraphs_all = len(paragraphs)
        paragraphs = filter_texts(paragraphs)
        self.n_paragraphs_extracted += len(paragraphs)
        self.n_paragraphs_filtered += n_paragraphs_all - len(paragraphs)
        article.paragraphs = []
        for paragraph in paragraphs:
            splits = separate_links(paragraph)
            text = ""
            paragraph_links = []
            for split in splits:
                if is_link(split):
                    inner = get_inner(split)
                    values = inner.split("|")
                    link_target = values[0]
                    link_text = values[-1]
                    paragraph_links.append(((len(text), len(text) + len(link_text)), link_target))
                    text += link_text
                else:
                    text += split
            article.paragraphs.append(
                Paragraph(text=paragraph,
                          wikipedia_links=paragraph_links)
            )
