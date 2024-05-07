import logging
from typing import List, Tuple, Optional, Dict

import spacy
from spacy.tokens.doc import Doc

from elevant.models.entity_database import EntityDatabase, MappingName
from elevant.linkers.abstract_entity_linker import AbstractEntityLinker
from elevant.models.entity_prediction import EntityPrediction
from elevant.utils.dates import is_date

logger = logging.getLogger("main." + __name__.split(".")[-1])


def get_split_points(text: str) -> List[int]:
    return [-1] + [i for i, c in enumerate(text) if not c.isalnum()] + [len(text)]


def contains_uppercase(text: str) -> bool:
    return any(c.isupper() for c in text)


class MaximumMatchingNER(AbstractEntityLinker):
    def predict(self,
                text: str,
                doc: Optional[Doc] = None,
                uppercase: Optional[bool] = False) -> Dict[Tuple[int, int], EntityPrediction]:
        mention_spans = self.entity_mentions(text)
        if uppercase:
            predictions = {span: EntityPrediction(span, "Unknown", set()) for span in mention_spans
                           if not text[span[0]:span[1]].islower()}
        else:
            predictions = {span: EntityPrediction(span, "Unknown", set()) for span in mention_spans}
        return predictions

    def has_entity(self, entity_id: str) -> bool:
        return False

    def __init__(self, entity_db: EntityDatabase):
        logger.warning("Due to some restructuring of the entity database, the MaximumMatchingNER"
                       "currently takes a very long time for loading and should therefore not be"
                       "used without modifications.")
        logger.info("Loading necessary mappings for NER ...")
        if not entity_db.loaded_info.get(MappingName.FAMILY_NAME_ALIASES):
            entity_db.load_family_name_aliases()
        if not entity_db.loaded_info.get(MappingName.WIKIDATA_ALIASES):
            entity_db.load_alias_to_entities()
        if not entity_db.is_wikipedia_to_wikidata_mapping_loaded():
            entity_db.load_wikipedia_to_wikidata_db()
        if not entity_db.is_redirects_loaded():
            entity_db.load_redirects()
        if not entity_db.is_link_frequencies_loaded():
            entity_db.load_link_frequencies()
        if len(entity_db.unigram_counts) == 0:
            entity_db.load_unigram_counts()
        logger.info("Necessary mappings loaded.")
        model = spacy.load("en_core_web_sm")
        stopwords = model.Defaults.stop_words
        exclude = {"January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                   "November", "December", "The", "A", "An", "It"}
        remove_beginnings = {"a ", "an ", "the ", "in ", "at "}
        remove_ends = {"'s"}
        exclude_ends = {" the"}

        logger.info("Retrieving alias frequencies ...")
        self.alias_frequencies = {}
        # TODO: Aliases used to be stored in one central dictionary, but now they are stored in different dictionaries
        #       and databases. But this approach is super slow right now:
        for alias in list(entity_db.family_name_aliases.keys()) + list(entity_db.alias_to_entities_db.keys()) + list(entity_db.name_to_entities_db.keys()):
            ignore_alias = False
            if len(alias) == 0:
                continue
            lowercased = alias[0].lower() + alias[1:]
            for beginning in remove_beginnings:
                if lowercased.startswith(beginning):
                    if alias[0].islower() or entity_db.contains_alias(alias[len(beginning):]):
                        ignore_alias = True
                        break
            if not alias[-1].isalnum() and entity_db.contains_alias(alias[:-1]):
                continue
            if alias.isnumeric():
                continue
            if is_date(alias):
                continue
            if alias[0].islower():
                continue
            if entity_db.get_alias_frequency(alias) < entity_db.get_unigram_count(lowercased):
                continue
            for end in exclude_ends:
                if alias.endswith(end):
                    ignore_alias = True
                    break
            if ignore_alias:
                continue
            for end in remove_ends:
                if alias.endswith(end):
                    alias = alias[:-(len(end))]
                    break
            if lowercased not in stopwords and alias not in exclude and contains_uppercase(alias):
                alias_frequency = entity_db.get_alias_frequency(alias)
                if len(alias) > 1 and alias_frequency > 0:
                    self.alias_frequencies[alias] = alias_frequency
        self.max_len = 20
        self.model = None
        logger.info("%d alias frequencies retrieved." % len(self.alias_frequencies))

    def entity_mentions(self, text: str) -> List[Tuple[int, int]]:
        split_points = get_split_points(text)
        point_i = 0
        n_points = len(split_points)
        mention_spans = []
        while point_i < n_points - 1:
            start_point = split_points[point_i] + 1
            for length in reversed(range(1, min(self.max_len + 1, n_points - point_i))):
                end_point = split_points[point_i + length]
                if end_point > start_point:
                    snippet = text[start_point:end_point]
                    if snippet in self.alias_frequencies:
                        point_i += length - 1
                        mention_spans.append((start_point, end_point))
                        break
            point_i += 1
        return mention_spans

    def get_alias_frequency(self, alias: str) -> int:
        return self.alias_frequencies[alias] if alias in self.alias_frequencies else 0
