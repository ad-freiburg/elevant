import logging
from typing import List, Set, Optional, Dict, Tuple

from src import settings
from src.evaluation.case import Case, ErrorLabel
from src.evaluation.coreference_groundtruth_generator import CoreferenceGroundtruthGenerator
from src.evaluation.case_generator import CaseGenerator
from src.evaluation.groundtruth_label import GroundtruthLabel
from src.evaluation.mention_type import is_named_entity
from src.helpers.entity_database_reader import EntityDatabaseReader
from src.models.entity_database import EntityDatabase
from src.models.article import Article
from src.evaluation.errors import label_errors

logger = logging.getLogger("main." + __name__.split(".")[-1])


def load_evaluation_entities(relevant_entity_ids: Set[str], type_mapping_file: str) -> EntityDatabase:
    logger.info("Initializing entity database for evaluation ...")
    entity_db = EntityDatabase()
    mapping = EntityDatabaseReader.get_wikipedia_to_wikidata_mapping()
    mapping_entity_ids = set(mapping.values())
    relevant_entity_ids.update(mapping_entity_ids)
    entity_db.load_sitelink_counts()
    entity_db.load_entities(relevant_entity_ids, type_mapping=type_mapping_file)
    entity_db.load_wikipedia_wikidata_mapping()
    entity_db.load_redirects()
    entity_db.load_demonyms()
    entity_db.load_quantities()
    entity_db.load_datetimes()
    entity_db.add_name_aliases()
    entity_db.add_wikidata_aliases()
    entity_db.add_link_aliases()
    logger.info("-> Entity database initialized.")
    return entity_db


def percentage(nominator: int, denominator: int) -> Tuple[float, int, int]:
    if denominator == 0:
        percent = 0
    else:
        percent = nominator / denominator * 100
    return percent, nominator, denominator


def create_f1_dict(tp: int, fp: int, fn: int) -> Dict:
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    ground_truth = tp + fn
    recall = tp / ground_truth if ground_truth > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "ground_truth": ground_truth,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }


def create_f1_dict_from_counts(counts: Dict):
    return create_f1_dict(counts["tp"], counts["fp"], counts["fn"])


EVALUATION_CATEGORIES = ("all", "NER", "entity", "entity_named", "entity_other", "coref", "coref_nominal", "coref_pronominal")


class Evaluator:
    def __init__(self,
                 relevant_entity_ids: Set[str],
                 type_mapping_file: Optional[str],
                 whitelist_file: Optional[str] = settings.WHITELIST_FILE,
                 load_data: bool = True,
                 coreference: bool = True,
                 contains_unknowns: bool = True):
        self.whitelist_types = EntityDatabaseReader.read_whitelist_types(whitelist_file, with_adjustments=True)
        self.all_cases = []
        if load_data:
            self.entity_db = load_evaluation_entities(relevant_entity_ids, type_mapping_file)
        self.case_generator = CaseGenerator(self.entity_db)
        self.data_loaded = load_data
        self.coreference = coreference
        self.contains_unknowns = contains_unknowns
        self.counts = {}
        for key in EVALUATION_CATEGORIES:
            self.counts[key] = {"tp": 0, "fp": 0, "fn": 0}
        self.error_counts = {label: 0 for label in ErrorLabel}
        self.type_counts = {GroundtruthLabel.OTHER: {"tp": 0, "fp": 0, "fn": 0}}
        for type_id in self.whitelist_types:
            self.type_counts[type_id] = {"tp": 0, "fp": 0, "fn": 0}
        self.has_candidates = False
        self.n_entity_lowercase = 0
        self.n_entity_contains_space = 0

    def add_cases(self, cases: List[Case]):
        self.all_cases.extend(cases)
        for case in cases:
            self.count_ner_case(case)
            self.count_mention_type_case(case)
            self.count_error_labels(case)
            if len(case.candidates) > 1:
                self.has_candidates = True
            if case.is_not_coreference() and case.has_ground_truth() and ' ' in case.text:
                self.n_entity_contains_space += 1

    def count_ner_case(self, case: Case):
        if case.is_not_coreference():
            # Disregard child GT labels for TP and FN
            if case.has_ground_truth() and case.is_known_entity() and not case.is_optional() and case.true_entity.parent is None:
                if case.children_correctly_detected is True:
                    self.counts["NER"]["tp"] += 1
                elif case.children_correctly_detected is False:
                    self.counts["NER"]["fn"] += 1
                if not is_named_entity(case.text):
                    self.n_entity_lowercase += 1
            elif not case.has_ground_truth() or (not case.is_known_entity() and case.predicted_entity is not None):
                # Don't use case.has_predicted_entity() here, because this is false for NIL predictions,
                # but NIL predictions should not be ignored when evaluating NER.
                # TODO: shouldn't case.has_predicted_entity() be outside the brackets?
                # If case has no GT or if GT entity is unknown, the case has a predicted entity -> FP
                # otherwise ignore the case (NIL-entities are not expected to be predicted and should not count towards
                # errors)
                self.counts["NER"]["fp"] += 1

    def count_mention_type_case(self, case: Case):
        key = case.mention_type.value.lower()
        # Disregard child labels for TP and FN (case.is_correct() is also true if all child labels are linked correctly)
        # Parent could be 0 so check explicitly if parent is None.
        if case.is_correct() and not case.is_optional() and case.true_entity.parent is None:
            self.counts["all"]["tp"] += 1
            self.counts[key]["tp"] += 1

            if case.is_coreference():
                self.counts["coref"]["tp"] += 1
            else:
                type_ids = case.true_entity.type
                type_ids = type_ids.split("|")
                for type_id in type_ids:
                    self.type_counts[type_id]["tp"] += 1

        else:
            if case.is_false_positive() and not case.is_true_quantity_or_datetime() and case.factor != 0:
                self.counts["all"]["fp"] += 1
                self.counts[key]["fp"] += 1

                if case.is_coreference():
                    self.counts["coref"]["fp"] += 1
                else:
                    pred_entity_id = case.predicted_entity.entity_id
                    if self.entity_db.contains_entity(pred_entity_id):
                        type_ids = self.entity_db.get_entity(pred_entity_id).type.split("|")
                    else:
                        type_ids = [GroundtruthLabel.OTHER]
                    for type_id in type_ids:
                        self.type_counts[type_id]["fp"] += 1

            if case.is_false_negative() and not case.is_optional() and case.true_entity.parent is None:
                self.counts["all"]["fn"] += 1
                self.counts[key]["fn"] += 1

                if case.is_coreference():
                    self.counts["coref"]["fn"] += 1
                else:
                    type_ids = case.true_entity.type
                    type_ids = type_ids.split("|")
                    for type_id in type_ids:
                        self.type_counts[type_id]["fn"] += 1

    def count_error_labels(self, case: Case):
        for label in case.error_labels:
            self.error_counts[label] += case.factor  # factor is 0 or 1

    def get_cases(self, article: Article):
        if not self.data_loaded:
            raise Exception("Cannot call Evaluator.get_cases() when the evaluator was created with load_data=False.")
        coref_ground_truth = CoreferenceGroundtruthGenerator.get_groundtruth(article)

        cases = self.case_generator.get_evaluation_cases(article, coref_ground_truth)

        label_errors(article, cases, self.entity_db, contains_unknowns=self.contains_unknowns)

        return cases

    def get_results_dict(self):
        self.counts["entity"]["tp"] = self.counts["entity_named"]["tp"] + self.counts["entity_other"]["tp"]
        self.counts["entity"]["fp"] = self.counts["entity_named"]["fp"] + self.counts["entity_other"]["fp"]
        self.counts["entity"]["fn"] = self.counts["entity_named"]["fn"] + self.counts["entity_other"]["fn"]

        results_dict = {}
        results_dict["mention_types"] = {
            category: create_f1_dict_from_counts(self.counts[category]) for category in EVALUATION_CATEGORIES
        }

        results_dict["error_categories"] = {}

        # Move NER results to error categories
        results_dict["error_categories"]["NER"] = results_dict["mention_types"]["NER"]
        del results_dict["mention_types"]["NER"]

        results_dict["error_categories"]["undetected"] = {
            # Undetected
            "all": {
                "errors": self.error_counts[ErrorLabel.UNDETECTED],
                "total": results_dict["error_categories"]["NER"]["ground_truth"]
            },
            "lowercase": {
                "errors": self.error_counts[ErrorLabel.UNDETECTED_LOWERCASE],
                "total": self.n_entity_lowercase
            },
            "partially_included": {
                "errors": self.error_counts[ErrorLabel.UNDETECTED_PARTIALLY_INCLUDED],
                "total": self.n_entity_contains_space
            },
            "partial_overlap": {
                "errors": self.error_counts[ErrorLabel.UNDETECTED_PARTIAL_OVERLAP],
                "total": results_dict["error_categories"]["NER"]["ground_truth"] - self.n_entity_lowercase
            },
            "other": {
                "errors": self.error_counts[ErrorLabel.UNDETECTED_OTHER],
                "total": results_dict["error_categories"]["NER"]["ground_truth"] - self.n_entity_lowercase
            }
        }
        results_dict["error_categories"]["false_detection"] = {
            # False detection
            "all": self.error_counts[ErrorLabel.FALSE_DETECTION],
            "abstract_entity": self.error_counts[ErrorLabel.FALSE_DETECTION_ABSTRACT_ENTITY],
            "unknown_entity": self.error_counts[ErrorLabel.FALSE_DETECTION_UNKNOWN_ENTITY],
            "other": self.error_counts[ErrorLabel.FALSE_DETECTION_OTHER],
            "wrong_span": {
                "errors": self.error_counts[ErrorLabel.FALSE_DETECTION_WRONG_SPAN],
                "total": self.counts["all"]["fp"] + self.counts["all"]["tp"]
            }
        }
        results_dict["error_categories"]["wrong_disambiguation"] = {
            # Disambiguation errors
            "all": {
                "errors": self.error_counts[ErrorLabel.DISAMBIGUATION_WRONG],
                "total": self.counts["NER"]["tp"]
            },
            "demonym": {
                "errors": self.error_counts[ErrorLabel.DISAMBIGUATION_DEMONYM_WRONG],
                "total": self.error_counts[ErrorLabel.DISAMBIGUATION_DEMONYM_CORRECT] +
                         self.error_counts[ErrorLabel.DISAMBIGUATION_DEMONYM_WRONG]
            },
            "metonymy": {
                "errors": self.error_counts[ErrorLabel.DISAMBIGUATION_METONYMY_WRONG],
                "total": self.error_counts[ErrorLabel.DISAMBIGUATION_METONYMY_CORRECT] +
                         self.error_counts[ErrorLabel.DISAMBIGUATION_METONYMY_WRONG]
            },
            "partial_name": {
                "errors": self.error_counts[ErrorLabel.DISAMBIGUATION_PARTIAL_NAME_WRONG],
                "total": self.error_counts[ErrorLabel.DISAMBIGUATION_PARTIAL_NAME_CORRECT] +
                         self.error_counts[ErrorLabel.DISAMBIGUATION_PARTIAL_NAME_WRONG]
            },
            "rare": {
                "errors": self.error_counts[ErrorLabel.DISAMBIGUATION_RARE_WRONG],
                "total": self.error_counts[ErrorLabel.DISAMBIGUATION_RARE_CORRECT] +
                         self.error_counts[ErrorLabel.DISAMBIGUATION_RARE_WRONG]
            },
            "other": self.error_counts[ErrorLabel.DISAMBIGUATION_WRONG_OTHER],
            "wrong_candidates": {
                "errors": self.error_counts[ErrorLabel.DISAMBIGUATION_WRONG_CANDIDATES],
                "total": self.counts["NER"]["tp"]
            } if self.has_candidates else None,
            "multi_candidates": {
                "errors": self.error_counts[ErrorLabel.DISAMBIGUATION_MULTI_CANDIDATES_WRONG],
                "total": self.error_counts[ErrorLabel.DISAMBIGUATION_MULTI_CANDIDATES_WRONG] +
                         self.error_counts[ErrorLabel.DISAMBIGUATION_MULTI_CANDIDATES_CORRECT]
            } if self.has_candidates else None
        }
        results_dict["error_categories"]["other_errors"] = {
            # Other errors
            "hyperlink": {
                "errors": self.error_counts[ErrorLabel.HYPERLINK_WRONG],
                "total": self.error_counts[ErrorLabel.HYPERLINK_CORRECT] +
                         self.error_counts[ErrorLabel.HYPERLINK_WRONG]
            },
        }
        results_dict["error_categories"]["wrong_coreference"] = {
            # Coreference errors
            "undetected": {
                "errors": self.error_counts[ErrorLabel.COREFERENCE_UNDETECTED],
                "total": results_dict["mention_types"]["coref"]["ground_truth"]
            },
            "wrong_mention_referenced": {
                "errors": self.error_counts[ErrorLabel.COREFERENCE_WRONG_MENTION_REFERENCED],
                "total": results_dict["mention_types"]["coref"]["ground_truth"] -
                         self.error_counts[ErrorLabel.COREFERENCE_UNDETECTED]
            },
            "reference_wrongly_disambiguated": {
                "errors": self.error_counts[ErrorLabel.COREFERENCE_REFERENCE_WRONGLY_DISAMBIGUATED],
                "total": results_dict["mention_types"]["coref"]["ground_truth"] -
                         self.error_counts[ErrorLabel.COREFERENCE_UNDETECTED] -
                         self.error_counts[ErrorLabel.COREFERENCE_WRONG_MENTION_REFERENCED]
            },
            "false_detection": self.error_counts[ErrorLabel.COREFERENCE_FALSE_DETECTION]
        }
        # Type results
        results_dict["entity_types"] = {}
        for type_id in self.type_counts:
            results_dict["entity_types"][type_id] = create_f1_dict_from_counts(self.type_counts[type_id])
        return results_dict

    def print_results(self):
        print("== EVALUATION ==")
        for cat in self.counts:
            print()
            print("= %s =" % cat)
            f1_dict = create_f1_dict(self.counts[cat]["tp"], self.counts[cat]["fp"], self.counts[cat]["fn"])
            print("precision:\t%.2f%%" % (f1_dict["precision"] * 100))
            print("recall:\t\t%.2f%%" % (f1_dict["recall"] * 100))
            print("f1:\t\t%.2f%%" % (f1_dict["f1"] * 100))
