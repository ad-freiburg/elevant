from collections import defaultdict
from typing import Tuple, List, Set, Dict

from elevant.evaluation.case import Case, EvaluationType, EvaluationMode
from elevant.evaluation.groundtruth_label import GroundtruthLabel
from elevant.models.entity_database import EntityDatabase
from elevant.models.entity_mention import EntityMention
from elevant.models.wikidata_entity import WikidataEntity
from elevant.models.article import Article
from elevant.utils.knowledge_base_mapper import UnknownEntity, KnowledgeBaseMapper


def word_boundary(span: Tuple[int, int], text: str) -> Tuple[int, int]:
    """
    Given a span and the article text, expand the span to match the word
    boundaries to the left and right.
    Word boundaries are indicated by spaces and non-alphanumeric characters
    other than "'\"_".
    >>> word_boundary((0, 6), "Albert's birthplace is Ulm.")
    (0, 8)
    >>> word_boundary((1, 19), '"Hearts and Flowers" is a song.')
    (0, 20)
    >>> word_boundary((0, 6), "Soviet-backed government.")
    (0, 6)
    """
    extended_span = [span[0], span[1]]
    while extended_span[0] > 0 and (text[extended_span[0] - 1].isalnum() or text[extended_span[0] - 1] in "'\"_"):
        # Extend span to the left until it reaches a whitespace
        extended_span[0] -= 1
    while extended_span[1] < len(text) - 1 and (text[extended_span[1]].isalnum()
                                                or text[extended_span[1]] in "'\"_"):
        # Extend span to the right until it reaches whitespace or punctuation except for those noted
        extended_span[1] += 1
    if text[extended_span[0]] == '"' and '"' not in text[extended_span[0] + 1:extended_span[1]]:
        # Avoid expanding spans in cases like 'MetalStorm wrote: "Gore Metal features ...'
        extended_span[0] += 1
    return extended_span[0], extended_span[1]


class CaseGenerator:
    def __init__(self, entity_db: EntityDatabase):
        self.entity_db = entity_db
        self.article = None
        self.label_dict = None
        self.all_predictions = None
        self.factor_dict = None
        self.gt_case_dict = None

    def determine_entity_type(self, entity_id: str) -> str:
        """
        Determine the type of an entity.
        Either a type from the whitelist or QUANTITY, DATETIME, OTHER.
        """
        entity_type = GroundtruthLabel.OTHER
        if self.entity_db.is_quantity(entity_id):
            entity_type = GroundtruthLabel.QUANTITY
        elif self.entity_db.is_datetime(entity_id):
            entity_type = GroundtruthLabel.DATETIME
        else:
            type_ids = self.entity_db.get_entity_types(entity_id)
            if type_ids:
                entity_type = "|".join(type_ids)
        return entity_type

    def get_evaluation_cases(self, article: Article) -> List[Case]:
        """
        Return all evaluation cases for a given article.
        """
        self.article = article

        # all_predictions contains predicted spans and predicted spans that were expanded to word boundaries
        predictions = article.entity_mentions
        expanded_prediction_spans = {word_boundary(span, article.text): pred for span, pred in predictions.items()}
        self.all_predictions = predictions.copy()
        self.all_predictions.update(expanded_prediction_spans)

        evaluation_span = article.evaluation_span

        # Get set of ground truth spans + ground truth spans expanded to word boundaries
        ground_truth_spans = set()
        for gt_label in article.labels:
            ground_truth_spans.add(gt_label.span)
            ground_truth_spans.add(word_boundary(gt_label.span, article.text))

        self.label_dict = dict()
        for gt_label in article.labels:
            self.label_dict[gt_label.id] = gt_label

        root_gt_labels = sorted([label for label in article.labels if label.parent is None])
        child_gt_labels = sorted([label for label in article.labels if label.parent is not None])

        self.factor_dict = dict()
        cases = []
        self.gt_case_dict = dict()

        # Ground truth cases:
        # Go through root ground truth labels first to compute the factor for all its children
        # Then add the child cases
        for gt_label in root_gt_labels + child_gt_labels:
            span = gt_label.span
            expanded_span = word_boundary(span, article.text)
            text = article.text[span[0]:span[1]]
            detected = span in self.all_predictions or expanded_span in self.all_predictions
            if detected:
                predicted_mention = self.all_predictions[span] if span in self.all_predictions else \
                    self.all_predictions[expanded_span]
                candidates = set()
                for cand_id in predicted_mention.candidates:
                    candidates.add(WikidataEntity(cand_id, self.entity_db.get_entity_name(cand_id)))
                predicted_by = predicted_mention.linked_by
                predicted_entity_id = predicted_mention.entity_id
                predicted_entity_name = self.entity_db.get_entity_name(predicted_entity_id)
                predicted_entity_type = self.determine_entity_type(predicted_entity_id)
                predicted_entity = WikidataEntity(predicted_mention.entity_id,
                                                  predicted_entity_name,
                                                  type=predicted_entity_type)
            else:
                predicted_by = None
                predicted_entity = None
                candidates = set()

            # Due to our overlapping gt labels, some cases should not count
            # If gt_label is parent of a child label that was detected, don't count parent label -> factor = 0
            if gt_label.parent is None:
                factor = self.recursively_determine_factor(gt_label.id)
            else:
                factor = self.factor_dict[gt_label.id] if gt_label.id in self.factor_dict else 0

            case = Case(span, text, gt_label, predicted_entity, candidates, predicted_by, factor=factor)
            cases.append(case)
            self.gt_case_dict[gt_label.id] = case

        # predicted cases (potential false detections):
        for span in sorted(predictions):
            expanded_span = word_boundary(span, article.text)
            predicted_mention = predictions[span]

            candidates = set()
            for cand_id in predicted_mention.candidates:
                candidates.add(WikidataEntity(cand_id, self.entity_db.get_entity_name(cand_id)))

            predicted_entity_id = predicted_mention.entity_id
            predicted_entity_name = self.entity_db.get_entity_name(predicted_entity_id)
            predicted_entity_type = self.determine_entity_type(predicted_entity_id)
            predicted_entity = WikidataEntity(predicted_mention.entity_id, predicted_entity_name,
                                              type=predicted_entity_type)

            if (span not in ground_truth_spans and expanded_span not in ground_truth_spans) and \
                    predicted_entity_id is not None and span[0] >= evaluation_span[0] and span[1] <= evaluation_span[1]:
                text = article.text[span[0]:span[1]]
                predicted_by = predicted_mention.linked_by
                case = Case(span, text, None, predicted_entity, candidates=candidates,
                            predicted_by=predicted_by, factor=1)
                cases.append(case)

        # Now, after all cases are computed together with their evaluation case, go through
        # root GT cases and re-compute their evaluation type from their child evaluation types.
        self.reevaluate_root_gt_cases()

        return sorted(cases)

    def reevaluate_root_gt_cases(self) -> None:
        """
        Re-evaluate all root cases with a ground truth and factor == 0 by first
        retrieving all their relevant child evaluation types (children are
        relevant when their factor is != 0) and then re-computing their
        evaluation type using these child evaluation types.
        """
        for case in self.gt_case_dict.values():
            if case.true_entity.parent is None:
                if case.true_entity.children:
                    if case.true_entity.is_optional():
                        # Determine whether a ground truth parent label has non-optional children
                        case.set_has_non_optional_children(case.true_entity.has_non_optional_child(self.label_dict))
                        # Re-compute evaluation types for parent GT labels with children
                        case.compute_eval_types()
                    if case.factor == 0:
                        # Get relevant child evaluation types for both linking and NER
                        child_linking_et, child_ner_et = self.get_relevant_child_eval_types(case.true_entity)
                        case.set_child_linking_eval_types(child_linking_et)
                        case.set_child_ner_eval_types(child_ner_et)

                        # Re-compute evaluation types for parent GT labels with children
                        case.compute_eval_types()

    def get_relevant_child_eval_types(self, gt_label: GroundtruthLabel) \
            -> Tuple[Dict[EvaluationMode, Set[EvaluationType]], Dict[EvaluationMode, Set[EvaluationType]]]:
        """
        Recursively retrieve all evaluation types (linking and NER) for the
        current label and its child labels if they have factor != 0.
        Retrieve the evaluation types separately for each evaluation mode.
        """
        linking_eval_types = defaultdict(set)
        ner_eval_types = defaultdict(set)
        for child_id in gt_label.children:
            # Recursively retrieve evaluation types for children of the current label
            child_gt_label = self.label_dict[child_id]
            child_linking_eval_types, child_ner_eval_types = self.get_relevant_child_eval_types(child_gt_label)
            for mode in EvaluationMode:
                linking_eval_types[mode].update(child_linking_eval_types[mode])
                ner_eval_types[mode].update(child_ner_eval_types[mode])

            # Get evaluation types for the current label if it has factor != 0
            case = self.gt_case_dict[child_id]
            if case.factor != 0:
                for mode in EvaluationMode:
                    linking_eval_types[mode].update(set(case.linking_eval_types[mode]))
                    ner_eval_types[mode].update(set(case.ner_eval_types[mode]))

        return linking_eval_types, ner_eval_types

    def recursively_determine_factor(self, label_id: int, determining_siblings=False) -> int:
        """
        Returns factor for given label_id and saves determined factors in the
        factors dictionary. Factors of children that did not have to be looked
        at are not saved in the factors dictionary.

        >>> cg = CaseGenerator(EntityDatabase())
        >>> text = "aa, bb, cc"
        >>> article = Article(0, "", text, [])
        >>> cg.article = article
        >>> l1 = GroundtruthLabel(1, (0, 10), "Q1", "Q1", None, [2])
        >>> l2 = GroundtruthLabel(2, (0, 2), "Q2", "Q2", 1, None)
        >>> labels = [l1, l2]
        >>> cg.label_dict = {label.id: label for label in labels}
        >>> p1 = EntityMention((0, 2), "Test", "Q2")
        >>> cg.all_predictions ={p1.span: p1}
        >>> result_list = []
        >>> cg.factor_dict = dict()
        >>> cg.recursively_determine_factor(1)
        0
        >>> sorted(cg.factor_dict.items())
        [(1, 0), (2, 1)]
        >>> cg = CaseGenerator(EntityDatabase())
        >>> text = "aa, bb, cc"
        >>> article = Article(0, "", text, [])
        >>> cg.article = article
        >>> l1 = GroundtruthLabel(1, (0, 10), "Q1", "Q1", None, [2])
        >>> l2 = GroundtruthLabel(2, (0, 2), UnknownEntity.NIL.value, "Unknown1", 1, None)
        >>> labels = [l1, l2]
        >>> cg.label_dict = {label.id: label for label in labels}
        >>> p1 = EntityMention((0, 2), "Unknown", UnknownEntity.NIL.value)
        >>> cg.all_predictions ={p1.span: p1}
        >>> result_list = []
        >>> cg.factor_dict = dict()
        >>> cg.recursively_determine_factor(1)
        0
        >>> sorted(cg.factor_dict.items())
        [(1, 0), (2, 1)]
        >>> cg = CaseGenerator(EntityDatabase())
        >>> text = "aa, bb, cc"
        >>> article = Article(0, "", text, [])
        >>> cg.article = article
        >>> l1 = GroundtruthLabel(1, (0, 10), "Q1", "Q1", None, [2, 5])
        >>> l2 = GroundtruthLabel(2, (0, 2), "Q2", "Q2", 1, [3])
        >>> l3 = GroundtruthLabel(3, (0, 2), "Q3", "Q3", 2, [4])
        >>> l4 = GroundtruthLabel(4, (0, 2), "Q4", "Q4", 3, None)
        >>> l5 = GroundtruthLabel(5, (4, 10), "Q5", "Q5", 1, [6, 7])
        >>> l6 = GroundtruthLabel(6, (4, 6), "Q6", "Q6", 5, [8])
        >>> l7 = GroundtruthLabel(7, (8, 10), "Q7", "Q7", 5, None)
        >>> l8 = GroundtruthLabel(8, (4, 6), "Q8", "Q8", 6, None)
        >>> labels = [l1, l2, l3, l4, l5, l6, l7, l8]
        >>> cg.label_dict = {label.id: label for label in labels}
        >>> p1 = EntityMention((0, 2), "Test", "Q3")
        >>> p2 = EntityMention((4, 6), "Test", "Q8")
        >>> p3 = EntityMention((8, 10), "Test", "Q7")
        >>> cg.all_predictions ={p1.span: p1, p2.span: p2, p3.span: p3}
        >>> cg.factor_dict = dict()
        >>> cg.recursively_determine_factor(1)
        0
        >>> sorted(cg.factor_dict.items())
        [(1, 0), (2, 0), (3, 1), (5, 0), (6, 0), (7, 1), (8, 1)]
        >>> cg = CaseGenerator(EntityDatabase())
        >>> text = "aa, bb, cc"
        >>> article = Article(0, "", text, [])
        >>> cg.article = article
        >>> l1 = GroundtruthLabel(1, (0, 10), "Q1", "Q1", None, None)
        >>> labels = [l1]
        >>> cg.label_dict = {label.id: label for label in labels}
        >>> cg.all_predictions = dict()
        >>> cg.factor_dict = dict()
        >>> cg.recursively_determine_factor(1)
        1
        >>> sorted(cg.factor_dict.items())
        [(1, 1)]
        """
        label = self.label_dict[label_id]
        expanded_label_span = word_boundary(label.span, self.article.text)

        # Get predicted entity id for label span
        if label.span in self.all_predictions:
            pred_entity_id = self.all_predictions[label.span].entity_id
        elif expanded_label_span in self.all_predictions:
            pred_entity_id = self.all_predictions[expanded_label_span].entity_id
        else:
            pred_entity_id = None

        if pred_entity_id and (label.entity_id == pred_entity_id or
                               (KnowledgeBaseMapper.is_unknown_entity(label.entity_id) and
                                KnowledgeBaseMapper.is_unknown_entity(pred_entity_id))):
            # Factor is certainly 1 if the mention was correctly detected and linked. All child labels have factor 0.
            # Return is only ok if child labels not occurring in the factor dictionary are assigned factor 0.
            # Otherwise, we need to go through all child labels.
            factor = 1
            if not determining_siblings:
                self.factor_dict[label_id] = factor
            return factor

        biggest_child_factor = 0
        if label.children:
            for child_id in label.children:
                biggest_child_factor = max(biggest_child_factor, self.recursively_determine_factor(child_id))

        if label.parent is None:
            # We are at the root node. Iff none of the children were detected, show the root node
            factor = 1 if biggest_child_factor == 0 else 0
            if not determining_siblings:
                # If statement currently not necessary, since determining_siblings is never true for root
                self.factor_dict[label_id] = factor
            return factor
        else:
            factor = 0
            parent_span = self.label_dict[label.parent].span
            if pred_entity_id and biggest_child_factor == 0 and \
                    word_boundary(parent_span, self.article.text) != word_boundary(label.span, self.article.text):
                # If the mention was detected, no child was correct and the parent span is not the same as the label
                # span
                factor = 1
            elif not pred_entity_id and not determining_siblings and biggest_child_factor == 0:
                # If the mention was not detected, but siblings were, factor is 1.
                # If parent span is the same as label span, the label can not have any siblings, so the factor is 0
                siblings = self.label_dict[label.parent].children[:]
                siblings.remove(label_id)
                for sibling_id in siblings:
                    sibling_factor = self.recursively_determine_factor(sibling_id, determining_siblings=True)
                    if sibling_factor > 0:
                        factor = 1
                        break

            if not determining_siblings:
                # Don't overwrite a previously determined factor when determining sibling factors
                self.factor_dict[label_id] = factor
            return max(biggest_child_factor, factor)
