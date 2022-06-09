from typing import Optional, Tuple, Set, Dict
from enum import Enum
import json

from src.evaluation.groundtruth_label import GroundtruthLabel
from src.models.wikidata_entity import WikidataEntity
from src.evaluation.mention_type import get_mention_type


JOKER_LABELS = ("DATETIME", "QUANTITY")


class ErrorLabel(Enum):
    # detection
    UNDETECTED = "UNDETECTED"
    UNDETECTED_LOWERCASE = "UNDETECTED_LOWERCASE"
    UNDETECTED_PARTIALLY_INCLUDED = "UNDETECTED_PARTIALLY_INCLUDED"
    UNDETECTED_PARTIAL_OVERLAP = "UNDETECTED_PARTIAL_OVERLAP"
    UNDETECTED_OTHER = "UNDETECTED_OTHER"
    # disambiguation
    DISAMBIGUATION_WRONG = "DISAMBIGUATION_WRONG"
    DISAMBIGUATION_DEMONYM_CORRECT = "DISAMBIGUATION_DEMONYM_CORRECT"
    DISAMBIGUATION_DEMONYM_WRONG = "DISAMBIGUATION_DEMONYM_WRONG"
    DISAMBIGUATION_METONYMY_CORRECT = "DISAMBIGUATION_METONYMY_CORRECT"
    DISAMBIGUATION_METONYMY_WRONG = "DISAMBIGUATION_METONYMY_WRONG"
    DISAMBIGUATION_PARTIAL_NAME_CORRECT = "DISAMBIGUATION_PARTIAL_NAME_CORRECT"
    DISAMBIGUATION_PARTIAL_NAME_WRONG = "DISAMBIGUATION_PARTIAL_NAME_WRONG"
    DISAMBIGUATION_RARE_CORRECT = "DISAMBIGUATION_RARE_CORRECT"
    DISAMBIGUATION_RARE_WRONG = "DISAMBIGUATION_RARE_WRONG"
    DISAMBIGUATION_WRONG_OTHER = "DISAMBIGUATION_WRONG_OTHER"
    # disambiguation candidates
    DISAMBIGUATION_WRONG_CANDIDATES = "DISAMBIGUATION_WRONG_CANDIDATES"
    DISAMBIGUATION_MULTI_CANDIDATES_CORRECT = "DISAMBIGUATION_MULTI_CANDIDATES_CORRECT"
    DISAMBIGUATION_MULTI_CANDIDATES_WRONG = "DISAMBIGUATION_MULTI_CANDIDATES_WRONG"
    # false positives
    FALSE_DETECTION = "FALSE_DETECTION"
    FALSE_DETECTION_ABSTRACT_ENTITY = "FALSE_DETECTION_ABSTRACT_ENTITY"
    FALSE_DETECTION_UNKNOWN_ENTITY = "FALSE_DETECTION_UNKNOWN_ENTITY"
    FALSE_DETECTION_OTHER = "FALSE_DETECTION_OTHER"
    FALSE_DETECTION_WRONG_SPAN = "FALSE_DETECTION_WRONG_SPAN"
    # other
    HYPERLINK_CORRECT = "HYPERLINK_CORRECT"
    HYPERLINK_WRONG = "HYPERLINK_WRONG"
    # coreference
    COREFERENCE_FALSE_DETECTION = "COREFERENCE_FALSE_DETECTION"
    COREFERENCE_REFERENCE_WRONGLY_DISAMBIGUATED = "COREFERENCE_REFERENCE_WRONGLY_DISAMBIGUATED"
    COREFERENCE_WRONG_MENTION_REFERENCED = "COREFERENCE_WRONG_MENTION_REFERENCED"
    COREFERENCE_UNDETECTED = "COREFERENCE_UNDETECTED"


ERROR_LABELS = {
    error_label.value: error_label for error_label in ErrorLabel
}


class Case:
    def __init__(self,
                 span: Tuple[int, int],
                 text: str,
                 true_entity: Optional[GroundtruthLabel],
                 detected: bool,
                 predicted_entity: Optional[WikidataEntity],
                 candidates: Set[WikidataEntity],
                 predicted_by: str,
                 contained: Optional[bool] = None,
                 is_true_coref: Optional[bool] = False,
                 correct_span_referenced: Optional[bool] = False,
                 referenced_span: Optional[Tuple[int, int]] = None,
                 error_labels: Optional[Set[ErrorLabel]] = None,
                 factor: Optional[float] = None,
                 children_correctly_linked: Optional[bool] = None,
                 children_correctly_detected: Optional[bool] = None):
        self.span = span
        self.text = text
        self.true_entity = true_entity
        self.detected = detected
        self.predicted_entity = predicted_entity
        self.candidates = candidates
        self.predicted_by = predicted_by
        self.contained = contained
        self.is_true_coref = is_true_coref
        self.correct_span_referenced = correct_span_referenced
        self.referenced_span = referenced_span
        self.optional = true_entity.optional if true_entity else False
        self.children_correctly_linked = children_correctly_linked
        self.children_correctly_detected = children_correctly_detected
        self.error_labels = set() if error_labels is None else error_labels
        self.mention_type = get_mention_type(text, true_entity, predicted_entity)
        self.factor = 1 if factor is None else factor

    def has_ground_truth(self) -> bool:
        return self.true_entity is not None

    def has_predicted_entity(self) -> bool:
        return self.predicted_entity is not None and not self.predicted_entity.is_nil()

    def is_known_entity(self) -> bool:
        return self.true_entity is not None and not self.true_entity.entity_id.startswith("Unknown") \
               and not self.true_entity.is_datetime() and not self.true_entity.is_quantity()

    def is_nil_entity(self) -> bool:
        return self.predicted_entity is not None and self.predicted_entity.is_nil()

    def is_detected(self) -> bool:
        return self.detected

    def is_correct(self) -> bool:
        return self.has_predicted_entity() and self.true_entity \
               and self.true_entity.entity_id == self.predicted_entity.entity_id \
               or self.children_correctly_linked is True

    def true_entity_is_candidate(self) -> bool:
        return self.true_entity.entity_id in set([cand.entity_id for cand in self.candidates])

    def n_candidates(self) -> int:
        return len(self.candidates)

    def is_false_positive(self) -> bool:
        return not self.is_correct() and self.has_predicted_entity() and not self.is_true_quantity_or_datetime()

    def is_false_negative(self) -> bool:
        return not self.is_correct() and self.has_ground_truth() and self.is_known_entity() and not self.is_optional()

    def is_true_coreference(self) -> bool:
        return self.is_true_coref

    def is_true_quantity_or_datetime(self) -> bool:
        return self.true_entity and self.predicted_entity and self.true_entity.type == self.predicted_entity.type and \
               (self.true_entity.is_quantity() or self.true_entity.is_datetime())

    def is_optional(self) -> bool:
        return self.optional or self.true_entity and (self.true_entity.is_quantity() or self.true_entity.is_datetime())

    def add_error_label(self, error_label: ErrorLabel):
        self.error_labels.add(error_label)

    def __lt__(self, other) -> bool:
        return self.span < other.span

    def to_dict(self) -> Dict:
        data = {"span": self.span,
                "text": self.text,
                "detected": self.detected,
                "candidates": [{"entity_id": cand.entity_id, "name": cand.name} for cand in sorted(self.candidates)],
                "predicted_by": self.predicted_by,
                "error_labels": sorted([label.value for label in self.error_labels]),
                "factor": self.factor,
                "children_correctly_linked": self.children_correctly_linked,
                "children_correctly_detected": self.children_correctly_detected}
        if self.true_entity is not None:
            data["true_entity"] = self.true_entity.to_dict()
        if self.predicted_entity is not None:
            data["predicted_entity"] = {"entity_id": self.predicted_entity.entity_id,
                                        "name": self.predicted_entity.name,
                                        "type": self.predicted_entity.type}
        if self.is_true_coref is not None:
            data["is_true_coref"] = self.is_true_coref
        if self.correct_span_referenced is not None:
            data["correct_span_referenced"] = self.correct_span_referenced
        if self.referenced_span is not None:
            data["referenced_span"] = self.referenced_span
        if self.contained is not None:
            data["contained"] = self.contained
        if self.mention_type is not None:
            data["mention_type"] = self.mention_type.value
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def is_coreference(self) -> bool:
        return self.mention_type.is_coreference()

    def is_not_coreference(self) -> bool:
        return not self.is_coreference()


def case_from_dict(data) -> Case:
    true_entity = None
    if "true_entity" in data:
        true_entity = WikidataEntity(data["true_entity"]["name"], 0, data["true_entity"]["entity_id"])
    pred_entity = None
    if "predicted_entity" in data:
        pred_entity = WikidataEntity(data["predicted_entity"]["name"], 0, data["predicted_entity"]["entity_id"])
    candidates = set()
    if "candidates" in data:
        candidates = set([WikidataEntity(cand["name"], 0, cand["entity_id"])
                          for cand in data["candidates"]])
    error_labels = {ERROR_LABELS[label] for label in data["error_labels"]}
    return Case(span=data["span"],
                text=data["text"],
                true_entity=true_entity,
                detected=data["detected"],
                predicted_entity=pred_entity,
                candidates=candidates,
                predicted_by=data["predicted_by"],
                contained=data["contained"] if "contained" in data else None,
                is_true_coref=data["is_true_coref"] if "is_true_coref" in data else None,
                correct_span_referenced=data["correct_span_referenced"] if "correct_span_referenced" in data else None,
                referenced_span=data["referenced_span"] if "referenced_span" in data else None,
                error_labels=error_labels,
                factor=data["factor"] if "factor" in data else 1,
                children_correctly_linked=data["children_correctly_linked"] if "children_correctly_linked" in data else False,
                children_correctly_detected=data["children_correctly_detected"] if "children_correctly_detected" in data else False)


def case_from_json(dump) -> Case:
    return case_from_dict(json.loads(dump))
