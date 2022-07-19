import json
import os
from typing import Optional, Tuple, Dict, Set, Any

from src.linkers.dbpedia_spotlight_linker import DbpediaSpotlightLinker
from src.prediction_readers.simple_jsonl_prediction_reader import SimpleJsonlPredictionReader
from src.prediction_readers.nif_prediction_reader import NifPredictionReader
from src.prediction_readers.wikifier_prediction_reader import WikifierPredictionReader
from src.prediction_readers.ambiverse_prediction_reader import AmbiversePredictionReader
from src.linkers.baseline_linker import BaselineLinker
from src.linkers.bert_linker import BertLinker
from src.linkers.entity_coref_linker import EntityCorefLinker
from src.linkers.linkers import Linkers, CoreferenceLinkers, PredictionFormats
from src.linkers.popular_entities_linker import PopularEntitiesLinker
from src.linkers.prior_linker import PriorLinker
from src.linkers.explosion_linker import ExplosionEntityLinker
from src.linkers.neuralcoref_coref_linker import NeuralcorefCorefLinker
from src.linkers.stanford_corenlp_coref_linker import StanfordCoreNLPCorefLinker
from src.linkers.tagme_linker import TagMeLinker
from src.linkers.spacy_linker import SpacyLinker
from src.linkers.xrenner_coref_linker import XrennerCorefLinker
from src.models.article import Article
from src.models.entity_database import EntityDatabase, MappingName

import logging

logger = logging.getLogger("main." + __name__.split(".")[-1])


class LinkingSystem:
    def __init__(self,
                 linker_name: Optional[str] = None,
                 config_path: Optional[str] = None,
                 prediction_file: Optional[str] = None,
                 prediction_format: Optional[str] = None,
                 prediction_name: Optional[str] = None,
                 coref_linker: Optional[str] = None,
                 min_score: Optional[int] = None,
                 type_mapping_file: Optional[str] = None):
        self.linker = None
        self.prediction_reader = None
        self.prediction_name = prediction_name
        self.coref_linker = None
        self.coref_prediction_iterator = None
        self.entity_db = None
        self.globally = False
        self.type_mapping_file = type_mapping_file  # Only needed for pure prior linker
        self.linker_config = None
        self.linker_config = self.get_linker_config(linker_name, config_path) if linker_name else None

        self._initialize_entity_db(linker_name, coref_linker, min_score)
        self._initialize_linker(linker_name, prediction_file, prediction_format)
        self._initialize_coref_linker(coref_linker)

    def _initialize_entity_db(self, linker_name: str, coref_linker: str, min_score: int):
        # Linkers for which not to load entities into the entity database
        no_db_linkers = (Linkers.TAGME.value, Linkers.DBPEDIA_SPOTLIGHT.value, Linkers.NONE.value)

        self.entity_db = EntityDatabase()

        # When a prediction_file is given linker_name is None
        if coref_linker or (linker_name is not None and linker_name not in no_db_linkers):
            self.entity_db.load_all_entities_in_wikipedia(minimum_sitelink_count=min_score,
                                                          type_mapping=self.type_mapping_file)

    @staticmethod
    def get_linker_config(linker_name: str, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Get config dictionary for the specified linker or config path.
        """
        if not config_path:
            # Generate default config path for linker if no config path was provided
            config_path = "configs/" + str(linker_name) + ".config.json"

        if not os.path.exists(config_path):
            # Return empty config if no config file was found
            logger.info("No config file found for linker %s. No config loaded." % linker_name)
            return {}
        else:
            logger.info("Loading config file %s for linker %s." % (config_path, linker_name))
            with open(config_path, "r", encoding="utf8") as file:
                linker_config = json.load(file)
            return linker_config

    def _initialize_linker(self, linker_name: str, prediction_file: str, prediction_format: str):
        if linker_name:
            logger.info("Initializing linker %s with config parameters %s ..." % (linker_name, self.linker_config))
            linker_type = linker_name

        else:
            logger.info("Initializing prediction reader for file %s in format %s ..." %
                        (prediction_file, prediction_format))
            linker_type = prediction_format

        linker_exists = True

        if linker_type == Linkers.SPACY.value:
            self.linker = SpacyLinker(self.entity_db, self.linker_config)
        elif linker_type == Linkers.EXPLOSION.value:
            self.linker = ExplosionEntityLinker(self.entity_db, self.linker_config)
        elif linker_type == PredictionFormats.AMBIVERSE.value:
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS})
            self.prediction_reader = AmbiversePredictionReader(prediction_file, self.entity_db)
        elif linker_type == Linkers.TAGME.value:
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS})
            self.linker = TagMeLinker(self.entity_db, self.linker_config)
        elif linker_type == PredictionFormats.SIMPLE_JSONL.value:
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS})
            self.prediction_reader = SimpleJsonlPredictionReader(prediction_file, self.entity_db)
        elif linker_type == Linkers.BASELINE.value:
            if self.linker_config["strategy"] == "wikidata":
                self.load_missing_mappings({MappingName.WIKIDATA_ALIASES,
                                            MappingName.NAME_ALIASES,
                                            MappingName.SITELINKS})
            else:
                if self.linker_config["strategy"] != "wikipedia":
                    logger.info("Unknown strategy %s. Assuming strategy \"wikipedia\"" % self.linker_config["strategy"])
                self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                            MappingName.REDIRECTS,
                                            MappingName.LINK_ALIASES,
                                            MappingName.LINK_FREQUENCIES,
                                            MappingName.NAME_ALIASES,
                                            MappingName.WIKIDATA_ALIASES})
            self.linker = BaselineLinker(self.entity_db, self.linker_config)
        elif linker_type == Linkers.BERT_MODEL.value:
            self.linker = BertLinker(self.entity_db, self.linker_config)
        elif linker_type == Linkers.POPULAR_ENTITIES.value:
            min_score = self.linker_config["min_score"]
            self.load_missing_mappings({MappingName.NAME_ALIASES,
                                        MappingName.WIKIDATA_ALIASES,
                                        MappingName.LANGUAGES,
                                        MappingName.DEMONYMS,
                                        MappingName.SITELINKS}, min_score)
            self.linker = PopularEntitiesLinker(self.entity_db, self.linker_config)
            self.globally = True
        elif linker_type == PredictionFormats.WIKIFIER.value:
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS,
                                        MappingName.WIKIPEDIA_ID_WIKIPEDIA_TITLE})
            self.prediction_reader = WikifierPredictionReader(prediction_file, self.entity_db)
        elif linker_type == Linkers.POS_PRIOR.value:
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS,
                                        MappingName.LINK_FREQUENCIES,
                                        MappingName.NAME_ALIASES,
                                        MappingName.WIKIDATA_ALIASES})
            self.linker = PriorLinker(self.entity_db, self.linker_config)
        elif linker_type == PredictionFormats.NIF.value:
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS})
            self.prediction_reader = NifPredictionReader(prediction_file, self.entity_db)
        elif linker_type == Linkers.DBPEDIA_SPOTLIGHT.value:
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS})
            self.linker = DbpediaSpotlightLinker(self.entity_db, self.linker_config)
        else:
            linker_exists = False

        if self.prediction_reader and self.prediction_name:
            # Set the name of the linker
            self.prediction_reader.set_linker_identifier(self.prediction_name)

        if linker_exists:
            logger.info("-> Linker initialized.")
        else:
            logger.info("Linker type not found or not specified.")

    def _initialize_coref_linker(self, linker_type: str):
        logger.info("Initializing coref linker %s ..." % linker_type)
        linker_exists = True
        if linker_type == CoreferenceLinkers.NEURALCOREF.value:
            self.coref_linker = NeuralcorefCorefLinker()
        elif linker_type == CoreferenceLinkers.ENTITY.value:
            self.load_missing_mappings({MappingName.GENDER,
                                        MappingName.COREFERENCE_TYPES})
            self.coref_linker = EntityCorefLinker(self.entity_db)
        elif linker_type == CoreferenceLinkers.STANFORD.value:
            self.coref_linker = StanfordCoreNLPCorefLinker()
        elif linker_type == CoreferenceLinkers.XRENNER.value:
            self.coref_linker = XrennerCorefLinker()
        else:
            linker_exists = False

        if linker_exists:
            logger.info("-> Coref linker initialized.")
        else:
            logger.info("Coref linker type not found or not specified.")

    def link_entities(self,
                      article: Article,
                      uppercase: Optional[bool] = False,
                      only_pronouns: Optional[bool] = False,
                      evaluation_span: Optional[Tuple[int, int]] = None):
        if self.linker and self.linker.model:
            doc = self.linker.model(article.text)
        else:
            doc = None

        if self.linker:
            self.linker.link_entities(article, doc, uppercase=uppercase, globally=self.globally)
        elif self.prediction_reader:
            self.prediction_reader.link_entities(article, uppercase=uppercase)

        if self.coref_linker:
            coref_eval_span = evaluation_span if evaluation_span else None
            self.coref_linker.link_entities(article,
                                            only_pronouns=only_pronouns,
                                            evaluation_span=coref_eval_span)
        elif self.coref_prediction_iterator:
            predicted_coref_entities = next(self.coref_prediction_iterator)
            article.link_entities(predicted_coref_entities, "PREDICTION_READER_COREF", "PREDICTION_READER_COREF")

    def load_missing_mappings(self, mappings: Set[MappingName], min_count: Optional[int] = 1):
        if MappingName.WIKIPEDIA_WIKIDATA in mappings and not self.entity_db.is_wikipedia_wikidata_mapping_loaded():
            self.entity_db.load_wikipedia_wikidata_mapping()
        if MappingName.REDIRECTS in mappings and not self.entity_db.is_redirects_loaded():
            self.entity_db.load_redirects()
        if MappingName.LINK_FREQUENCIES in mappings and not self.entity_db.is_link_frequencies_loaded():
            self.entity_db.load_link_frequencies()

        # Alias mappings
        if MappingName.NAME_ALIASES in mappings and not self.entity_db.loaded_info.get(MappingName.NAME_ALIASES):
            self.entity_db.add_name_aliases()
        if MappingName.WIKIDATA_ALIASES in mappings and not self.entity_db.loaded_info.get(MappingName.WIKIDATA_ALIASES):
            self.entity_db.add_wikidata_aliases()
        if MappingName.LINK_ALIASES in mappings and not self.entity_db.loaded_info.get(MappingName.LINK_ALIASES):
            self.entity_db.add_link_aliases()
        if MappingName.NAMES in mappings and not self.entity_db.is_names_loaded():
            self.entity_db.load_names()
        if MappingName.TITLE_SYNONYMS in mappings and not self.entity_db.is_title_synonyms_loaded():
            self.entity_db.load_title_synonyms()
        if MappingName.AKRONYMS in mappings and not self.entity_db.is_akronyms_loaded():
            self.entity_db.load_akronyms()

        if MappingName.LANGUAGES in mappings and not self.entity_db.has_languages_loaded():
            self.entity_db.load_languages()
        if MappingName.DEMONYMS in mappings and not self.entity_db.has_demonyms_loaded():
            self.entity_db.load_demonyms()
        if MappingName.SITELINKS in mappings and not self.entity_db.has_sitelink_counts_loaded():
            self.entity_db.load_sitelink_counts(min_count=min_count)
        if MappingName.WIKIPEDIA_ID_WIKIPEDIA_TITLE in mappings and not self.entity_db.has_wikipedia_id2wikipedia_title_loaded():
            self.entity_db.load_wikipedia_id2wikipedia_title()

        if MappingName.GENDER in mappings and not self.entity_db.is_gender_loaded():
            self.entity_db.load_gender()
        if MappingName.COREFERENCE_TYPES in mappings and not self.entity_db.is_coreference_types_loaded():
            self.entity_db.load_coreference_types()
