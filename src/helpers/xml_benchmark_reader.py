import os

from typing import Iterator

from src.models.entity_database import EntityDatabase
from src.models.wikipedia_article import WikipediaArticle

from xml.etree import ElementTree


class XMLBenchmarkParser:
    def __init__(self, entity_db: EntityDatabase):
        self.entity_db = entity_db
        self.mention_dictionary = dict()

    def to_article(self, filename: str, text: str) -> WikipediaArticle:
        """
        Use the mention dictionary to create a WikipediaArticle from the given
        text.
        """
        # At least Neural EL has a problem with articles starting with whitespace.
        # Therefore left-strip whitespaces and adjust the label spans.
        stripped_text = text.lstrip()
        offset = len(text) - len(stripped_text)
        if filename in self.mention_dictionary:
            wiki_labels = self.mention_dictionary[filename]
            labels = []
            for span, wiki_name in wiki_labels:
                span = span[0] - offset, span[1] - offset
                # For now, simply ignore NIL-entities.
                if wiki_name != "NIL" and wiki_name is not None:
                    entity_id = self.entity_db.link2id(wiki_name)
                    if entity_id is None:
                        # This is the case for one ACE wiki name (Lujaizui)
                        # which does not (anymore?) exist in Wikipedia either.
                        # For MSNBC 2 distinct entities: "State Children's Health Insurance Program" and "S&P 500"
                        print("\nMapping not found for wiki title: %s" % wiki_name)
                    else:
                        labels.append((span, entity_id))
            return WikipediaArticle(id=-1, title="", text=stripped_text, links=[], labels=labels)

    def get_mention_dictionary(self, xml_file: str):
        """
        Build a mapping from a document name to a list of mentions from the
        given xml file.
        """
        xml_tree = ElementTree.parse(xml_file)
        root = xml_tree.getroot()
        for document in root.iter('document'):
            doc_name = document.get('docName')
            self.mention_dictionary[doc_name] = []
            for annotation in document.iter('annotation'):
                wiki_title = annotation.find('wikiName').text
                start = int(annotation.find('offset').text)
                length = int(annotation.find('length').text)
                span = start, start + length
                self.mention_dictionary[doc_name].append((span, wiki_title))

    def article_iterator(self, xml_file: str, raw_text_dir: str) -> Iterator[WikipediaArticle]:
        """
        Yields for each document in the XML file and its corresponding
        document in the raw_text_dir a WikipediaArticle with labels.
        """
        self.get_mention_dictionary(xml_file)
        for filename in sorted(os.listdir(raw_text_dir)):
            file_path = os.path.join(raw_text_dir, filename)
            text = ''.join(open(file_path, "r", encoding="utf8").readlines())
            article = self.to_article(filename, text)
            # There are 57 files for ACE, but only 36 documents in the xml file.
            # But the number of non-NIL mentions in the xml file is 257 as it should be
            # So assume we can skip the remaining documents
            if article:
                yield article
