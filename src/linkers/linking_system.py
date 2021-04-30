from typing import Optional, Tuple, Dict

from src.helpers.neural_el_prediction_reader import NeuralELPredictionReader
from src.helpers.wexea_prediction_reader import WexeaPredictionReader
from src.linkers.alias_entity_linker import LinkingStrategy, AliasEntityLinker
from src.helpers.ambiverse_prediction_reader import AmbiversePredictionReader
from src.helpers.conll_iob_prediction_reader import ConllIobPredictionReader
from src.linkers.bert_entity_linker import BertEntityLinker
from src.linkers.entity_coref_linker import EntityCorefLinker
from src.linkers.linkers import Linkers, LinkLinkers, CoreferenceLinkers
from src.linkers.popular_entities_linker import PopularEntitiesLinker
from src.linkers.trained_entity_linker import TrainedEntityLinker
from src.models.entity_database import EntityDatabase
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
    def __init__(self, linker_type: str, linker: str, link_linker: str, coreference_linker: str, kb_name: str,
                 minimum_score: int, longest_alias_ner: bool):
        self.link_linker = None
        self.linker = None
        self.prediction_iterator = None
        self.coreference_linker = None
        self.coreference_prediction_iterator = None
        self.entity_db = None
        self.globally = False

        self._initialize_entity_db(linker_type, linker, link_linker, coreference_linker, minimum_score)
        self._initialize_link_linker(link_linker)
        self._initialize_linker(linker_type, linker, kb_name, longest_alias_ner)
        self._initialize_coref_linker(coreference_linker, linker)

    def _initialize_entity_db(self, linker_type: str, linker: str, link_linker: str, coreference_linker: str,
                              minimum_score: int):
        print("load entities...")
        self.entity_db = EntityDatabase()
        if not link_linker and not coreference_linker and ((linker_type == Linkers.BASELINE.value and linker == "max-match-ner")
                                                           or linker_type == Linkers.TAGME.value
                                                           or linker_type == Linkers.AMBIVERSE.value
                                                           or linker_type == Linkers.IOB.value):
            pass
        elif linker_type == Linkers.BASELINE.value and linker in ("scores", "links"):
            self.entity_db.load_entities_small(minimum_score)
        else:
            self.entity_db.load_entities_big()

        print(self.entity_db.size_entities(), "entities")
        if linker_type == Linkers.BASELINE.value:
            if linker == "max-match-ner":
                pass
            elif linker in ("links", "links-all"):
                print("load link frequencies...")
                self.entity_db.load_mapping()
                self.entity_db.load_redirects()
                self.entity_db.add_link_aliases()
                self.entity_db.load_link_frequencies()
            else:
                print("add synonyms...")
                self.entity_db.add_synonym_aliases()
                print(self.entity_db.size_aliases(), "aliases")
                print("add names...")
                self.entity_db.add_name_aliases()
                print(self.entity_db.size_aliases(), "aliases")

    def _initialize_linker(self, linker_type: str, linker_info: str, kb_name: Optional[str] = None,
                           longest_alias_ner: Optional[bool] = False):
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
            result_dir = linker_info
            self.prediction_iterator = AmbiversePredictionReader.article_predictions_iterator(result_dir)
        elif linker_type == Linkers.TAGME.value:
            rho_threshold = float(linker_info)
            self.linker = TagMeLinker(rho_threshold)
        elif linker_type == Linkers.WEXEA.value:
            result_dir = linker_info
            if not self.entity_db.is_mapping_loaded():
                print("Loading wikipedia-wikidata mapping...")
                self.entity_db.load_mapping()
            if not self.entity_db.is_redirects_loaded():
                print("Loading redirects...")
                self.entity_db.load_redirects()
            self.prediction_iterator = WexeaPredictionReader(self.entity_db).article_predictions_iterator(result_dir)
        elif linker_type == Linkers.NEURAL_EL.value:
            result_file = linker_info
            if not self.entity_db.is_mapping_loaded():
                print("Loading wikipedia-wikidata mapping...")
                self.entity_db.load_mapping()
            if not self.entity_db.is_redirects_loaded():
                print("Loading redirects...")
                self.entity_db.load_redirects()
            self.prediction_iterator = NeuralELPredictionReader(self.entity_db).\
                article_predictions_iterator(result_file)
        elif linker_type == Linkers.BASELINE.value:
            if linker_info == "max-match-ner":
                self.linker = MaximumMatchingNER()
            else:
                if linker_info not in ("links", "scores", "links-all"):
                    raise NotImplementedError("Unknown strategy '%s'." % linker_info)
                if linker_info in ("links", "links-all"):
                    strategy = LinkingStrategy.LINK_FREQUENCY
                else:
                    strategy = LinkingStrategy.ENTITY_SCORE
                self.linker = AliasEntityLinker(self.entity_db, strategy, load_model=not longest_alias_ner,
                                                longest_alias_ner=longest_alias_ner)
        elif linker_type == Linkers.TRAINED_MODEL.value:
            print("loading trained entity linking model...")
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
            if not self.entity_db.has_languages_loaded():
                print("Loading languages...")
                self.entity_db.load_languages()
            if not self.entity_db.has_demonyms_loaded():
                print("Loading demonyms...")
                self.entity_db.load_demonyms()
            if not self.entity_db.has_sitelink_counts_loaded():
                print("Loading sitelink counts...")
                self.entity_db.load_sitelink_counts()
            min_score = int(linker_info)
            self.linker = PopularEntitiesLinker(min_score, self.entity_db, longest_alias_ner)
            self.globally = True

    def _initialize_link_linker(self, linker_type: str):
        if not self.entity_db.is_mapping_loaded():
            self.entity_db.load_mapping()
        if not self.entity_db.is_redirects_loaded():
            self.entity_db.load_redirects()
        if linker_type == LinkLinkers.LINK_TEXT_LINKER.value:
            print("add synonyms...")
            self.entity_db.add_synonym_aliases()
            print(self.entity_db.size_aliases(), "aliases")
            print("add names...")
            self.entity_db.add_name_aliases()
            print(self.entity_db.size_aliases(), "aliases")
            self.link_linker = LinkTextEntityLinker(entity_db=self.entity_db)
        elif linker_type == LinkLinkers.LINK_LINKER.value:
            self.link_linker = LinkEntityLinker()

    def _initialize_coref_linker(self, linker_type: str, linker_info):
        if linker_type == CoreferenceLinkers.NEURALCOREF.value:
            self.coreference_linker = NeuralcorefCorefLinker()
        elif linker_type == CoreferenceLinkers.ENTITY.value:
            self.coreference_linker = EntityCorefLinker(entity_db=self.entity_db)
        elif linker_type == CoreferenceLinkers.STANFORD.value:
            self.coreference_linker = StanfordCoreNLPCorefLinker()
        elif linker_type == CoreferenceLinkers.XRENNER.value:
            self.coreference_linker = XrennerCorefLinker()
        elif linker_type == CoreferenceLinkers.HOBBS.value:
            self.coreference_linker = HobbsCorefLinker(entity_db=self.entity_db)
        elif linker_type == CoreferenceLinkers.WEXEA.value:
            result_dir = linker_info
            if not self.entity_db.is_mapping_loaded():
                print("Loading wikipedia-wikidata mapping...")
                self.entity_db.load_mapping()
            if not self.entity_db.is_redirects_loaded():
                print("Loading redirects...")
                self.entity_db.load_redirects()
            self.coreference_prediction_iterator = WexeaPredictionReader(self.entity_db)\
                .article_coref_predictions_iterator(result_dir)

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

        if self.coreference_linker:
            coref_eval_span = evaluation_span if evaluation_span else None
            self.coreference_linker.link_entities(article,
                                                  only_pronouns=only_pronouns,
                                                  evaluation_span=coref_eval_span)
        elif self.coreference_prediction_iterator:
            predicted_coref_entities = next(self.coreference_prediction_iterator)
            article.link_entities(predicted_coref_entities, "PREDICTION_READER_COREF", "PREDICTION_READER_COREF")
