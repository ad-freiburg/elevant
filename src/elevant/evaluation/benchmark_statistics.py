import spacy
import json

from typing import List

from elevant.evaluation.groundtruth_label import GroundtruthLabel
from elevant.evaluation.mention_type import get_mention_type, MentionType
from elevant.evaluation.benchmark_iterator import get_benchmark_iterator
from elevant.evaluation.benchmark_case import BenchmarkCase

from elevant.evaluation.case import Case
from elevant.evaluation.errors import get_benchmark_case_labels
from elevant.evaluation.benchmark_case import BenchmarkCaseLabel
from elevant.models.entity_database import EntityDatabase
from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper, UnknownEntity
from elevant.utils.utils import compute_num_words


class BenchmarkStatistics:
    def __init__(self, entity_db: EntityDatabase, model=None):
        self.entity_db = entity_db

        self.model = model
        if self.model is None:
            self.model = spacy.load("en_core_web_lg")

        # Text corpus statistics
        self.text_statistics = {"words": 0, "sents": 0, "articles": 0, "labels": 0}

        # Groundtruth label statistics
        self.types = {}
        self.multi_word_statistics = {}
        self.mention_types = {mention_type: 0 for mention_type in MentionType}
        self.tags = {case_label: 0 for case_label in BenchmarkCaseLabel}

    def analyze_benchmark(self, benchmark: str, only_root_labels: bool = False) -> List[List[BenchmarkCase]]:
        benchmark_cases = []
        benchmark_iterator = get_benchmark_iterator(benchmark)
        for article in benchmark_iterator.iterate():
            article_gt_cases = []
            self.text_statistics["articles"] += 1
            self.analyze_text(article)
            for gt_label in article.labels:
                if only_root_labels and gt_label.parent is not None:
                    # If only root labels are supposed to be analyzed, skip all labels that have a parent
                    continue
                mention_text = article.text[gt_label.span[0]:gt_label.span[1]]
                groundtruth_case = self.analyze_label(gt_label, mention_text)
                article_gt_cases.append(groundtruth_case)
                self.text_statistics["labels"] += 1
            benchmark_cases.append(article_gt_cases)
        return benchmark_cases

    def analyze_text(self, article):
        # Analyze text statistics only within evaluated span
        evaluated_text = article.text[article.evaluation_span[0]:article.evaluation_span[1]]
        doc = self.model(evaluated_text)
        self.text_statistics["words"] += compute_num_words(doc)
        self.text_statistics["sents"] += len([sent for sent in doc.sents])

    def analyze_label(self, gt_label: GroundtruthLabel, mention_text: str):
        benchmark_case = BenchmarkCase(gt_label.span, gt_label)

        # Compute mention type statistics (named entity / non-named entity / pronominal coref / coref)
        mention_type = get_mention_type(mention_text, gt_label, None)
        self.mention_types[mention_type] += 1
        benchmark_case.set_mention_type(mention_type)

        # Compute type statistics
        for type in gt_label.get_types():
            if type not in self.types:
                self.types[type] = 0
            self.types[type] += 1
        benchmark_case.set_types(gt_label.get_types())

        # Compute multi-word statistics
        num_words = len(mention_text.split(" "))
        if num_words not in self.multi_word_statistics:
            self.multi_word_statistics[num_words] = 0
        self.multi_word_statistics[num_words] += 1
        benchmark_case.set_mention_word_count(num_words)

        # Compute potential error type statistics
        # Create a dummy case, so I can use the functions defined in errors.py
        dummy_case = Case(gt_label.span, mention_text, gt_label, None, set(), None)
        error_type = get_benchmark_case_labels(dummy_case, self.entity_db)
        if error_type:
            self.tags[error_type] += 1
            benchmark_case.add_tag(error_type)

        # Compute mention case statistics

        if mention_text[0].isupper():
            tag = BenchmarkCaseLabel.CAPITALIZED
            self.tags[tag] += 1
            benchmark_case.add_tag(tag)
        elif mention_text[0].islower():
            tag = BenchmarkCaseLabel.LOWERCASED
            self.tags[tag] += 1
            benchmark_case.add_tag(tag)
            if mention_type == MentionType.ENTITY_NON_NAMED:
                tag = BenchmarkCaseLabel.LOWERCASED_NON_NAMED
                self.tags[tag] += 1
                benchmark_case.add_tag(tag)
        else:
            tag = BenchmarkCaseLabel.NON_ALPHA
            self.tags[tag] += 1
            benchmark_case.add_tag(tag)

        # Compute optional label statistics
        if gt_label.is_optional():
            tag = BenchmarkCaseLabel.OPTIONAL
            self.tags[tag] += 1
            benchmark_case.add_tag(tag)

        # Compute unknown label statistics
        if KnowledgeBaseMapper.is_unknown_entity(gt_label.entity_id):
            tag = BenchmarkCaseLabel.UNKNOWN
            self.tags[tag] += 1
            benchmark_case.add_tag(tag)
        if gt_label.entity_id == UnknownEntity.NIL.value:
            tag = BenchmarkCaseLabel.UNKNOWN_NIL
            self.tags[tag] += 1
            benchmark_case.add_tag(tag)
        elif gt_label.entity_id == UnknownEntity.NO_MAPPING.value:
            tag = BenchmarkCaseLabel.UNKNOWN_NO_MAPPING
            self.tags[tag] += 1
            benchmark_case.add_tag(tag)

        # Compute root / child label statistics
        if gt_label.parent is None:
            tag = BenchmarkCaseLabel.ROOT
            self.tags[tag] += 1
            benchmark_case.add_tag(tag)
        else:
            tag = BenchmarkCaseLabel.CHILD
            self.tags[tag] += 1
            benchmark_case.add_tag(tag)

        return benchmark_case

    def to_dict(self):
        return {"text_statistics": self.text_statistics,
                "mention_types": {mention_type.value.lower(): num for mention_type, num in self.mention_types.items()},
                "types": self.types,
                "multi_word_statistics": self.multi_word_statistics,
                "tags": {tag.value.lower(): num for tag, num in self.tags.items()}}

    def to_json(self):
        return json.dumps(self.to_dict())
