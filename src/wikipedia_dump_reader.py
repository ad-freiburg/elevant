from typing import Iterator

import os
import bz2

from src.wikipedia_article import WikipediaArticle


PAGE_START_TAG = "<page>"
PAGE_END_TAG = "</page>"
ID_START_TAG = "<id>"
ID_END_TAG = "</id>"
TITLE_START_TAG = "<title>"
TITLE_END_TAG = "</title>"
TEXT_START_TAG_OPEN = "<text"
TEXT_END_TAG = "</text>"


class WikipediaDumpReader:
    @staticmethod
    def page_iterator(dump_file: str) -> Iterator[str]:
        """
        Iterate over the pages in a Wikipedia dump.
        Yields everything between <page> and </page> tags.

        :param dump_file: path to the bz2 dump file
        :return: iterator over pages (strings)
        """
        page_content = ""
        inside_page = False
        for line in bz2.open(dump_file):
            line = line.decode()
            stripped_line = line.strip()
            if stripped_line.startswith(PAGE_START_TAG):
                page_content = ""
                inside_page = True
            if inside_page:
                page_content += line
            if stripped_line.endswith(PAGE_END_TAG):
                inside_page = False
                yield page_content

    @staticmethod
    def extract_pages(dump_file: str, out_dir: str, pages_per_subdir: int = 1000):
        """
        Write all pages from a Wikipedia dump to disk, each in a separate xml file.

        :param dump_file: path to the bz2 Wikipedia dump file
        :param out_dir: directory where the page files will be saved
        :param pages_per_subdir: how many pages to store in every subdirectory of out_dir
        """
        if out_dir[-1] != "/":
            out_dir += "/"
        if not os.path.isdir(out_dir):
            os.mkdir(out_dir)
        for i, page_content in enumerate(WikipediaDumpReader.page_iterator(dump_file)):
            if i % pages_per_subdir == 0:
                subdir = out_dir + "%i/" % (i // pages_per_subdir)
                if not os.path.isdir(subdir):
                    os.mkdir(subdir)
            path = subdir + "%i.xml" % i
            with open(path, "w") as page_file:
                page_file.write(page_content)
            print("\r%i pages" % (i + 1), end='')
        print()

    @staticmethod
    def parse_article(page_content: str) -> WikipediaArticle:
        """
        Create WikipediaArticle objects from the given XML page.

        :param page_content: xml of the page
        :return: wikipedia article
        """
        id = None
        title = None
        markup = ""
        inside_markup = False
        for line in page_content.split('\n'):
            line = line.strip()
            if id is None and line.startswith(ID_START_TAG):
                if line.endswith(ID_END_TAG):
                    line = line[:-len(ID_END_TAG)]
                id = int(line[len(ID_START_TAG):])
            if title is None and line.startswith(TITLE_START_TAG):
                if line.endswith(TITLE_END_TAG):
                    line = line[:-len(TITLE_END_TAG)]
                title = line[len(TITLE_START_TAG):]
            if line.startswith(TEXT_START_TAG_OPEN):
                inside_markup = True
                line = line[(line.find(">") + 1):]
            if inside_markup:
                if line.endswith(TEXT_END_TAG):
                    line = line[:-len(TEXT_END_TAG)]
                    inside_markup = False
                markup += line + '\n'
        if len(markup) == 0:
            print(page_content)
        return WikipediaArticle(id, title, markup)
