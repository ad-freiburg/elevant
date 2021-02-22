from typing import List, Optional

from src.evaluation.case import Case, ErrorLabel
from src.evaluation.coreference_groundtruth_generator import CoreferenceGroundtruthGenerator, is_coreference
from src.evaluation.methods import get_evaluation_cases
from src.evaluation.examples_generator import get_ground_truth_from_labels
from src.evaluation.print_methods import print_colored_text, print_article_nerd_evaluation, \
    print_article_coref_evaluation, print_evaluation_summary
from src.models.entity_database import EntityDatabase
from src.models.wikipedia_article import WikipediaArticle
from src.evaluation.errors import label_errors


def load_evaluation_entities():
    entity_db = EntityDatabase()
    entity_db.load_entities_big()  # TODO big
    entity_db.load_mapping()
    entity_db.load_redirects()
    entity_db.load_sitelink_counts()
    entity_db.load_demonyms()
    return entity_db


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
        for key in ("all", "ner", "coreference", "named", "nominal", "pronominal"):
            self.counts[key] = {"tp": 0, "fp": 0, "fn": 0}
        self.error_counts = {label: 0 for label in ErrorLabel}

    def add_cases(self, cases: List[Case]):
        self.all_cases.extend(cases)
        for case in cases:
            self.count_ner_case(case)
            self.count_mention_type_case(case)
            self.count_error_labels(case)

    def count_ner_case(self, case: Case):
        if not case.is_coreference():
            if case.has_ground_truth():
                if case.has_predicted_entity():
                    self.counts["ner"]["tp"] += 1
                else:
                    self.counts["ner"]["fn"] += 1
            else:
                self.counts["ner"]["fp"] += 1

    def count_mention_type_case(self, case: Case):
        key = case.mention_type.value.lower()
        if case.is_correct():
            subkey = "tp"
        elif case.is_false_positive():
            subkey = "fp"
        else:
            subkey = "fn"
        self.counts[key][subkey] += 1

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

    def print_results(self, output_file: Optional[str] = None):
        print_evaluation_summary(self.all_cases, self.counts, self.error_counts, output_file=output_file)
