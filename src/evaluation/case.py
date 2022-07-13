import logging
from typing import Optional, Tuple, Set, Dict, List
from enum import Enum
import json

from src.evaluation.groundtruth_label import GroundtruthLabel
from src.models.wikidata_entity import WikidataEntity
from src.evaluation.mention_type import get_mention_type


logger = logging.getLogger("main." + __name__.split(".")[-1])


class EvaluationMode(Enum):
    IGNORED = "IGNORED"
    OPTIONAL = "OPTIONAL"
    REQUIRED = "REQUIRED"


class EvaluationType(Enum):
    TP = "TP"
    FP = "FP"
    FN = "FN"


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
    FALSE_DETECTION_LOWERCASED = "FALSE_DETECTION_LOWERCASED"
    FALSE_DETECTION_GROUNDTRUTH_UNKNOWN = "FALSE_DETECTION_GROUNDTRUTH_UNKNOWN"
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
                 predicted_entity: Optional[WikidataEntity],
                 candidates: Set[WikidataEntity],
                 predicted_by: str,
                 error_labels: Optional[Set[ErrorLabel]] = None,
                 factor: Optional[float] = None,
                 child_linking_eval_types: Optional[Dict[EvaluationMode, Set[EvaluationType]]] = None,
                 child_ner_eval_types: Optional[Dict[EvaluationMode, Set[EvaluationType]]] = None):
        self.span = span
        self.text = text
        self.true_entity = true_entity
        self.predicted_entity = predicted_entity
        self.candidates = candidates
        self.predicted_by = predicted_by
        self.optional = true_entity.is_optional() if true_entity else False
        self.error_labels = set() if error_labels is None else error_labels
        self.mention_type = get_mention_type(text, true_entity, predicted_entity)
        self.factor = 1 if factor is None else factor
        self.child_linking_eval_types = child_linking_eval_types
        self.child_ner_eval_types = child_ner_eval_types
        self.linking_eval_types = {}
        self.ner_eval_types = {}
        self.compute_eval_types()

    def compute_eval_types(self):
        for mode in EvaluationMode:
            self.linking_eval_types[mode] = self._get_linking_eval_type(mode)
            self.ner_eval_types[mode] = self._get_ner_eval_type(mode)

    def set_child_linking_eval_types(self, child_eval_types=Dict[EvaluationMode, Set[EvaluationType]]):
        self.child_linking_eval_types = child_eval_types

    def set_child_ner_eval_types(self, child_eval_types=Set[EvaluationType]):
        self.child_ner_eval_types = child_eval_types

    def _get_linking_eval_type(self, eval_mode: EvaluationMode) -> List[EvaluationType]:
        if self.factor == 0:
            if self.child_linking_eval_types is None:
                # Child evaluation types have not been initialized (yet) so the
                # parent evaluation type can't be inferred
                return []

            # Get eval type of child cases with factor != 0.
            if EvaluationType.FN in self.child_linking_eval_types[eval_mode]:
                # Return FN if at least one is FN
                return [EvaluationType.FN]
            elif EvaluationType.TP in self.child_linking_eval_types[eval_mode] and \
                    len(self.child_linking_eval_types[eval_mode]) == 1:
                # Return TP if all are TP (or None).
                return [EvaluationType.TP]
            else:
                # Don't return FP. FPs are counted for all cases with factor != 0 so there's
                # no special treatment of the parent needed
                # This case should never happen, since cases with factor = 0 are always caess
                # with a GT and therefore have at least one FN or TP.
                logger.warning("Evaluation case with factor = 0 is neither FN nor TP.")
                return []

        if not self.has_ground_truth():
            if self.has_prediction():
                if eval_mode in (EvaluationMode.IGNORED, EvaluationMode.OPTIONAL) and not self.prediction_is_known():
                    # --- / unk: IGN, OPT
                    return []
                # --- / unk: REQ
                # --- / ent: IGN, OPT, REQ
                return [EvaluationType.FP]
            else:
                # The case (not self.predicted_entity) should not happen
                # but just to be save
                return []

        if not self.has_prediction():
            if self.is_optional():
                if eval_mode in (EvaluationMode.IGNORED, EvaluationMode.OPTIONAL):
                    # optent / ---: IGN, OPT
                    # optunk / ---: IGN, OPT
                    return []
                else:
                    # optent / ---: REQ
                    # optunk / ---: REQ
                    return [EvaluationType.FN]
            elif self.has_ground_truth():
                if eval_mode in (EvaluationMode.IGNORED, EvaluationMode.OPTIONAL) and not self.ground_truth_is_known():
                    # unk / ---: IGN, OPT
                    return []
                # unk / ---: REQ
                # ent / ---: IGN, OPT, REQ
                return [EvaluationType.FN]
            else:
                # The case (not self.true_entity) should not happen
                # but just to be save
                return []

        if self.is_optional():
            if self.prediction_is_known():
                if eval_mode == EvaluationMode.IGNORED:
                    # optent / ent: IGN
                    # optunk / ent: IGN
                    return [EvaluationType.FP]
                elif self.true_entity.entity_id == self.predicted_entity.entity_id or \
                        self.is_true_quantity_or_datetime():
                    if eval_mode == EvaluationMode.OPTIONAL:
                        # optent / ent: OPT (true)
                        return []
                    else:
                        # optent / ent: REQ (true)
                        return [EvaluationType.TP]
                else:
                    # optent / ent: OPT, REQ (false)
                    # optunk / ent: OPT, REQ
                    return [EvaluationType.FN, EvaluationType.FP]
            else:
                if self.ground_truth_is_known() or self.ground_truth_is_datetime_or_quantity():
                    if eval_mode == EvaluationMode.IGNORED:
                        # optent / unk: IGN
                        return []
                    else:
                        # optent / unk: OPT, REQ
                        return [EvaluationType.FN, EvaluationType.FP]
                else:
                    if eval_mode in (EvaluationMode.IGNORED, EvaluationMode.OPTIONAL):
                        # optunk / unk: IGN, OPT
                        return []
                    else:
                        # optunk / unk: REQ
                        return [EvaluationType.TP]
        elif self.ground_truth_is_known():
            if self.prediction_is_known():
                if self.true_entity.entity_id == self.predicted_entity.entity_id:
                    # ent / ent: IGN, OPT, REQ (true)
                    return [EvaluationType.TP]
                else:
                    # ent / ent: IGN, OPT, REQ (false)
                    return [EvaluationType.FN, EvaluationType.FP]
            else:
                if eval_mode == EvaluationMode.IGNORED:
                    # ent / unk: IGN
                    return [EvaluationType.FN]
                # ent / unk: OPT, REQ
                return [EvaluationType.FN, EvaluationType.FP]
        else:
            if self.prediction_is_known():
                if eval_mode == EvaluationMode.IGNORED:
                    # unk / ent: IGN
                    return [EvaluationType.FP]
                # unk / ent: OPT, REQ
                return [EvaluationType.FN, EvaluationType.FP]
            else:
                if eval_mode in (EvaluationMode.IGNORED, EvaluationMode.OPTIONAL):
                    # unk / unk: IGN, OPT
                    return []
                # unk / unk: REQ
                return[EvaluationType.TP]

    def _get_ner_eval_type(self, eval_mode: EvaluationMode) -> Optional[List[EvaluationType]]:
        if self.factor == 0:
            if self.child_ner_eval_types is None:
                # Child evaluation types have not been initialized (yet) so the
                # parent evaluation type can't be inferred
                return []

            # Get eval type of child cases with factor != 0.
            if EvaluationType.FN in self.child_ner_eval_types[eval_mode]:
                # Return FN if at least one is FN
                return [EvaluationType.FN]
            elif EvaluationType.TP in self.child_ner_eval_types[eval_mode] and \
                    len(self.child_ner_eval_types[eval_mode]) == 1:
                # Return TP if all are TP (or None).
                return [EvaluationType.TP]
            else:
                # Don't return FP. FPs are counted for all cases with factor != 0 so there's
                # no special treatment of the parent needed.
                # This case should never happen, since cases with factor = 0 are always caess
                # with a GT and therefore have at least one FN or TP.
                logger.warning("Evaluation case with factor = 0 is neither NER FN nor TP.")
                return []

        if not self.has_ground_truth():
            if self.has_prediction():
                if eval_mode in (EvaluationMode.IGNORED, EvaluationMode.OPTIONAL) and not self.prediction_is_known():
                    # --- / unk: IGN, OPT
                    return []
                # --- / unk: REQ
                # --- / ent: IGN, OPT, REQ
                return [EvaluationType.FP]
            else:
                # The case (not self.predicted_entity) should not happen
                # but just to be save
                return []

        if not self.has_prediction():
            if self.is_optional():
                if eval_mode in (EvaluationMode.IGNORED, EvaluationMode.OPTIONAL):
                    # optent / ---: IGN, OPT
                    # optunk / ---: IGN, OPT
                    return []
                else:
                    # optent / ---: REQ
                    # optunk / ---: REQ
                    return [EvaluationType.FN]
            elif self.has_ground_truth():
                if eval_mode in (EvaluationMode.IGNORED, EvaluationMode.OPTIONAL) and not self.ground_truth_is_known():
                    # unk / ---: IGN, OPT
                    return []
                # unk / ---: REQ
                # ent / ---: IGN, OPT, REQ
                return [EvaluationType.FN]
            else:
                # The case (not self.true_entity) should not happen
                # but just to be save
                return []

        if self.is_optional():
            if self.prediction_is_known():
                if eval_mode == EvaluationMode.IGNORED:
                    # optent / ent: IGN
                    # optunk / ent: IGN
                    return [EvaluationType.FP]
                elif eval_mode == EvaluationMode.OPTIONAL:
                    # optent / ent: OPT
                    # optunk / ent: OPT
                    return []
                else:
                    # optent / ent: OPT, REQ
                    # optunk / ent: OPT, REQ
                    return [EvaluationType.TP]
            else:
                if eval_mode in (EvaluationMode.IGNORED, EvaluationMode.OPTIONAL):
                    # optent / unk: IGN, OPT
                    # optunk / unk: IGN, OPT
                    return []
                else:
                    # optent / unk: REQ
                    # optunk / unk: REQ
                    return [EvaluationType.TP]
        elif self.ground_truth_is_known():
            if self.prediction_is_known():
                # ent / ent: IGN, OPT, REQ
                return [EvaluationType.TP]
            else:
                if eval_mode == EvaluationMode.IGNORED:
                    # ent / unk: IGN
                    return [EvaluationType.FN]
                # ent / unk: OPT, REQ
                return [EvaluationType.TP]
        else:
            if self.prediction_is_known():
                if eval_mode == EvaluationMode.IGNORED:
                    # unk / ent: IGN
                    return [EvaluationType.FP]
                # unk / ent: OPT, REQ
                return [EvaluationType.TP]
            else:
                if eval_mode in (EvaluationMode.IGNORED, EvaluationMode.OPTIONAL):
                    # unk / unk: IGN, OPT
                    return []
                # unk / unk: REQ
                return[EvaluationType.TP]

    def is_linking_tp(self, eval_mode: EvaluationMode) -> bool:
        return EvaluationType.TP in self.linking_eval_types[eval_mode]

    def is_linking_fp(self, eval_mode: EvaluationMode) -> bool:
        return EvaluationType.FP in self.linking_eval_types[eval_mode]

    def is_linking_fn(self, eval_mode: EvaluationMode) -> bool:
        return EvaluationType.FN in self.linking_eval_types[eval_mode]

    def is_ner_tp(self, eval_mode: EvaluationMode) -> bool:
        return EvaluationType.TP in self.ner_eval_types[eval_mode]

    def is_ner_fp(self, eval_mode: EvaluationMode) -> bool:
        return EvaluationType.FP in self.ner_eval_types[eval_mode]

    def is_ner_fn(self, eval_mode: EvaluationMode) -> bool:
        return EvaluationType.FN in self.ner_eval_types[eval_mode]

    def has_ground_truth(self) -> bool:
        return self.true_entity is not None

    def has_prediction(self) -> bool:
        return self.predicted_entity is not None

    def ground_truth_is_known(self) -> bool:
        return self.true_entity is not None and not self.true_entity.entity_id.startswith("Unknown") \
               and not self.true_entity.is_datetime() and not self.true_entity.is_quantity()

    def ground_truth_is_datetime_or_quantity(self):
        return self.true_entity and (self.true_entity.is_quantity() or self.true_entity.is_datetime())

    def prediction_is_known(self) -> bool:
        return self.predicted_entity is not None and not self.predicted_entity.is_nil()

    def has_relevant_ground_truth(self, eval_mode: EvaluationMode) -> bool:
        if eval_mode == EvaluationMode.IGNORED:
            return self.ground_truth_is_known() and not self.is_optional()
        else:
            return self.true_entity is not None

    def true_entity_is_candidate(self) -> bool:
        return self.true_entity.entity_id in set([cand.entity_id for cand in self.candidates])

    def n_candidates(self) -> int:
        return len(self.candidates)

    def is_true_quantity_or_datetime(self) -> bool:
        return self.true_entity and self.predicted_entity and self.true_entity.type == self.predicted_entity.type and \
               (self.true_entity.is_quantity() or self.true_entity.is_datetime())

    def is_optional(self) -> bool:
        return self.optional

    def is_coreference(self) -> bool:
        return self.mention_type.is_coreference()

    def add_error_label(self, error_label: ErrorLabel):
        self.error_labels.add(error_label)

    def __lt__(self, other) -> bool:
        return self.span < other.span

    def to_dict(self) -> Dict:
        data = {"span": self.span,
                "text": self.text,
                "candidates": [{"entity_id": cand.entity_id, "name": cand.name} for cand in sorted(self.candidates)],
                "predicted_by": self.predicted_by,
                "error_labels": sorted([label.value for label in self.error_labels]),
                "factor": self.factor,
                "linking_eval_types": {mode.value: [et.value for et in self.linking_eval_types[mode]]
                                       for mode in EvaluationMode},
                "ner_eval_types": {mode.value: [et.value for et in self.ner_eval_types[mode]]
                                   for mode in EvaluationMode},
                "optional": self.optional}
        if self.true_entity is not None:
            data["true_entity"] = self.true_entity.to_dict()
        if self.predicted_entity is not None:
            data["predicted_entity"] = {"entity_id": self.predicted_entity.entity_id,
                                        "name": self.predicted_entity.name,
                                        "type": self.predicted_entity.type}
        if self.mention_type is not None:
            data["mention_type"] = self.mention_type.value
        if self.child_linking_eval_types is not None:
            data["child_linking_eval_types"] = {m.value: [et.value for et in self.child_linking_eval_types[m]]
                                                for m in EvaluationMode}
        if self.child_ner_eval_types is not None:
            data["child_ner_eval_types"] = {m.value: [et.value for et in self.child_ner_eval_types[m]]
                                            for m in EvaluationMode}
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


def case_from_dict(data) -> Case:
    # eval_types are freshly computed.
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
    child_linking_eval_types = None
    if "child_linking_eval_types" in data:
        child_linking_eval_types = {EvaluationMode(m): set([EvaluationType(t)
                                                            for t in data["child_linking_eval_types"]])
                                    for m in data["child_linking_eval_types"]}
    child_ner_eval_types = None
    if "child_ner_eval_types" in data:
        child_ner_eval_types = {EvaluationMode(m): set([EvaluationType(t) for t in data["child_ner_eval_types"]])
                                for m in data["child_ner_eval_types"]}
    error_labels = {ERROR_LABELS[label] for label in data["error_labels"]}
    return Case(span=data["span"],
                text=data["text"],
                true_entity=true_entity,
                predicted_entity=pred_entity,
                candidates=candidates,
                predicted_by=data["predicted_by"],
                error_labels=error_labels,
                factor=data["factor"] if "factor" in data else 1,
                child_linking_eval_types=child_linking_eval_types,
                child_ner_eval_types=child_ner_eval_types)


def case_from_json(dump) -> Case:
    return case_from_dict(json.loads(dump))
