from typing import Optional, Tuple, Set, Dict
from enum import Enum
import json

from src.linkers.abstract_coref_linker import AbstractCorefLinker
from src.models.wikidata_entity import WikidataEntity
from src.evaluation.mention_type import MentionType


class CaseType(Enum):
    UNKNOWN_ENTITY = 0
    UNDETECTED = 1
    WRONG_CANDIDATES = 2
    CORRECT = 3
    WRONG = 4
    FALSE_DETECTION = 5


CASE_COLORS = {
    CaseType.UNKNOWN_ENTITY: None,
    CaseType.UNDETECTED: "blue",
    CaseType.WRONG_CANDIDATES: "yellow",
    CaseType.CORRECT: "green",
    CaseType.WRONG: "red",
    CaseType.FALSE_DETECTION: "cyan",
    "mixed": "magenta"
}


MENTION_TYPES = {
    "NAMED": MentionType.NAMED,
    "NOMINAL": MentionType.NOMINAL,
    "PRONOMINAL": MentionType.PRONOMINAL
}


class Case:
    def __init__(self,
                 span: Tuple[int, int],
                 true_entity: Optional[WikidataEntity],
                 detected: bool,
                 predicted_entity: Optional[WikidataEntity],
                 candidates: Set[WikidataEntity],
                 predicted_by: str,
                 mention_type: Optional[MentionType] = None,
                 contained: Optional[bool] = None,
                 is_true_coref: Optional[bool] = False,
                 correct_span_referenced: Optional[bool] = False,
                 referenced_span: Optional[Tuple[int, int]] = None):
        self.span = span
        self.true_entity = true_entity
        self.detected = detected
        self.predicted_entity = predicted_entity
        self.candidates = candidates
        self.eval_type = self._type()
        self.predicted_by = predicted_by
        self.mention_type = mention_type
        self.contained = contained
        self.is_true_coref = is_true_coref
        self.correct_span_referenced = correct_span_referenced
        self.referenced_span = referenced_span
        self.coref_type = self._coref_type()

    def has_ground_truth(self):
        return self.true_entity is not None

    def is_known_entity(self):
        return self.true_entity is not None and not self.true_entity.entity_id.startswith("Unknown")

    def is_detected(self):
        return self.detected

    def is_correct(self):
        return self.predicted_entity is not None and self.true_entity \
               and self.true_entity.entity_id == self.predicted_entity.entity_id

    def true_entity_is_candidate(self):
        return self.true_entity.entity_id in set([cand.entity_id for cand in self.candidates])

    def n_candidates(self):
        return len(self.candidates)

    def is_false_positive(self):
        return self.predicted_entity is not None and (self.true_entity is None or
                                                      self.true_entity.entity_id != self.predicted_entity.entity_id)

    def is_true_coreference(self):
        return self.is_true_coref

    def set_mention_type(self, mention_type: MentionType):
        self.mention_type = mention_type

    def _type(self) -> CaseType:
        if not self.has_ground_truth():
            return CaseType.FALSE_DETECTION
        if not self.is_known_entity():
            return CaseType.UNKNOWN_ENTITY
        if not self.is_detected():
            return CaseType.UNDETECTED
        if not self.true_entity_is_candidate():
            return CaseType.WRONG_CANDIDATES
        if self.is_correct():
            return CaseType.CORRECT
        else:
            return CaseType.WRONG

    def _coref_type(self) -> CaseType:
        if self.is_true_coreference():
            if not self.is_detected():
                return CaseType.UNDETECTED
            elif self.correct_span_referenced:
                return CaseType.CORRECT
            else:
                return CaseType.WRONG
        elif self.predicted_by == AbstractCorefLinker.IDENTIFIER:
            return CaseType.FALSE_DETECTION

    def __lt__(self, other) -> bool:
        return self.span < other.span

    def to_dict(self) -> Dict:
        data = {"span": self.span,
                "detected": self.detected,
                "candidates": [{"entity_id": cand.entity_id, "name": cand.name} for cand in sorted(self.candidates)],
                "predicted_by": self.predicted_by,
                "eval_type": self.eval_type.value}
        if self.true_entity is not None:
            data["true_entity"] = {"entity_id": self.true_entity.entity_id, "name": self.true_entity.name}
        if self.predicted_entity is not None:
            data["predicted_entity"] = {"entity_id": self.predicted_entity.entity_id,
                                        "name": self.predicted_entity.name}
        if self.is_true_coref is not None:
            data["is_true_coref"] = self.is_true_coref
        if self.correct_span_referenced is not None:
            data["correct_span_referenced"] = self.correct_span_referenced
        if self.referenced_span is not None:
            data["referenced_span"] = self.referenced_span
        if self.coref_type is not None:
            data["coref_type"] = self.coref_type.value
        if self.contained is not None:
            data["contained"] = self.contained
        if self.mention_type is not None:
            data["mention_type"] = self.mention_type.value
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


def case_from_dict(data) -> Case:
    true_entity = None
    if "true_entity" in data:
        true_entity = WikidataEntity(data["true_entity"]["name"], 0, data["true_entity"]["entity_id"], [])
    pred_entity = None
    if "predicted_entity" in data:
        pred_entity = WikidataEntity(data["predicted_entity"]["name"], 0, data["predicted_entity"]["entity_id"], [])
    candidates = set()
    if "candidates" in data:
        candidates = set([WikidataEntity(cand["name"], 0, cand["entity_id"], [])
                          for cand in data["candidates"]])
    return Case(span=data["span"],
                true_entity=true_entity,
                detected=data["detected"],
                predicted_entity=pred_entity,
                candidates=candidates,
                predicted_by=data["predicted_by"],
                mention_type=MENTION_TYPES[data["mention_type"]] if "mention_type" in data else None,
                contained=data["contained"] if "contained" in data else None,
                is_true_coref=data["is_true_coref"] if "is_true_coref" in data else None,
                correct_span_referenced=data["correct_span_referenced"] if "correct_span_referenced" in data else None,
                referenced_span=data["referenced_span"] if "referenced_span" in data else None)


def case_from_json(dump) -> Case:
    return case_from_dict(json.loads(dump))
