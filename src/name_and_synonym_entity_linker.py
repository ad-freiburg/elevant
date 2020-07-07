from typing import Optional

from src.entity_database import EntityDatabase
from src.paragraph import Paragraph


def read_person_names(name_file: str):
    names = {}
    for line in open(name_file):
        url, encoded_names = line[:-1].split(">,")
        entity_id = parse_entity_id(url)
        entity_names = [parse_name(encoded) for encoded in encoded_names.split("@en,")]
        names[entity_id] = entity_names
    return names


class NameAndSynonymEntityLinker:
    NAME_IDENTIFIER = "NAME"
    SYNONYM_IDENTIFIER = "SYNONYM"

    def __init__(self,
                 entity_database: EntityDatabase,
                 person_name_file: Optional[str]):
        # TODO: use person names
        self.entity_db = entity_database
        self.names = {} # if person_name_file is None else read_person_names(person_name_file, entity_database)
        self.synonyms = {}
        for entity in self.entity_db.all_entities():
            name = entity.name
            if name not in self.names or entity.score > self.entity_db.get_score(self.names[name]):
                self.names[name] = entity.entity_id
            for synonym in entity.synonyms:
                if synonym not in self.synonyms or entity.score > self.entity_db.get_score(self.synonyms[synonym]):
                    self.synonyms[synonym] = entity.entity_id
        print(len(self.names), "entity names")
        print(len(self.synonyms), "synonyms")
        self.linked_by_name = 0
        self.linked_by_synonym = 0

    def link_entities(self, paragraph: Paragraph):
        for mention in paragraph.entity_mentions:
            if not mention.is_linked():
                begin, end = mention.span
                if begin >= end:
                    continue
                snippet = paragraph.text[begin:end]
                # check if the text snippet (or a part of it) matches the known entity names:
                test_snippets = [snippet]
                starts_with_the = ends_with_punctuation = False
                if snippet.startswith("the ") or snippet.startswith("The "):
                    test_snippets.append(snippet[4:])
                    starts_with_the = True
                if not snippet[-1].isalnum():
                    test_snippets.append(snippet[:-1])
                    ends_with_punctuation = True
                if starts_with_the and ends_with_punctuation:
                    test_snippets.append(snippet[4:-1])
                for test_snippet in test_snippets:
                    if test_snippet in self.names:
                        mention.link(self.names[test_snippet], self.NAME_IDENTIFIER)
                        self.linked_by_name += 1
                        break
                    elif test_snippet in self.synonyms:
                        mention.link(self.synonyms[test_snippet], self.SYNONYM_IDENTIFIER)
                        self.linked_by_synonym += 1
                        break
