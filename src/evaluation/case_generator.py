from typing import Tuple, List

from src.evaluation.case import Case
from src.evaluation.groundtruth_label import GroundtruthLabel
from src.linkers.abstract_coref_linker import AbstractCorefLinker
from src.models.entity_database import EntityDatabase
from src.models.entity_mention import EntityMention
from src.models.wikidata_entity import WikidataEntity
from src.models.article import Article


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
        self.coref_ground_truth = None
        self.label_dict = None
        self.all_predictions = None
        self.factor_dict = None

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
        elif self.entity_db.contains_entity(entity_id):
            type_ids = self.entity_db.get_entity(entity_id).type.split("|")
            entity_type = "|".join(type_ids)
        return entity_type

    def get_evaluation_cases(self, article: Article, coref_ground_truth) -> List[Case]:
        """
        Return all evaluation cases for a given article.
        """
        self.article = article
        self.coref_ground_truth = coref_ground_truth

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

        # Ground truth cases:
        # Go through root ground truth labels first to compute the factor for all its children
        # Then add the child cases
        for gt_label in root_gt_labels + child_gt_labels:
            span = gt_label.span
            expanded_span = word_boundary(span, article.text)
            text = article.text[span[0]:span[1]]
            detected = span in self.all_predictions or expanded_span in self.all_predictions
            predicted_mention = None
            if detected:
                predicted_mention = self.all_predictions[span] if span in self.all_predictions else \
                    self.all_predictions[expanded_span]
                candidates = set()
                for cand_id in predicted_mention.candidates:
                    if self.entity_db.contains_entity(cand_id):
                        candidates.add(WikidataEntity(self.entity_db.get_entity(cand_id).name, 0, cand_id))
                predicted_by = predicted_mention.linked_by
                predicted_entity_id = predicted_mention.entity_id
                predicted_entity_name = self.entity_db.get_entity(predicted_entity_id).name \
                    if self.entity_db.contains_entity(predicted_entity_id) else "Unknown"

                predicted_entity_type = self.determine_entity_type(predicted_entity_id)

                predicted_entity = WikidataEntity(predicted_entity_name, 0, predicted_mention.entity_id,
                                                  type=predicted_entity_type)
                contained = predicted_mention.contained
            else:
                predicted_by = None
                predicted_entity = None
                candidates = set()
                contained = None

            referenced_span = None
            is_true_coref = span in coref_ground_truth
            correct_span_referenced = False
            if detected and predicted_by == AbstractCorefLinker.IDENTIFIER:
                referenced_span = predicted_mention.referenced_span
                if is_true_coref:
                    for poss_ref_span in coref_ground_truth[span]:
                        # Do not require a perfect match of the spans but look for overlaps
                        if poss_ref_span[0] <= referenced_span[1] <= poss_ref_span[1] or \
                                poss_ref_span[0] <= referenced_span[0] <= poss_ref_span[1]:
                            correct_span_referenced = True
                            break

            # Due to our overlapping gt labels, some cases should not count
            # If gt_label is parent of a child label that was detected, don't count parent label -> factor = 0
            children_correctly_linked = None
            children_correctly_detected = None
            if gt_label.parent is None:
                children_correctly_linked = self.recursively_check_children_correctly_linked(gt_label.id)
                children_correctly_detected = self.recursively_check_children_correctly_detected(gt_label.id)
                factor = self.recursively_determine_factor(gt_label.id)
            else:
                factor = self.factor_dict[gt_label.id] if gt_label.id in self.factor_dict else 0

            case = Case(span, text, gt_label, detected, predicted_entity, candidates, predicted_by,
                        contained=contained,
                        is_true_coref=is_true_coref,
                        correct_span_referenced=correct_span_referenced,
                        referenced_span=referenced_span,
                        factor=factor,
                        children_correctly_linked=children_correctly_linked,
                        children_correctly_detected=children_correctly_detected)
            cases.append(case)

        # predicted cases (potential false detections):
        for span in sorted(predictions):
            expanded_span = word_boundary(span, article.text)
            predicted_mention = predictions[span]

            candidates = set()
            for cand_id in predicted_mention.candidates:
                if self.entity_db.contains_entity(cand_id):
                    candidates.add(WikidataEntity(self.entity_db.get_entity(cand_id).name, 0, cand_id))

            predicted_entity_id = predicted_mention.entity_id
            predicted_entity_name = self.entity_db.get_entity(predicted_entity_id).name \
                if self.entity_db.contains_entity(predicted_entity_id) else "Unknown"
            predicted_entity_type = self.determine_entity_type(predicted_entity_id)
            predicted_entity = WikidataEntity(predicted_entity_name, 0, predicted_mention.entity_id,
                                              type=predicted_entity_type)

            if (span not in ground_truth_spans and expanded_span not in ground_truth_spans) and \
                    predicted_entity_id is not None and span[0] >= evaluation_span[0] and span[1] <= evaluation_span[1]:
                text = article.text[span[0]:span[1]]
                predicted_by = predicted_mention.linked_by
                contained = predicted_mention.contained
                case = Case(span, text, None, True, predicted_entity, contained=contained, candidates=candidates,
                            predicted_by=predicted_by, referenced_span=predicted_mention.referenced_span, factor=1)
                cases.append(case)

        return sorted(cases)

    def recursively_check_children_correctly_linked(self, label_id: int) -> bool:
        """
        Returns True if all paths in the tree from the root parent have a
        correctly predicted entity on them.

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
        >>> cg.recursively_check_children_correctly_linked(1)
        True
        >>> p1 = EntityMention((0, 2), "Test", "Q3")
        >>> p2 = EntityMention((4, 6), "Test", "Q9")
        >>> p3 = EntityMention((8, 10), "Test", "Q7")
        >>> cg.all_predictions ={p1.span: p1, p2.span: p2, p3.span: p3}
        >>> cg.recursively_check_children_correctly_linked(1)
        False
        >>> p1 = EntityMention((0, 2), "Test", "Q3")
        >>> p2 = EntityMention((4, 10), "Test", "Q5")
        >>> cg.all_predictions ={p1.span: p1, p2.span: p2}
        >>> cg.recursively_check_children_correctly_linked(1)
        True
        >>> p1 = EntityMention((0, 2), "Test", "Q3")
        >>> p3 = EntityMention((8, 10), "Test", "Q7")
        >>> cg.all_predictions ={p1.span: p1, p3.span: p3}
        >>> cg.recursively_check_children_correctly_linked(1)
        False
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

        if pred_entity_id and label.entity_id == pred_entity_id:
            return True
        elif label.children:
            result = True
            for child_id in label.children:
                result = result and self.recursively_check_children_correctly_linked(child_id)
            return result
        return False

    def recursively_check_children_correctly_detected(self, label_id: int) -> bool:
        """
        Returns True if all paths in the tree from the root parent have a
        correctly detected mention on them.
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
        >>> cg.recursively_check_children_correctly_detected(1)
        True
        >>> p1 = EntityMention((0, 2), "Test", "Q3")
        >>> p2 = EntityMention((4, 6), "Test", "Q9")
        >>> p3 = EntityMention((8, 10), "Test", "Q7")
        >>> cg.all_predictions ={p1.span: p1, p2.span: p2, p3.span: p3}
        >>> cg.recursively_check_children_correctly_detected(1)
        True
        >>> p1 = EntityMention((0, 2), "Test", "Q3")
        >>> p2 = EntityMention((4, 10), "Test", "Q5")
        >>> cg.all_predictions ={p1.span: p1, p2.span: p2}
        >>> cg.recursively_check_children_correctly_detected(1)
        True
        >>> p1 = EntityMention((0, 2), "Test", "Q3")
        >>> p3 = EntityMention((8, 10), "Test", "Q7")
        >>> cg.all_predictions ={p1.span: p1, p3.span: p3}
        >>> cg.recursively_check_children_correctly_detected(1)
        False
        """
        label = self.label_dict[label_id]
        expanded_label_span = word_boundary(label.span, self.article.text)

        # Check if label span or expanded label span is in predictions
        if label.span in self.all_predictions or expanded_label_span in self.all_predictions:
            return True
        elif label.children:
            result = True
            for child_id in label.children:
                result = result and self.recursively_check_children_correctly_detected(child_id)
            return result
        return False

    def recursively_determine_factor(self, label_id: int, ignore_siblings=False) -> int:
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

        if pred_entity_id and label.entity_id == pred_entity_id:
            # Factor is certainly 1 if the mention was correctly detected and linked. All child labels have factor 0.
            # Return is only ok if child labels not occurring in the factor dictionary are assigned factor 0.
            # Otherwise we need to go through all child labels.
            factor = 1
            self.factor_dict[label_id] = factor
            return factor

        biggest_child_factor = 0
        if label.children:
            for child_id in label.children:
                biggest_child_factor = max(biggest_child_factor, self.recursively_determine_factor(child_id))

        if label.parent is None:
            # We are at the root node. Iff none of the children were detected, show the root node
            factor = 1 if biggest_child_factor == 0 else 0
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
            elif not pred_entity_id and not ignore_siblings and biggest_child_factor == 0:
                # If the mention was not detected, but siblings were, factor is 1.
                # If parent span is the same as label span, the label can not have any siblings, so the factor is 0
                siblings = self.label_dict[label.parent].children[:]
                siblings.remove(label_id)
                for sibling_id in siblings:
                    sibling_factor = self.recursively_determine_factor(sibling_id, ignore_siblings=True)
                    if sibling_factor > 0:
                        factor = 1
                        break

            self.factor_dict[label_id] = factor
            return max(biggest_child_factor, factor)
