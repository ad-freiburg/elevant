import logging
import spacy
from typing import Optional, Dict, Tuple, List

from elevant import settings
from elevant.evaluation.case import Case, ErrorLabel, EvaluationMode
from elevant.evaluation.case_generator import CaseGenerator
from elevant.evaluation.groundtruth_label import GroundtruthLabel
from elevant.evaluation.mention_type import MentionType
from elevant.helpers.entity_database_reader import EntityDatabaseReader
from elevant.models.article import Article
from elevant.models.entity_database import EntityDatabase
from elevant.evaluation.errors import label_errors
from elevant.utils.utils import compute_num_words, compute_lowercase_words, compute_no_lowercase_words

logger = logging.getLogger("main." + __name__.split(".")[-1])


def load_evaluation_entities(type_mapping_file: str, custom_kb: bool) -> EntityDatabase:
    logger.info("Initializing entity database for evaluation ...")
    entity_db = EntityDatabase()
    if custom_kb:
        entity_db.load_custom_entity_names(settings.CUSTOM_ENTITY_TO_NAME_FILE)
        entity_db.load_custom_entity_types(settings.CUSTOM_ENTITY_TO_TYPES_FILE)
    else:
        entity_db.load_entity_names()
        entity_db.load_entity_types(type_mapping_file)
        entity_db.load_wikipedia_to_wikidata_db()
        entity_db.load_redirects()
        entity_db.load_demonyms()
        entity_db.load_quantities()
        entity_db.load_datetimes()
        entity_db.load_family_name_aliases()
        entity_db.load_alias_to_entities()
        entity_db.load_hyperlink_to_most_popular_candidates()
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


def get_type_ids(types: List[str]) -> List[str]:
    type_ids = [typ for typ in types if typ not in ["DATETIME", "QUANTITY"]]
    if not type_ids:  # Datetimes and Quantities are assigned type OTHER
        type_ids = [GroundtruthLabel.OTHER]
    return type_ids


EVALUATION_CATEGORIES = (("all", "ner", "entity", "coref") +
                         tuple(mention_type.value.lower() for mention_type in MentionType))


class Evaluator:
    def __init__(self,
                 type_mapping_file: Optional[str],
                 whitelist_file: Optional[str] = settings.WHITELIST_FILE,
                 contains_unknowns: Optional[bool] = True,
                 custom_kb: Optional[bool] = False):
        self.whitelist_types = EntityDatabaseReader.read_whitelist_types(whitelist_file, with_adjustments=True)
        self.entity_db = load_evaluation_entities(type_mapping_file, custom_kb)
        self.model = spacy.load("en_core_web_lg")
        self.case_generator = CaseGenerator(self.entity_db)
        self.contains_unknowns = contains_unknowns
        self.has_candidates = False

        # Case counts
        self.counts = None
        self.error_counts = None
        self.type_counts = None
        self.n_entity_lowercase = None

        # Denominator counts for false positives
        self.n_words = 0
        self.n_lowercase_words = 0
        self.n_no_lowercase_words = 0
        self.text_stats_dict = {}

        self.reset_variables()

    def reset_variables(self):
        self.has_candidates = False
        self.counts = {}
        self.error_counts = {}
        self.type_counts = {}
        for mode in EvaluationMode:
            self.counts[mode] = {}
            for key in EVALUATION_CATEGORIES:
                self.counts[mode][key] = {"tp": 0, "fp": 0, "fn": 0}
            self.error_counts[mode] = {label: 0 for label in ErrorLabel}
            self.type_counts[mode] = {GroundtruthLabel.OTHER: {"tp": 0, "fp": 0, "fn": 0}}
            for type_id in self.whitelist_types:
                self.type_counts[mode][type_id] = {"tp": 0, "fp": 0, "fn": 0}

        self.n_words = 0
        self.n_lowercase_words = 0
        self.n_no_lowercase_words = 0

    def evaluate_article(self, article: Article) -> List[Case]:
        cases = self.case_generator.get_evaluation_cases(article)
        for mode in EvaluationMode:
            label_errors(article, cases, self.entity_db, mode, contains_unknowns=self.contains_unknowns)
            for case in cases:
                self.count_ner_case(case, mode)
                self.count_mention_type_case(case, mode)
                self.count_error_labels(case, mode)
                if len(case.candidates) > 1:
                    self.has_candidates = True
        # Update denominator counts for false positives.
        # Use hash of text as key to avoid time-consuming recomputation of statistics.
        evaluated_text = article.text[article.evaluation_span[0]:article.evaluation_span[1]]
        if hash(evaluated_text) not in self.text_stats_dict:
            doc = self.model(evaluated_text)
            n_words = compute_num_words(doc)
            n_lowercase_words = compute_lowercase_words(doc)
            n_no_lowercase_words = compute_no_lowercase_words(doc)
            fp_denominators = (n_words, n_lowercase_words, n_no_lowercase_words)
            self.text_stats_dict[hash(evaluated_text)] = fp_denominators
        else:
            fp_denominators = self.text_stats_dict[hash(evaluated_text)]
        self.n_words += fp_denominators[0]
        self.n_lowercase_words += fp_denominators[1]
        self.n_no_lowercase_words += fp_denominators[2]
        return cases

    def count_ner_case(self, case: Case, eval_mode: EvaluationMode):
        if not case.is_coreference():
            if case.is_ner_tp(eval_mode) and case.true_entity.parent is None:
                self.counts[eval_mode]["ner"]["tp"] += 1
            if case.is_ner_fn(eval_mode) and case.true_entity.parent is None:
                self.counts[eval_mode]["ner"]["fn"] += 1
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
                for type_id in get_type_ids(case.true_entity.type.split("|")):
                    self.type_counts[eval_mode][type_id]["tp"] += 1
        if case.is_linking_fn(eval_mode) and case.true_entity.parent is None:
            self.counts[eval_mode]["all"]["fn"] += 1
            self.counts[eval_mode][key]["fn"] += 1

            if case.is_coreference():
                self.counts[eval_mode]["coref"]["fn"] += 1
            else:
                for type_id in get_type_ids(case.true_entity.type.split("|")):
                    self.type_counts[eval_mode][type_id]["fn"] += 1
        if case.is_linking_fp(eval_mode) and case.factor != 0:
            self.counts[eval_mode]["all"]["fp"] += 1
            self.counts[eval_mode][key]["fp"] += 1

            if case.is_coreference():
                self.counts[eval_mode]["coref"]["fp"] += 1
            else:
                pred_entity_id = case.predicted_entity.entity_id
                type_ids = get_type_ids(self.entity_db.get_entity_types(pred_entity_id))
                if not type_ids:
                    type_ids = [GroundtruthLabel.OTHER]
                for type_id in type_ids:
                    self.type_counts[eval_mode][type_id]["fp"] += 1

    def count_error_labels(self, case: Case, eval_mode: EvaluationMode):
        for label in case.error_labels[eval_mode]:
            # We do not count error cases for child labels. This is because we treat all child labels of a parent
            # label as one unit (i.e. for one parent label one can get exactly one TP OR one FN). If we counted all
            # child error labels, the total number of FN errors could be larger than the total number of GT mentions.
            # If we selected only one child error label for the parent label, it would be unclear which child error to
            # select.
            # should_count = (not case.true_entity or case.true_entity.parent is None) and case.factor != 0
            self.error_counts[eval_mode][label] += case.factor  # factor is 0 or 1

    def get_results_dict(self):
        results_dict = {}
        for mode in EvaluationMode:
            entity_mention_types = [mention_type.value.lower() for mention_type in MentionType if mention_type.value.startswith("ENTITY_")]
            self.counts[mode]["entity"]["tp"] = sum([self.counts[mode][mention_type]["tp"] for mention_type in entity_mention_types])
            self.counts[mode]["entity"]["fp"] = sum([self.counts[mode][mention_type]["fp"] for mention_type in entity_mention_types])
            self.counts[mode]["entity"]["fn"] = sum([self.counts[mode][mention_type]["fn"] for mention_type in entity_mention_types])

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
                    "total": self.error_counts[mode][ErrorLabel.NER_FN]
                             + self.error_counts[mode][ErrorLabel.AVOIDED_NER_FN]
                },
                "lowercased": {
                    "errors": self.error_counts[mode][ErrorLabel.NER_FN_LOWERCASED],
                    "total": self.error_counts[mode][ErrorLabel.NER_FN_LOWERCASED]
                             + self.error_counts[mode][ErrorLabel.AVOIDED_NER_FN_LOWERCASED]
                },
                "partially_included": {
                    "errors": self.error_counts[mode][ErrorLabel.NER_FN_PARTIALLY_INCLUDED],
                    "total": self.error_counts[mode][ErrorLabel.NER_FN_PARTIALLY_INCLUDED]
                             + self.error_counts[mode][ErrorLabel.AVOIDED_NER_FN_PARTIALLY_INCLUDED]
                },
                "partial_overlap": {
                    "errors": self.error_counts[mode][ErrorLabel.NER_FN_PARTIAL_OVERLAP],
                    "total": self.error_counts[mode][ErrorLabel.NER_FN_PARTIAL_OVERLAP]
                             + self.error_counts[mode][ErrorLabel.AVOIDED_NER_FN_PARTIAL_OVERLAP]
                },
                "other": {
                    "errors": self.error_counts[mode][ErrorLabel.NER_FN_OTHER],
                    "total": self.error_counts[mode][ErrorLabel.NER_FN_OTHER]
                             + self.error_counts[mode][ErrorLabel.AVOIDED_NER_FN_OTHER]
                }
            }
            results_dict[mode.value]["error_categories"]["ner_fp"] = {
                # False detection
                "all": {
                    "errors": self.error_counts[mode][ErrorLabel.NER_FP],
                    "total": self.n_words
                },
                "lowercased": {
                    "errors": self.error_counts[mode][ErrorLabel.NER_FP_LOWERCASED],
                    "total": self.n_lowercase_words
                },
                "groundtruth_unknown": {
                    "errors": self.error_counts[mode][ErrorLabel.NER_FP_GROUNDTRUTH_UNKNOWN],
                    "total": self.error_counts[mode][ErrorLabel.NER_FP_GROUNDTRUTH_UNKNOWN]
                             + self.error_counts[mode][ErrorLabel.AVOIDED_NER_FP_GROUNDTRUTH_UNKNOWN]
                },
                "other": {
                    "errors": self.error_counts[mode][ErrorLabel.NER_FP_OTHER],
                    "total": self.n_no_lowercase_words
               },
                "wrong_span": {
                    "errors": self.error_counts[mode][ErrorLabel.NER_FP_WRONG_SPAN],
                    "total": self.error_counts[mode][ErrorLabel.NER_FP_WRONG_SPAN]
                             + self.error_counts[mode][ErrorLabel.AVOIDED_NER_FP_WRONG_SPAN]
                }
            }
            results_dict[mode.value]["error_categories"]["wrong_disambiguation"] = {
                # Disambiguation errors
                "all": {
                    "errors": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_WRONG],
                    "total": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_WRONG]
                             + self.error_counts[mode][ErrorLabel.DISAMBIGUATION_CORRECT]
                },
                "demonym": {
                    "errors": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_DEMONYM_WRONG],
                    "total": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_DEMONYM_CORRECT]
                             + self.error_counts[mode][ErrorLabel.DISAMBIGUATION_DEMONYM_WRONG]
                },
                "metonymy": {
                    "errors": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_METONYMY_WRONG],
                    "total": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_METONYMY_CORRECT]
                             + self.error_counts[mode][ErrorLabel.DISAMBIGUATION_METONYMY_WRONG]
                },
                "partial_name": {
                    "errors": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_PARTIAL_NAME_WRONG],
                    "total": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_PARTIAL_NAME_CORRECT]
                             + self.error_counts[mode][ErrorLabel.DISAMBIGUATION_PARTIAL_NAME_WRONG]
                },
                "rare": {
                    "errors": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_RARE_WRONG],
                    "total": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_RARE_CORRECT]
                             + self.error_counts[mode][ErrorLabel.DISAMBIGUATION_RARE_WRONG]
                },
                "other": {
                    "errors": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_OTHER_WRONG],
                    "total": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_OTHER_WRONG]
                             + self.error_counts[mode][ErrorLabel.DISAMBIGUATION_OTHER_CORRECT]
                },
                "wrong_candidates": {
                    "errors": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_CANDIDATES_WRONG],
                    "total": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_CANDIDATES_WRONG]
                             + self.error_counts[mode][ErrorLabel.DISAMBIGUATION_CANDIDATES_CORRECT]
                } if self.has_candidates else None,
                "multiple_candidates": {
                    "errors": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_MULTI_CANDIDATES_WRONG],
                    "total": self.error_counts[mode][ErrorLabel.DISAMBIGUATION_MULTI_CANDIDATES_WRONG]
                             + self.error_counts[mode][ErrorLabel.DISAMBIGUATION_MULTI_CANDIDATES_CORRECT]
                } if self.has_candidates else None
            }
            results_dict[mode.value]["error_categories"]["other_errors"] = {
                # Other errors
                "hyperlink": {
                    "errors": self.error_counts[mode][ErrorLabel.HYPERLINK_WRONG],
                    "total": self.error_counts[mode][ErrorLabel.HYPERLINK_CORRECT]
                             + self.error_counts[mode][ErrorLabel.HYPERLINK_WRONG]
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
                    "total": results_dict[mode.value]["mention_types"]["coref"]["ground_truth"]
                             - self.error_counts[mode][ErrorLabel.COREFERENCE_UNDETECTED]
                },
                "reference_wrongly_disambiguated": {
                    "errors": self.error_counts[mode][ErrorLabel.COREFERENCE_REFERENCE_WRONGLY_DISAMBIGUATED],
                    "total": results_dict[mode.value]["mention_types"]["coref"]["ground_truth"]
                             - self.error_counts[mode][ErrorLabel.COREFERENCE_UNDETECTED]
                             - self.error_counts[mode][ErrorLabel.COREFERENCE_WRONG_MENTION_REFERENCED]
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
