import numpy as np
from typing import Optional, Dict, Tuple, Iterator

import spacy
from spacy.tokens import Doc

import requests

from src.helpers.entity_database_reader import EntityDatabaseReader
from src.linkers.abstract_entity_linker import AbstractEntityLinker
from src.models.entity_database import EntityDatabase
from src.models.entity_prediction import EntityPrediction
from src import settings


QUERY = "PREFIX wdt: <http://www.wikidata.org/prop/direct/> " \
        "PREFIX wd: <http://www.wikidata.org/entity/> " \
        "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>" \
        "SELECT DISTINCT ?item WHERE " \
        "{ { ?item wdt:P31 ?type . " \
        "VALUES ?type { %s } } " \
        "UNION " \
        "{ ?item wdt:P31 ?m . ?m wdt:P279+ ?type . " \
        "VALUES ?type { %s } } }"


class PurePriorLinker(AbstractEntityLinker):
    LINKER_IDENTIFIER = "PurePrior"

    def __init__(self,
                 entity_database: EntityDatabase,
                 whitelist_type_file: str):
        self.entity_db = entity_database
        self.model = spacy.load(settings.LARGE_MODEL_NAME)
        self.max_tokens = 15
        self.whitelist_string = ""
        if whitelist_type_file:
            self.whitelist_string = self.get_whitelist(whitelist_type_file)
            self.entities_with_whitelist_type = set()
            self.retrieve_entity_types()

    def get_whitelist(self, whitelist_type_file: str):
        whitelist_str = ""
        types = EntityDatabaseReader.read_whitelist_types(whitelist_type_file)
        for typ in types:
            whitelist_str += "wd:" + typ + " "
        return whitelist_str

    def retrieve_entity_types(self):
        print("Retrieving entities with whitelist types from QLever...")
        query = QUERY % (self.whitelist_string, self.whitelist_string)
        print("Query: %s" % query)
        url = 'https://qlever.informatik.uni-freiburg.de/api/wikidata-proxy'
        data = {"query": query, "action": "tsv_export"}
        r = requests.get(url, params=data)
        if not r.text:
            print("Unable to retrieve type information from QLever. Link all types.")
        else:
            for i, entity_url in enumerate(r.text.split("\n")):
                entity_id = entity_url[len("<http://www.wikidata.org/entity/"):-1]
                if i == 0:
                    print("Extracted entity_id: %s" % entity_id)
                if entity_id == "Q10000001":
                    print("Entity ID properly extracted.")
                if self.entity_db.contains_entity(entity_id):
                    self.entities_with_whitelist_type.add(entity_id)
        print("Number of entities in the DB with a whitelist type: %d" % len(self.entities_with_whitelist_type))

    def has_entity(self, entity_id: str) -> bool:
        return self.entity_db.contains_entity(entity_id)

    def get_mention_spans(self, doc: Doc, text: str) -> Iterator[Tuple[Tuple[int, int], str]]:
        for n_tokens in range(self.max_tokens, 0, -1):
            for result in self.get_mention_spans_with_n_tokens(doc, text, n_tokens):
                yield result

    def get_mention_spans_with_n_tokens(self, doc: Doc, text: str, n_tokens: int) -> Iterator[Tuple[Tuple[int, int], str]]:
        mention_start = 0
        while mention_start + n_tokens < len(doc):
            span = doc[mention_start].idx, doc[mention_start + n_tokens].idx + len(doc[mention_start + n_tokens])
            mention_text = text[span[0]:span[1]]
            yield span, mention_text
            mention_start += 1

    def get_matching_entity_id(self, mention_text: str) -> Optional[str]:
        if mention_text in self.entity_db.link_frequencies:
            return max(self.entity_db.link_frequencies[mention_text], key=self.entity_db.link_frequencies[mention_text].get)

    def has_whitelist_type(self, entity_id: str) -> bool:
        entity_string = entity_id
        query = QUERY % (entity_string, self.whitelist_string, entity_string, self.whitelist_string)
        url = 'https://qlever.informatik.uni-freiburg.de/api/wikidata-proxy'
        data = {"query": query}
        r = requests.get(url, params=data)
        # print("Results for entity %s: %s" % (entity_id, r.json()))
        return True if r.json()["res"] else False

    def predict(self,
                text: str,
                doc: Optional[Doc] = None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        if doc is None:
            doc = self.model(text)

        predictions = {}
        annotated_chars = np.zeros(shape=len(text), dtype=bool)
        for span, mention_text in self.get_mention_spans(doc, text):
            if uppercase and mention_text.islower():
                continue
            predicted_entity_id = self.get_matching_entity_id(mention_text)
            if predicted_entity_id:
                # Do not allow overlapping links. Prioritize links with more tokens
                if np.sum(annotated_chars[span[0]:span[1]]) == 0:
                    if not self.entities_with_whitelist_type or predicted_entity_id in self.entities_with_whitelist_type:
                        annotated_chars[span[0]:span[1]] = True
                        candidates = {predicted_entity_id}
                        predictions[span] = EntityPrediction(span, predicted_entity_id, candidates)
        return predictions
