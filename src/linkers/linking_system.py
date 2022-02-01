from typing import Optional, Tuple, Dict, Set

from src.helpers.neural_el_prediction_reader import NeuralELPredictionReader
from src.helpers.wexea_prediction_reader import WexeaPredictionReader
from src.helpers.wikifier_prediction_reader import WikifierPredictionReader
from src.linkers.alias_entity_linker import LinkingStrategy, AliasEntityLinker
from src.helpers.ambiverse_prediction_reader import AmbiversePredictionReader
from src.helpers.conll_iob_prediction_reader import ConllIobPredictionReader
from src.linkers.bert_entity_linker import BertEntityLinker
from src.linkers.entity_coref_linker import EntityCorefLinker
from src.linkers.linkers import Linkers, LinkLinkers, CoreferenceLinkers
from src.linkers.popular_entities_linker import PopularEntitiesLinker
from src.linkers.prior_linker import PriorLinker
from src.linkers.trained_entity_linker import TrainedEntityLinker
from src.models.entity_database import EntityDatabase, MappingName
from src.models.entity_prediction import EntityPrediction
from src.linkers.explosion_linker import ExplosionEntityLinker
from src.linkers.hobbs_coref_linker import HobbsCorefLinker
from src.linkers.link_entity_linker import LinkEntityLinker
from src.linkers.link_text_entity_linker import LinkTextEntityLinker
from src.ner.maximum_matching_ner import MaximumMatchingNER
from src.linkers.neuralcoref_coref_linker import NeuralcorefCorefLinker
from src.linkers.stanford_corenlp_coref_linker import StanfordCoreNLPCorefLinker
from src.linkers.tagme_linker import TagMeLinker
from src.linkers.trained_spacy_entity_linker import TrainedSpacyEntityLinker
from src.models.wikipedia_article import WikipediaArticle
from src.linkers.xrenner_coref_linker import XrennerCorefLinker

import torch
import logging

logger = logging.getLogger("main." + __name__.split(".")[-1])


def uppercase_predictions(predictions: Dict[Tuple[int, int], EntityPrediction],
                          text: str) -> Dict[Tuple[int, int], EntityPrediction]:
    filtered_predictions = {}
    for span in predictions:
        entity_prediction = predictions[span]
        begin, end = entity_prediction.span
        snippet = text[begin:end]
        if any([char.isupper() for char in snippet]):
            filtered_predictions[span] = entity_prediction
    return filtered_predictions


class LinkingSystem:
    def __init__(self, linker_type: str, linker: str, link_linker: str, coref_linker: str, kb_name: str, min_score: int,
                 longest_alias_ner: bool, type_mapping_file: str):
        self.link_linker = None
        self.linker = None
        self.prediction_iterator = None
        self.coref_linker = None
        self.coref_prediction_iterator = None
        self.entity_db = None
        self.globally = False
        self.type_mapping_file = type_mapping_file  # Only needed for pure prior linker

        self._initialize_entity_db(linker_type, linker, link_linker, coref_linker, min_score)
        self._initialize_link_linker(link_linker)
        self._initialize_linker(linker_type, linker, kb_name, longest_alias_ner)
        self._initialize_coref_linker(coref_linker, linker)

    def _initialize_entity_db(self, linker_type: str, linker: str, link_linker: str, coref_linker: str, min_score: int):
        # Linkers for which not to load entities into the entity database
        no_db_linkers = (Linkers.TAGME.value, Linkers.AMBIVERSE.value, Linkers.IOB.value, Linkers.NONE.value)

        self.entity_db = EntityDatabase()

        if linker_type == Linkers.BASELINE.value and linker in ("scores", "links"):
            # Note that this affects also a potential link_linker's and coreference_linker's entity database
            self.entity_db.load_entities_small(min_score)
        elif link_linker or coref_linker or not ((linker_type == Linkers.BASELINE.value and
                                                  linker == "max-match-ner") or linker_type in no_db_linkers):
            self.entity_db.load_entities_big(self.type_mapping_file)

    def _initialize_linker(self, linker_type: str, linker_info: str, kb_name: Optional[str] = None,
                           longest_alias_ner: Optional[bool] = False):
        logger.info("Initializing linker %s with parameter %s ..." % (linker_type, linker_info))

        linker_exists = True

        if linker_type == Linkers.SPACY.value:
            linker_name = linker_info
            self.linker = TrainedSpacyEntityLinker(linker_name, entity_db=self.entity_db, kb_name=kb_name)
        elif linker_type == Linkers.EXPLOSION.value:
            path = linker_info
            self.linker = ExplosionEntityLinker(path, entity_db=self.entity_db)
        elif linker_type == Linkers.IOB.value:
            path = linker_info
            self.prediction_iterator = ConllIobPredictionReader.document_predictions_iterator(path)
        elif linker_type == Linkers.AMBIVERSE.value:
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS})
            result_dir = linker_info
            self.prediction_iterator = AmbiversePredictionReader(self.entity_db).\
                article_predictions_iterator(result_dir)
        elif linker_type == Linkers.TAGME.value:
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS})
            rho_threshold = float(linker_info)
            self.linker = TagMeLinker(self.entity_db, rho_threshold)
        elif linker_type == Linkers.WEXEA.value:
            result_dir = linker_info
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS})
            self.prediction_iterator = WexeaPredictionReader(self.entity_db).article_predictions_iterator(result_dir)
        elif linker_type == Linkers.NEURAL_EL.value:
            result_file = linker_info
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS})
            self.prediction_iterator = NeuralELPredictionReader(self.entity_db).\
                article_predictions_iterator(result_file)
        elif linker_type == Linkers.BASELINE.value:
            if linker_info not in ("links", "scores", "links-all", "max-match-ner"):
                raise NotImplementedError("Unknown strategy '%s'." % linker_info)
            if linker_info == "max-match-ner":
                self.linker = MaximumMatchingNER(self.entity_db)
            if linker_info in ("links", "links-all"):
                self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                            MappingName.REDIRECTS,
                                            MappingName.LINK_ALIASES,
                                            MappingName.LINK_FREQUENCIES})
                strategy = LinkingStrategy.LINK_FREQUENCY
            else:
                self.load_missing_mappings({MappingName.WIKIDATA_ALIASES,
                                            MappingName.NAME_ALIASES})
                strategy = LinkingStrategy.ENTITY_SCORE
            self.linker = AliasEntityLinker(self.entity_db, strategy, load_model=not longest_alias_ner,
                                            longest_alias_ner=longest_alias_ner)
        elif linker_type == Linkers.TRAINED_MODEL.value:
            logger.info("Loading trained entity linking model...")
            linker_model_path = linker_info
            model_dict = torch.load(linker_model_path)
            prior = model_dict.get('prior', False)
            global_model = model_dict.get('global_model', False)
            rdf2vec = model_dict.get('rdf2vec', False)
            linker_model = model_dict['model']
            self.linker = TrainedEntityLinker(linker_model, self.entity_db, prior=prior, global_model=global_model,
                                              rdf2vec=rdf2vec)
        elif linker_type == Linkers.BERT_MODEL.value:
            self.linker = BertEntityLinker(linker_info, self.entity_db)
        elif linker_type == Linkers.POPULAR_ENTITIES.value:
            min_count = int(linker_info)
            self.load_missing_mappings({MappingName.NAME_ALIASES,
                                        MappingName.WIKIDATA_ALIASES,
                                        MappingName.LANGUAGES,
                                        MappingName.DEMONYMS,
                                        MappingName.SITELINKS},min_count)
            self.linker = PopularEntitiesLinker(min_count, self.entity_db, longest_alias_ner)
            self.globally = True
        elif linker_type == Linkers.WIKIFIER.value:
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS,
                                        MappingName.WIKIPEDIA_ID_WIKIPEDIA_TITLE})
            result_dir = linker_info
            self.prediction_iterator = WikifierPredictionReader(self.entity_db).article_predictions_iterator(result_dir)
        elif linker_type == Linkers.PURE_PRIOR.value or linker_type == Linkers.POS_PRIOR.value:
            whitelist_file = linker_info
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS,
                                        MappingName.LINK_FREQUENCIES,
                                        MappingName.NAME_ALIASES,
                                        MappingName.WIKIDATA_ALIASES})
            self.linker = PriorLinker(self.entity_db, whitelist_file, use_pos=linker_type == Linkers.POS_PRIOR.value)
        else:
            linker_exists = False

        if linker_exists:
            logger.info("-> Linker initialized.")
        else:
            logger.info("Linker type not found or not specified.")

    def _initialize_link_linker(self, linker_type: str):
        logger.info("Initializing link linker %s ..." % linker_type)
        linker_exists = True
        if linker_type == LinkLinkers.LINK_TEXT_LINKER.value:
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS,
                                        MappingName.WIKIDATA_ALIASES,
                                        MappingName.NAME_ALIASES,
                                        MappingName.NAMES,
                                        MappingName.TITLE_SYNONYMS,
                                        MappingName.AKRONYMS})
            self.link_linker = LinkTextEntityLinker(self.entity_db)
        elif linker_type == LinkLinkers.LINK_LINKER.value:
            self.link_linker = LinkEntityLinker()
        else:
            linker_exists = False

        if linker_exists:
            logger.info("-> Link linker initialized.")
        else:
            logger.info("Link linker type not found or not specified.")

    def _initialize_coref_linker(self, linker_type: str, linker_info: str):
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
        elif linker_type == CoreferenceLinkers.HOBBS.value:
            self.coref_linker = HobbsCorefLinker(self.entity_db)
        elif linker_type == CoreferenceLinkers.WEXEA.value:
            result_dir = linker_info
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS})
            self.coref_prediction_iterator = WexeaPredictionReader(self.entity_db)\
                .article_coref_predictions_iterator(result_dir)
        else:
            linker_exists = False

        if linker_exists:
            logger.info("-> Coref linker initialized.")
        else:
            logger.info("Coref linker type not found or not specified.")

    def link_entities(self,
                      article: WikipediaArticle,
                      uppercase: Optional[bool] = False,
                      only_pronouns: Optional[bool] = False,
                      evaluation_span: Optional[Tuple[int, int]] = None):
        if self.linker and self.linker.model:
            doc = self.linker.model(article.text)
        else:
            doc = None

        if self.link_linker:
            self.link_linker.link_entities(article, doc)

        if self.linker:
            self.linker.link_entities(article, doc, uppercase=uppercase, globally=self.globally)
        elif self.prediction_iterator:
            predicted_entities = next(self.prediction_iterator)
            if uppercase:
                predicted_entities = uppercase_predictions(predicted_entities, article.text)
            article.link_entities(predicted_entities, "PREDICTION_READER", "PREDICTION_READER")

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
