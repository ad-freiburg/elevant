from typing import List

from src.evaluation.case import Case, ErrorLabel
from src.evaluation.coreference_groundtruth_generator import CoreferenceGroundtruthGenerator, is_coreference
from src.evaluation.methods import get_evaluation_cases
from src.evaluation.examples_generator import get_ground_truth_from_labels
from src.evaluation.print_methods import print_colored_text, print_article_nerd_evaluation, \
    print_article_coref_evaluation, print_evaluation_summary, create_f1_dict_from_counts
from src.models.entity_database import EntityDatabase
from src.models.wikipedia_article import WikipediaArticle
from src.evaluation.errors import label_errors


def load_evaluation_entities():
    entity_db = EntityDatabase()
    entity_db.load_entities_big()
    entity_db.load_mapping()
    entity_db.load_redirects()
    entity_db.load_sitelink_counts()
    entity_db.load_demonyms()
    return entity_db


EVALUATION_CATEGORIES = ("all", "NER", "coreference", "named", "nominal", "pronominal")


class Evaluator:
    def __init__(self,
                 load_data: bool = True,
                 coreference: bool = True):
        self.all_cases = []
        if load_data:
            self.entity_db = load_evaluation_entities()
        self.data_loaded = load_data
        self.coreference = coreference
        self.counts = {}
        for key in EVALUATION_CATEGORIES:
            self.counts[key] = {"tp": 0, "fp": 0, "fn": 0}
        self.error_counts = {label: 0 for label in ErrorLabel}
        self.has_candidates = False
        self.n_named_lowercase = 0
        self.n_named_contains_space = 0

    def add_cases(self, cases: List[Case]):
        self.all_cases.extend(cases)
        for case in cases:
            self.count_ner_case(case)
            self.count_mention_type_case(case)
            self.count_error_labels(case)
            if len(case.candidates) > 1:
                self.has_candidates = True
            if case.is_named() and case.has_ground_truth() and ' ' in case.text:
                self.n_named_contains_space += 1

    def count_ner_case(self, case: Case):
        if case.is_named():
            if case.has_ground_truth() and case.is_known_entity():
                if case.has_predicted_entity():
                    self.counts["NER"]["tp"] += 1
                else:
                    self.counts["NER"]["fn"] += 1
                if case.text.islower():
                    self.n_named_lowercase += 1
            else:
                self.counts["NER"]["fp"] += 1

    def count_mention_type_case(self, case: Case):
        key = case.mention_type.value.lower()
        if case.is_correct():
            self.counts["all"]["tp"] += 1
            self.counts[key]["tp"] += 1
            if case.is_coreference():
                self.counts["coreference"]["tp"] += 1
        else:
            if case.is_false_positive():
                self.counts["all"]["fp"] += 1
                self.counts[key]["fp"] += 1
                if case.is_coreference():
                    self.counts["coreference"]["fp"] += 1
            if case.is_false_negative():
                self.counts["all"]["fn"] += 1
                self.counts[key]["fn"] += 1
                if case.is_coreference():
                    self.counts["coreference"]["fn"] += 1

    def count_error_labels(self, case: Case):
        for label in case.error_labels:
            self.error_counts[label] += 1

    def get_cases(self, article: WikipediaArticle):
        if not self.data_loaded:
            raise Exception("Cannot call Evaluator.get_cases() when the evaluator was created with load_data=False.")
        ground_truth = get_ground_truth_from_labels(article.labels)
        if not self.coreference:
            ground_truth = [(span, entity_id) for span, entity_id in ground_truth
                            if not is_coreference(article.text[span[0]:span[1]])]

        coref_ground_truth = CoreferenceGroundtruthGenerator.get_groundtruth(article)

        cases = get_evaluation_cases(article, ground_truth, coref_ground_truth, self.entity_db)

        label_errors(article.text, cases, self.entity_db)

        return cases

    @staticmethod
    def print_article_evaluation(article: WikipediaArticle, cases: List[Case]):
        print_colored_text(cases, article.text)
        print_article_nerd_evaluation(cases, article.text)
        print_article_coref_evaluation(cases, article.text)

    def print_results(self):
        print_evaluation_summary(self)

    def get_results_dict(self):
        results_dict = {
            category: create_f1_dict_from_counts(self.counts[category]) for category in EVALUATION_CATEGORIES
        }
        results_dict["errors"] = {
            "undetected": {
                "errors": self.error_counts[ErrorLabel.UNDETECTED],
                "total": results_dict["NER"]["ground_truth"]
            },
            "undetected_lowercase": {
                "errors": self.error_counts[ErrorLabel.UNDETECTED_LOWERCASE],
                "total": self.n_named_lowercase
            },
            "specificity": {
                "errors": self.error_counts[ErrorLabel.SPECIFICITY],
                "total": self.n_named_contains_space
            },
            "rare": {
                "errors": self.error_counts[ErrorLabel.RARE],
                "total": self.counts["NER"]["tp"]
            },
            "demonym": {
                "errors": self.error_counts[ErrorLabel.DEMONYM_WRONG],
                "total": self.error_counts[ErrorLabel.DEMONYM_CORRECT] +
                         self.error_counts[ErrorLabel.DEMONYM_WRONG]
            },
            "partial_name": {
                "errors": self.error_counts[ErrorLabel.PARTIAL_NAME_WRONG],
                "total": self.error_counts[ErrorLabel.PARTIAL_NAME_CORRECT] +
                         self.error_counts[ErrorLabel.PARTIAL_NAME_WRONG]
            },
            "abstraction": self.error_counts[ErrorLabel.ABSTRACTION]
        }
        if not self.has_candidates:
            results_dict["errors"]["wrong_candidates"] = None
            results_dict["errors"]["multi_candidates"] = None
        else:
            results_dict["errors"]["wrong_candidates"] = {
                "errors": self.error_counts[ErrorLabel.WRONG_CANDIDATES],
                "total": self.counts["NER"]["tp"]
            }
            results_dict["errors"]["multi_candidates"] = {
                "wrong": self.error_counts[ErrorLabel.MULTI_CANDIDATES_WRONG],
                "total": self.error_counts[ErrorLabel.MULTI_CANDIDATES_WRONG] +
                         self.error_counts[ErrorLabel.MULTI_CANDIDATES_CORRECT]
            }
        results_dict["coreference_errors"] = {
            "no_reference": {
                "errors": self.error_counts[ErrorLabel.COREFERENCE_NO_REFERENCE],
                "total": results_dict["coreference"]["ground_truth"]
            },
            "wrong_reference": {
                "errors": self.error_counts[ErrorLabel.COREFERENCE_WRONG_REFERENCE],
                "total": results_dict["coreference"]["ground_truth"] -
                         self.error_counts[ErrorLabel.COREFERENCE_NO_REFERENCE]
            },
            "referenced_wrong": {
                "errors": self.error_counts[ErrorLabel.COREFERENCE_REFERENCED_WRONG],
                "total": results_dict["coreference"]["ground_truth"] -
                         self.error_counts[ErrorLabel.COREFERENCE_NO_REFERENCE] -
                         self.error_counts[ErrorLabel.COREFERENCE_WRONG_REFERENCE]
            },
            "non_entity_coreference": self.error_counts[ErrorLabel.NON_ENTITY_COREFERENCE]
        }
        return results_dict
