from typing import List, Optional

from src.evaluation.case import Case
from src.evaluation.coreference_groundtruth_generator import CoreferenceGroundtruthGenerator, is_coreference
from src.evaluation.methods import get_evaluation_cases, evaluate_ner
from src.evaluation.examples_generator import get_ground_truth_from_labels
from src.evaluation.print_methods import print_colored_text, print_article_nerd_evaluation, \
    print_article_coref_evaluation, print_evaluation_summary
from src.models.entity_database import EntityDatabase
from src.models.wikipedia_article import WikipediaArticle


def load_evaluation_entities():
    entity_db = EntityDatabase()
    entity_db.load_entities_small()  # TODO big
    entity_db.load_mapping()
    entity_db.load_redirects()
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
        self.ner_tp = self.ner_fp = self.ner_fn = 0

    def add_cases(self, cases: List[Case]):
        self.all_cases.extend(cases)

    def get_cases(self, article: WikipediaArticle):
        if not self.data_loaded:
            raise Exception("Cannot call Evaluator.get_cases() when the evaluator was created with load_data=False.")
        ground_truth = get_ground_truth_from_labels(article.labels)
        if not self.coreference:
            ground_truth = [(span, entity_id) for span, entity_id in ground_truth
                            if not is_coreference(article.text[span[0]:span[1]])]

        coref_ground_truth = CoreferenceGroundtruthGenerator.get_groundtruth(article)

        cases = get_evaluation_cases(article.entity_mentions, ground_truth, coref_ground_truth, article.evaluation_span,
                                     self.entity_db)
        return cases

    def eval_ner(self, article):
        ground_truth = get_ground_truth_from_labels(article.labels)
        ner_tp, ner_fp, ner_fn = evaluate_ner(article.entity_mentions, ground_truth, article.evaluation_span)
        self.ner_tp += len(ner_tp)
        self.ner_fp += len(ner_fp)
        self.ner_fn += len(ner_fn)

    @staticmethod
    def print_article_evaluation(article: WikipediaArticle, cases: List[Case]):
        print_colored_text(cases, article.text)
        print_article_nerd_evaluation(cases, article.text)
        print_article_coref_evaluation(cases, article.text)

    def print_results(self, output_file: Optional[str] = None):
        print_evaluation_summary(self.all_cases, self.ner_tp, self.ner_fp, self.ner_fn, output_file=output_file)
