import json
import os
from typing import Optional, Tuple, Dict, Set, Any

from elevant.linkers.linkers import Linkers, CoreferenceLinkers, PredictionFormats
from elevant.models.article import Article
from elevant.models.entity_database import EntityDatabase, MappingName
from elevant import settings

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
                 min_score: Optional[int] = 0,
                 type_mapping_file: Optional[str] = settings.QID_TO_WHITELIST_TYPES_DB,
                 custom_kb: Optional[bool] = False):
        self.linker = None
        self.prediction_reader = None
        self.prediction_name = prediction_name
        self.coref_linker = None
        self.coref_prediction_iterator = None
        self.entity_db = None
        self.globally = False
        self.type_mapping_file = type_mapping_file  # Only needed for pure prior linker
        self.linker_config = self.read_linker_config(linker_name, config_path) if linker_name else {}
        self.custom_kb = custom_kb

        if custom_kb and prediction_format not in {PredictionFormats.NIF.value, PredictionFormats.SIMPLE_JSONL.value}:
            logger.warning(f"Using a custom knowledge base is not supported for linking result format "
                           f"{prediction_format}. Please choose a different format.")

        self._initialize_entity_db(linker_name, coref_linker, min_score)
        self._initialize_linker(linker_name, prediction_file, prediction_format)
        self._initialize_coref_linker(coref_linker)

    def _initialize_entity_db(self, linker_name: str, coref_linker: str, min_score: int):
        # Linkers for which not to load entities into the entity database
        # The Wikipedia2Wikidata mapping that might be loaded in _initialize_linker()
        # remains unaffected by this.
        no_db_linkers = (Linkers.TAGME.value, Linkers.DBPEDIA_SPOTLIGHT.value, Linkers.NONE.value,
                         Linkers.REFINED.value, Linkers.REL.value, Linkers.WAT.value, Linkers.SPACY.value,
                         Linkers.BABELFY.value, Linkers.GPT.value)

        self.entity_db = EntityDatabase()

        # When a prediction_file is given linker_name is None
        if coref_linker or (linker_name is not None and linker_name not in no_db_linkers):
            self.entity_db.load_all_entities_in_wikipedia(minimum_sitelink_count=min_score)
            self.entity_db.load_entity_types(self.type_mapping_file)
            self.entity_db.load_entity_names()

    @staticmethod
    def read_linker_config(linker_name: str, config_path: Optional[str] = None) -> Dict[str, Any]:
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

    def get_linker_config(self) -> Dict[str, Any]:
        return self.linker_config

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
            from elevant.linkers.spacy_linker import SpacyLinker
            self.linker = SpacyLinker(self.linker_config)
        elif linker_type == PredictionFormats.AMBIVERSE.value:
            from elevant.prediction_readers.ambiverse_prediction_reader import AmbiversePredictionReader
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS})
            self.prediction_reader = AmbiversePredictionReader(prediction_file, self.entity_db)
        elif linker_type == Linkers.TAGME.value:
            from elevant.linkers.tagme_linker import TagMeLinker
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS})
            self.linker = TagMeLinker(self.entity_db, self.linker_config)
        elif linker_type == PredictionFormats.SIMPLE_JSONL.value:
            from elevant.prediction_readers.simple_jsonl_prediction_reader import SimpleJsonlPredictionReader
            if not self.custom_kb:
                self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                            MappingName.REDIRECTS})
            self.prediction_reader = SimpleJsonlPredictionReader(prediction_file, self.entity_db, self.custom_kb)
        elif linker_type == Linkers.BASELINE.value:
            from elevant.linkers.baseline_linker import BaselineLinker
            if self.linker_config["strategy"] == "wikidata":
                self.load_missing_mappings({MappingName.WIKIDATA_ALIASES,
                                            MappingName.FAMILY_NAME_ALIASES,
                                            MappingName.SITELINKS})
            else:
                if self.linker_config["strategy"] != "wikipedia":
                    logger.info("Unknown strategy %s. Assuming strategy \"wikipedia\"" % self.linker_config["strategy"])
                self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                            MappingName.REDIRECTS,
                                            MappingName.HYPERLINK_TO_MOST_POPULAR_CANDIDATES,
                                            MappingName.FAMILY_NAME_ALIASES,
                                            MappingName.WIKIDATA_ALIASES})
            self.linker = BaselineLinker(self.entity_db, self.linker_config)
        elif linker_type == Linkers.POPULAR_ENTITIES.value:
            from elevant.linkers.popular_entities_linker import PopularEntitiesLinker
            self.load_missing_mappings({MappingName.FAMILY_NAME_ALIASES,
                                        MappingName.WIKIDATA_ALIASES,
                                        MappingName.LANGUAGES,
                                        MappingName.DEMONYMS,
                                        MappingName.SITELINKS,
                                        MappingName.NAME_TO_ENTITY_ID})
            self.linker = PopularEntitiesLinker(self.entity_db, self.linker_config)
            self.globally = True
        elif linker_type == PredictionFormats.WIKIFIER.value:
            from elevant.prediction_readers.wikifier_prediction_reader import WikifierPredictionReader
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS,
                                        MappingName.WIKIPEDIA_ID_WIKIPEDIA_TITLE})
            self.prediction_reader = WikifierPredictionReader(prediction_file, self.entity_db)
        elif linker_type == Linkers.POS_PRIOR.value:
            from elevant.linkers.prior_linker import PriorLinker
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS,
                                        MappingName.LINK_FREQUENCIES,
                                        MappingName.ENTITY_ID_TO_ALIAS,
                                        MappingName.ENTITY_ID_TO_FAMILY_NAME})
            self.linker = PriorLinker(self.entity_db, self.linker_config)
        elif linker_type == PredictionFormats.NIF.value:
            from elevant.prediction_readers.nif_prediction_reader import NifPredictionReader
            if not self.custom_kb:
                self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                            MappingName.REDIRECTS})
            self.prediction_reader = NifPredictionReader(prediction_file, self.entity_db, self.custom_kb)
        elif linker_type == PredictionFormats.EPGEL.value:
            from elevant.prediction_readers.epgel_prediction_reader import EPGELPredictionReader
            self.prediction_reader = EPGELPredictionReader(prediction_file)
        elif linker_type == Linkers.DBPEDIA_SPOTLIGHT.value:
            from elevant.linkers.dbpedia_spotlight_linker import DbpediaSpotlightLinker
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS})
            self.linker = DbpediaSpotlightLinker(self.entity_db, self.linker_config)
        elif linker_type == Linkers.REFINED.value:
            from elevant.linkers.refined_linker import RefinedLinker
            self.linker = RefinedLinker(self.linker_config)
        elif linker_type == Linkers.REL.value:
            from elevant.linkers.rel_linker import RelLinker
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS})
            self.linker = RelLinker(self.entity_db, self.linker_config)
        elif linker_type == Linkers.WAT.value:
            from elevant.linkers.wat_linker import WatLinker
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS})
            self.linker = WatLinker(self.entity_db, self.linker_config)
        elif linker_type == Linkers.GPT.value:
            from elevant.linkers.gpt_linker import GPTLinker
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS})
            self.linker = GPTLinker(self.entity_db, self.linker_config)
        elif linker_type == Linkers.BABELFY.value:
            from elevant.linkers.babelfy_linker import BabelfyLinker
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS})
            self.linker = BabelfyLinker(self.entity_db, self.linker_config)
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
        # Neuralcoref is outdated, see ELEVANT Github issue #5
        # if linker_type == CoreferenceLinkers.NEURALCOREF.value:
        #     from elevant.linkers.neuralcoref_coref_linker import NeuralcorefCorefLinker
        #     self.coref_linker = NeuralcorefCorefLinker()
        if linker_type == CoreferenceLinkers.ENTITY.value:
            from elevant.linkers.entity_coref_linker import EntityCorefLinker
            self.load_missing_mappings({MappingName.GENDER,
                                        MappingName.COREFERENCE_TYPES,
                                        MappingName.ENTITY_ID_TO_ALIAS})
            self.coref_linker = EntityCorefLinker(self.entity_db)
        elif linker_type == CoreferenceLinkers.STANFORD.value:
            from elevant.linkers.stanford_corenlp_coref_linker import StanfordCoreNLPCorefLinker
            self.coref_linker = StanfordCoreNLPCorefLinker()
        # elif linker_type == CoreferenceLinkers.XRENNER.value:
        #     from elevant.linkers.xrenner_coref_linker import XrennerCorefLinker
        #     self.coref_linker = XrennerCorefLinker()
        elif linker_type == CoreferenceLinkers.FASTCOREF.value:
            from elevant.linkers.fastcoref_coref_linker import FastcorefCorefLinker
            self.coref_linker = FastcorefCorefLinker()
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
            # This takes a lot of time, so if several components of the linking_system rely on the processed
            # document, only do this once. However, be aware the models of the different components might
            # differ slightly or have different pipeline components.
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
                                            doc,
                                            only_pronouns=only_pronouns,
                                            evaluation_span=coref_eval_span)
        elif self.coref_prediction_iterator:
            predicted_coref_entities = next(self.coref_prediction_iterator)
            article.link_entities(predicted_coref_entities, "PREDICTION_READER_COREF", "PREDICTION_READER_COREF")

    def load_missing_mappings(self, mappings: Set[MappingName]):
        if MappingName.WIKIPEDIA_WIKIDATA in mappings and not self.entity_db.is_wikipedia_to_wikidata_mapping_loaded():
            self.entity_db.load_wikipedia_to_wikidata_db()
        if MappingName.REDIRECTS in mappings and not self.entity_db.is_redirects_loaded():
            self.entity_db.load_redirects()
        if MappingName.LINK_FREQUENCIES in mappings and not self.entity_db.is_link_frequencies_loaded():
            self.entity_db.load_link_frequencies()

        # Alias mappings
        if MappingName.WIKIDATA_ALIASES in mappings and not self.entity_db.loaded_info.get(MappingName.WIKIDATA_ALIASES):
            self.entity_db.load_alias_to_entities()
        if MappingName.FAMILY_NAME_ALIASES in mappings and not self.entity_db.loaded_info.get(MappingName.FAMILY_NAME_ALIASES):
            self.entity_db.load_family_name_aliases()
        if MappingName.LINK_ALIASES in mappings and not self.entity_db.loaded_info.get(MappingName.LINK_ALIASES):
            self.entity_db.load_link_aliases()
        if MappingName.HYPERLINK_TO_MOST_POPULAR_CANDIDATES in mappings and not self.entity_db.loaded_info.get(MappingName.HYPERLINK_TO_MOST_POPULAR_CANDIDATES):
            self.entity_db.load_hyperlink_to_most_popular_candidates()

        # Inverse alias mappings
        if MappingName.ENTITY_ID_TO_ALIAS in mappings and not self.entity_db.loaded_info.get(MappingName.ENTITY_ID_TO_ALIAS):
            self.entity_db.load_entity_to_aliases()
        if MappingName.ENTITY_ID_TO_FAMILY_NAME in mappings and not self.entity_db.loaded_info.get(MappingName.ENTITY_ID_TO_FAMILY_NAME):
            self.entity_db.load_entity_to_family_name()
        if MappingName.ENTITY_ID_TO_LINK_ALIAS in mappings and not self.entity_db.loaded_info.get(MappingName.ENTITY_ID_TO_LINK_ALIAS):
            self.entity_db.load_entity_to_link_aliases()

        if MappingName.LANGUAGES in mappings and not self.entity_db.has_languages_loaded():
            self.entity_db.load_languages()
        if MappingName.DEMONYMS in mappings and not self.entity_db.has_demonyms_loaded():
            self.entity_db.load_demonyms()
        if MappingName.SITELINKS in mappings and not self.entity_db.has_sitelink_counts_loaded():
            self.entity_db.load_sitelink_counts()
        if MappingName.WIKIPEDIA_ID_WIKIPEDIA_TITLE in mappings and not self.entity_db.has_wikipedia_id2wikipedia_title_loaded():
            self.entity_db.load_wikipedia_id2wikipedia_title()
        if MappingName.NAME_TO_ENTITY_ID in mappings and not self.entity_db.loaded_info.get(MappingName.NAME_TO_ENTITY_ID):
            self.entity_db.load_name_to_entities()

        if MappingName.GENDER in mappings and not self.entity_db.is_gender_loaded():
            self.entity_db.load_gender()
        if MappingName.COREFERENCE_TYPES in mappings and not self.entity_db.is_coreference_types_loaded():
            self.entity_db.load_coreference_types()
