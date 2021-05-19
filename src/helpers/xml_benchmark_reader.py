import os

from typing import Iterator

from src.evaluation.groundtruth_label import GroundtruthLabel
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
        else:
            wiki_labels = []
        labels = []
        label_id_counter = 0
        for span, wiki_name in wiki_labels:
            span = span[0] - offset, span[1] - offset
            # For now, simply ignore NIL-entities.
            if wiki_name != "NIL" and wiki_name is not None:
                entity_id = self.entity_db.link2id(wiki_name)
                if entity_id is None:
                    # This is the case for 3 ACE mentions one of which does not (anymore?) exist in Wikipedia either.
                    # The other two are spelling errors: "Seattke" and "USS COLE (DDG-67)" (uppercase error)
                    # For MSNBC this is the case for 87 mentions.
                    print("\nMapping not found for wiki title: %s" % wiki_name)
                else:
                    gt_label = GroundtruthLabel(label_id_counter, span, entity_id, None, None)
                    labels.append(gt_label)
                    label_id_counter += 1
        return WikipediaArticle(id=-1, title="", text=stripped_text, links=[], labels=labels)

    def get_mention_dictionary_from_file(self, xml_file: str):
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

    def get_mention_dictionary_from_dir(self, mention_dir: str):
        """
        Build a mapping from a document name to a list of mentions.
        Mentions are extracted from the given directory containing an xml file for each document.
        """
        self.mention_dictionary = dict()
        for xml_file in sorted(os.listdir(mention_dir)):
            file_path = os.path.join(mention_dir, xml_file)
            xml_tree = ElementTree.parse(file_path)
            root = xml_tree.getroot()
            reference_filename = ""
            curr_offset = -1
            curr_span = -1, -1
            for element in root.iter():
                if element.tag == 'ReferenceFileName':
                    reference_filename = element.text.strip()
                    self.mention_dictionary[reference_filename] = []
                elif element.tag == 'Annotation':
                    curr_entity = element.text.strip().strip('"').replace("_", " ")
                    curr_entity = curr_entity.replace("http://en.wikipedia.org/wiki/", "")
                    curr_entity = "NIL" if curr_entity in ["none", "---"] else curr_entity
                    self.mention_dictionary[reference_filename].append((curr_span, curr_entity))
                elif element.tag == 'Offset':
                    curr_offset = int(element.text.strip())
                elif element.tag == 'Length':
                    curr_length = int(element.text.strip())
                    curr_span = curr_offset, curr_offset + curr_length

    def article_iterator(self, xml_path: str, raw_text_dir: str) -> Iterator[WikipediaArticle]:
        """
        Yields for each document in the XML file and its corresponding
        document in the raw_text_dir a WikipediaArticle with labels.
        """
        if os.path.isdir(xml_path):
            self.get_mention_dictionary_from_dir(xml_path)
        else:
            self.get_mention_dictionary_from_file(xml_path)
        for filename in sorted(os.listdir(raw_text_dir)):
            file_path = os.path.join(raw_text_dir, filename)
            text = ''.join(open(file_path, "r", encoding="utf8").readlines())
            article = self.to_article(filename, text)
            yield article
