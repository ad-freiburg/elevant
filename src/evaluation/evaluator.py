import logging
from typing import Set, Optional, Dict, Tuple, List

from src import settings
from src.evaluation.case import Case, ErrorLabel, EvaluationMode
from src.evaluation.case_generator import CaseGenerator
from src.evaluation.groundtruth_label import GroundtruthLabel
from src.evaluation.mention_type import is_named_entity
from src.helpers.entity_database_reader import EntityDatabaseReader
from src.models.entity_database import EntityDatabase
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


def get_type_ids(types: str) -> List[str]:
    type_ids = [typ for typ in types.split("|") if typ not in ["DATETIME", "QUANTITY"]]
    if not type_ids:  # Datetimes and Quantities are assigned type OTHER
        type_ids = [GroundtruthLabel.OTHER]
    return type_ids


EVALUATION_CATEGORIES = ("all", "ner", "entity", "entity_named", "entity_other", "coref", "coref_nominal", "coref_pronominal")


class Evaluator:
    def __init__(self,
                 relevant_entity_ids: Set[str],
                 type_mapping_file: Optional[str],
                 whitelist_file: Optional[str] = settings.WHITELIST_FILE,
                 contains_unknowns: bool = True):
        self.whitelist_types = EntityDatabaseReader.read_whitelist_types(whitelist_file, with_adjustments=True)
        self.entity_db = load_evaluation_entities(relevant_entity_ids, type_mapping_file)
        self.case_generator = CaseGenerator(self.entity_db)
        self.contains_unknowns = contains_unknowns
        self.has_candidates = False

        # Case counts
        self.counts = None
        self.error_counts = None
        self.type_counts = None
        self.n_entity_lowercase = None
        self.n_entity_contains_space = None
        self.reset_variables()

    def reset_variables(self):
        self.has_candidates = False
        self.counts = {}
        self.error_counts = {}
        self.type_counts = {}
        self.n_entity_lowercase = {}
        self.n_entity_contains_space = {}
        for mode in EvaluationMode:
            self.counts[mode] = {}
            for key in EVALUATION_CATEGORIES:
                self.counts[mode][key] = {"tp": 0, "fp": 0, "fn": 0}
            self.error_counts[mode] = {label: 0 for label in ErrorLabel}
            self.type_counts[mode] = {GroundtruthLabel.OTHER: {"tp": 0, "fp": 0, "fn": 0}}
            for type_id in self.whitelist_types:
                self.type_counts[mode][type_id] = {"tp": 0, "fp": 0, "fn": 0}
            self.n_entity_lowercase[mode] = 0
            self.n_entity_contains_space[mode] = 0

    def evaluate_article(self, article):
        cases = self.case_generator.get_evaluation_cases(article)
        for mode in EvaluationMode:
            label_errors(article, cases, self.entity_db, mode, contains_unknowns=self.contains_unknowns)
            for case in cases:
                self.count_ner_case(case, mode)
                self.count_mention_type_case(case, mode)
                self.count_error_labels(case, mode)
                if len(case.candidates) > 1:
                    self.has_candidates = True
                if case.has_relevant_ground_truth(mode) and not case.is_coreference() and ' ' in case.text:
                    self.n_entity_contains_space[mode] += 1
        return cases

    def count_ner_case(self, case: Case, eval_mode: EvaluationMode):
        if not case.is_coreference():
            if case.is_ner_tp(eval_mode) and case.true_entity.parent is None:
                self.counts[eval_mode]["ner"]["tp"] += 1
                if not is_named_entity(case.text):
                    self.n_entity_lowercase[eval_mode] += 1
            if case.is_ner_fn(eval_mode) and case.true_entity.parent is None:
                self.counts[eval_mode]["ner"]["fn"] += 1
                if not is_named_entity(case.text):
                    self.n_entity_lowercase[eval_mode] += 1
            if case.is_ner_fp(eval_mode) and case.factor != 0:
                self.counts[eval_mode]["ner"]["fp"] += 1

    def count_mention_type_case(self, case: Case, eval_mode: EvaluationMode):
        key = case.mention_type.value.lower()
        # Disregard child labels for TP and FN
        # Parent could be 0 so check explicitly if parent is None.
        if case.is_linking_tp(eval_mode) and case.true_entity.parent is None:
            self.counts[eval_mode]["all"]["tp"] += 1
            self.counts[eval_mode][key]["tp"] += 1

            if case.is_coreference():
                self.counts[eval_mode]["coref"]["tp"] += 1
            else:
                for type_id in get_type_ids(case.true_entity.type):
                    self.type_counts[eval_mode][type_id]["tp"] += 1
        if case.is_linking_fn(eval_mode) and case.true_entity.parent is None:
            self.counts[eval_mode]["all"]["fn"] += 1
            self.counts[eval_mode][key]["fn"] += 1

            if case.is_coreference():
                self.counts[eval_mode]["coref"]["fn"] += 1
            else:
                for type_id in get_type_ids(case.true_entity.type):
                    self.type_counts[eval_mode][type_id]["fn"] += 1
        if case.is_linking_fp(eval_mode) and case.factor != 0:
            self.counts[eval_mode]["all"]["fp"] += 1
            self.counts[eval_mode][key]["fp"] += 1

            if case.is_coreference():
                self.counts[eval_mode]["coref"]["fp"] += 1
            else:
                pred_entity_id = case.predicted_entity.entity_id
                if self.entity_db.contains_entity(pred_entity_id):
                    type_ids = get_type_ids(self.entity_db.get_entity(pred_entity_id).type)
                else:
                    type_ids = [GroundtruthLabel.OTHER]
                for type_id in type_ids:
                    self.type_counts[eval_mode][type_id]["fp"] += 1

    def count_error_labels(self, case: Case, eval_mode: EvaluationMode):
        for label in case.error_labels[eval_mode]:
            self.error_counts[eval_mode][label] += case.factor  # factor is 0 or 1

    def get_results_dict(self):
        results_dict = {}
        for mode in EvaluationMode:
            self.counts[mode]["entity"]["tp"] = self.counts[mode]["entity_named"]["tp"] + self.counts[mode]["entity_other"]["tp"]
            self.counts[mode]["entity"]["fp"] = self.counts[mode]["entity_named"]["fp"] + self.counts[mode]["entity_other"]["fp"]
            self.counts[mode]["entity"]["fn"] = self.counts[mode]["entity_named"]["fn"] + self.counts[mode]["entity_other"]["fn"]

            results_dict[mode.value] = {}
            results_dict[mode.value]["mention_types"] = {
                category: create_f1_dict_from_counts(self.counts[mode][category]) for category in EVALUATION_CATEGORIES
            }

            results_dict[mode.value]["error_categories"] = {}

            # Move NER results to error categories
            results_dict[mode.value]["error_categories"]["ner"] = results_dict[mode.value]["mention_types"]["ner"]
            del results_dict[mode.value]["mention_types"]["ner"]

            results_dict[mode.value]["error_categories"]["ner_fn"] = {
                # Undetected
                "all": {
                    "errors": self.error_counts[mode][ErrorLabel.NER_FN],
                    "total": results_dict[mode.value]["error_categories"]["ner"]["ground_truth"]
                },
                "lowercased": {
                    "errors": self.error_counts[mode][ErrorLabel.NER_FN_LOWERCASED],
                    "total": self.n_entity_lowercase[mode]
                },
                "partially_included": {
                    "errors": self.error_counts[mode][ErrorLabel.NER_FN_PARTIALLY_INCLUDED],
                    "total": self.n_entity_contains_space[mode]
                },
                "partial_overlap": {
                    "errors": self.error_counts[mode][ErrorLabel.NER_FN_PARTIAL_OVERLAP],
                    "total": results_dict[mode.value]["error_categories"]["ner"]["ground_truth"] - self.n_entity_lowercase[mode]
                },
                "other": {
                    "errors": self.error_counts[mode][ErrorLabel.NER_FN_OTHER],
                    "total": results_dict[mode.value]["error_categories"]["ner"]["ground_truth"] - self.n_entity_lowercase[mode]
                }
            }
            results_dict[mode.value]["error_categories"]["ner_fp"] = {
                # False detection
                "all": self.error_counts[mode][ErrorLabel.NER_FP],
                "lowercased": self.error_counts[mode][ErrorLabel.NER_FP_LOWERCASED],
                "groundtruth_unknown": self.error_counts[mode][ErrorLabel.NER_FP_GROUNDTRUTH_UNKNOWN],
                "other": self.error_counts[mode][ErrorLabel.NER_FP_OTHER],
                "wrong_span": {
                    "errors": self.error_counts[mode][ErrorLabel.NER_FP_WRONG_SPAN],
                    "total": self.counts[mode]["all"]["fp"] + self.counts[mode]["all"]["tp"]  # TODO: This should be only entities, because for undetected errors, only entities are considered, too. Also, coreference errors are handled separately.
                }
            }
            results_dict[mode.value]["error_categories"]["wrong_disambiguation"] = {
                # Disambiguation errors
                "all": {
                    "errors": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_WRONG],
                    "total": self.counts[mode]["ner"]["tp"]
                },
                "demonym": {
                    "errors": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_DEMONYM_WRONG],
                    "total": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_DEMONYM_CORRECT] +
                             self.error_counts[mode][ErrorLabel.DISAMBIGUATION_DEMONYM_WRONG]
                },
                "metonymy": {
                    "errors": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_METONYMY_WRONG],
                    "total": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_METONYMY_CORRECT] +
                             self.error_counts[mode][ErrorLabel.DISAMBIGUATION_METONYMY_WRONG]
                },
                "partial_name": {
                    "errors": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_PARTIAL_NAME_WRONG],
                    "total": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_PARTIAL_NAME_CORRECT] +
                             self.error_counts[mode][ErrorLabel.DISAMBIGUATION_PARTIAL_NAME_WRONG]
                },
                "rare": {
                    "errors": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_RARE_WRONG],
                    "total": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_RARE_CORRECT] +
                             self.error_counts[mode][ErrorLabel.DISAMBIGUATION_RARE_WRONG]
                },
                "other": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_WRONG_OTHER],
                "wrong_candidates": {
                    "errors": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_WRONG_CANDIDATES],
                    "total": self.counts[mode]["ner"]["tp"]
                } if self.has_candidates else None,
                "multiple_candidates": {
                    "errors": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_MULTI_CANDIDATES_WRONG],
                    "total": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_MULTI_CANDIDATES_WRONG] +
                             self.error_counts[mode][ErrorLabel.DISAMBIGUATION_MULTI_CANDIDATES_CORRECT]
                } if self.has_candidates else None
            }
            results_dict[mode.value]["error_categories"]["other_errors"] = {
                # Other errors
                "hyperlink": {
                    "errors": self.error_counts[mode][ErrorLabel.HYPERLINK_WRONG],
                    "total": self.error_counts[mode][ErrorLabel.HYPERLINK_CORRECT] +
                             self.error_counts[mode][ErrorLabel.HYPERLINK_WRONG]
                },
            }
            results_dict[mode.value]["error_categories"]["wrong_coreference"] = {
                # Coreference errors
                "undetected": {
                    "errors": self.error_counts[mode][ErrorLabel.COREFERENCE_UNDETECTED],
                    "total": results_dict[mode.value]["mention_types"]["coref"]["ground_truth"]
                },
                "wrong_mention_referenced": {
                    "errors": self.error_counts[mode][ErrorLabel.COREFERENCE_WRONG_MENTION_REFERENCED],
                    "total": results_dict[mode.value]["mention_types"]["coref"]["ground_truth"] -
                             self.error_counts[mode][ErrorLabel.COREFERENCE_UNDETECTED]
                },
                "reference_wrongly_disambiguated": {
                    "errors": self.error_counts[mode][ErrorLabel.COREFERENCE_REFERENCE_WRONGLY_DISAMBIGUATED],
                    "total": results_dict[mode.value]["mention_types"]["coref"]["ground_truth"] -
                             self.error_counts[mode][ErrorLabel.COREFERENCE_UNDETECTED] -
                             self.error_counts[mode][ErrorLabel.COREFERENCE_WRONG_MENTION_REFERENCED]
                },
                "false_detection": self.error_counts[mode][ErrorLabel.COREFERENCE_FALSE_DETECTION]
            }
            # Type results
            results_dict[mode.value]["entity_types"] = {}
            for type_id in self.type_counts[mode]:
                results_dict[mode.value]["entity_types"][type_id] = create_f1_dict_from_counts(self.type_counts[mode][type_id])
        return results_dict

    def print_results(self):
        print("*** EVALUATION (results shown for mode \"Ignored\" (= InKB)) ***")
        for cat in self.counts[EvaluationMode.IGNORED]:
            print()
            print("= %s =" % cat)
            f1_dict = create_f1_dict(self.counts[EvaluationMode.IGNORED][cat]["tp"],
                                     self.counts[EvaluationMode.IGNORED][cat]["fp"],
                                     self.counts[EvaluationMode.IGNORED][cat]["fn"])
            print("precision:\t%.2f%%" % (f1_dict["precision"] * 100))
            print("recall:\t\t%.2f%%" % (f1_dict["recall"] * 100))
            print("f1:\t\t%.2f%%" % (f1_dict["f1"] * 100))
