import logging
from typing import Optional, Tuple, Set, Dict, List
from enum import Enum
import json

from elevant.evaluation.groundtruth_label import GroundtruthLabel
from elevant.models.wikidata_entity import WikidataEntity
from elevant.evaluation.mention_type import get_mention_type
from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper

logger = logging.getLogger("main." + __name__.split(".")[-1])


class EvaluationMode(Enum):
    IGNORED = "IGNORED"
    REQUIRED = "REQUIRED"


class EvaluationType(Enum):
    TP = "TP"
    FP = "FP"
    FN = "FN"


class ErrorLabel(Enum):
    # detection
    NER_FN = "NER_FN"
    NER_FN_LOWERCASED = "NER_FN_LOWERCASED"
    NER_FN_PARTIALLY_INCLUDED = "NER_FN_PARTIALLY_INCLUDED"
    NER_FN_PARTIAL_OVERLAP = "NER_FN_PARTIAL_OVERLAP"
    NER_FN_OTHER = "NER_FN_OTHER"
    AVOIDED_NER_FN = "AVOIDED_NER_FN"  # These are NER TP
    AVOIDED_NER_FN_LOWERCASED = "AVOIDED_NER_FN_LOWERCASED"  # These are lowercased NER TP
    AVOIDED_NER_FN_PARTIALLY_INCLUDED = "AVOIDED_NER_FN_PARTIALLY_INCLUDED"
    AVOIDED_NER_FN_PARTIAL_OVERLAP = "AVOIDED_NER_FN_PARTIAL_OVERLAP"
    AVOIDED_NER_FN_OTHER = "AVOIDED_NER_FN_OTHER"
    # disambiguation
    DISAMBIGUATION_WRONG = "DISAMBIGUATION_WRONG"
    DISAMBIGUATION_CORRECT = "DISAMBIGUATION_CORRECT"
    DISAMBIGUATION_DEMONYM_CORRECT = "DISAMBIGUATION_DEMONYM_CORRECT"
    DISAMBIGUATION_DEMONYM_WRONG = "DISAMBIGUATION_DEMONYM_WRONG"
    DISAMBIGUATION_METONYMY_CORRECT = "DISAMBIGUATION_METONYMY_CORRECT"
    DISAMBIGUATION_METONYMY_WRONG = "DISAMBIGUATION_METONYMY_WRONG"
    DISAMBIGUATION_PARTIAL_NAME_CORRECT = "DISAMBIGUATION_PARTIAL_NAME_CORRECT"
    DISAMBIGUATION_PARTIAL_NAME_WRONG = "DISAMBIGUATION_PARTIAL_NAME_WRONG"
    DISAMBIGUATION_RARE_CORRECT = "DISAMBIGUATION_RARE_CORRECT"
    DISAMBIGUATION_RARE_WRONG = "DISAMBIGUATION_RARE_WRONG"
    DISAMBIGUATION_OTHER_WRONG = "DISAMBIGUATION_OTHER_WRONG"
    DISAMBIGUATION_OTHER_CORRECT = "DISAMBIGUATION_OTHER_CORRECT"
    # disambiguation candidates
    DISAMBIGUATION_CANDIDATES_WRONG = "DISAMBIGUATION_CANDIDATES_WRONG"
    DISAMBIGUATION_CANDIDATES_CORRECT = "DISAMBIGUATION_CANDIDATES_CORRECT"
    DISAMBIGUATION_MULTI_CANDIDATES_CORRECT = "DISAMBIGUATION_MULTI_CANDIDATES_CORRECT"
    DISAMBIGUATION_MULTI_CANDIDATES_WRONG = "DISAMBIGUATION_MULTI_CANDIDATES_WRONG"
    # false positives
    NER_FP = "NER_FP"
    NER_FP_LOWERCASED = "NER_FP_LOWERCASED"
    NER_FP_GROUNDTRUTH_UNKNOWN = "NER_FP_GROUNDTRUTH_UNKNOWN"
    NER_FP_OTHER = "NER_FP_OTHER"
    NER_FP_WRONG_SPAN = "NER_FP_WRONG_SPAN"
    AVOIDED_NER_FP_GROUNDTRUTH_UNKNOWN = "AVOIDED_NER_FP_GROUNDTRUTH_UNKNOWN"
    AVOIDED_NER_FP_WRONG_SPAN = "AVOIDED_NER_FP_WRONG_SPAN"
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
                 error_labels: Optional[Dict[EvaluationMode, Set[ErrorLabel]]] = None,
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
        self.error_labels = {m: set() for m in EvaluationMode} if error_labels is None else error_labels
        self.mention_type = get_mention_type(text, true_entity, predicted_entity)
        self.factor = 1 if factor is None else factor
        self.child_linking_eval_types = child_linking_eval_types
        self.child_ner_eval_types = child_ner_eval_types
        self.has_non_optional_children = False
        self.linking_eval_types = {}
        self.ner_eval_types = {}
        self.compute_eval_types()

    def compute_eval_types(self):
        for mode in EvaluationMode:
            self.linking_eval_types[mode] = self._get_linking_eval_type(mode)
            self.ner_eval_types[mode] = self._get_ner_eval_type(mode)

    def set_child_linking_eval_types(self, child_eval_types: Dict[EvaluationMode, Set[EvaluationType]]):
        self.child_linking_eval_types = child_eval_types

    def set_child_ner_eval_types(self, child_eval_types: Set[EvaluationType]):
        self.child_ner_eval_types = child_eval_types

    def set_has_non_optional_children(self, has_non_optional_children):
        self.has_non_optional_children = has_non_optional_children

    def _get_linking_eval_type(self, eval_mode: EvaluationMode) -> List[EvaluationType]:
        if self.factor == 0:
            if self.child_linking_eval_types is None:
                # Child evaluation types have not been initialized (yet) so the
                # parent evaluation type can't be inferred
                # This is always the case for 0-factor cases with a non-root GT label
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
                # no special treatment of the parent needed.
                # This case should never happen, since cases with factor = 0 are always cases
                # with a GT and therefore have at least one FN or TP.
                # Unless children are unknown and mode is IGNORED.
                return []

        if not self.has_ground_truth():
            if self.has_prediction():
                if eval_mode == EvaluationMode.IGNORED and not self.prediction_is_known():
                    # --- / unk: IGN
                    return []
                # --- / unk: REQ
                # --- / ent: IGN, REQ
                return [EvaluationType.FP]
            else:
                # The case (not self.predicted_entity) should not happen
                # but just to be safe
                return []

        if not self.has_prediction():
            if self.is_optional() and not self.has_non_optional_children:
                # An optional ground truth label without corresponding prediction might still be
                # an FN if it has non-optional children (often the case with descriptive GT labels)
                # optent / ---: IGN, REQ
                # optunk / ---: IGN, REQ
                return []
            elif self.has_ground_truth():
                if eval_mode == EvaluationMode.IGNORED and not self.ground_truth_has_known_entity_id():
                    # unk / ---: IGN
                    return []
                # unk / ---: REQ
                # ent / ---: IGN, REQ
                return [EvaluationType.FN]
            else:
                # The case (not self.true_entity) should not happen
                # but just to be safe
                return []

        if self.is_optional():
            if self.prediction_is_known():
                if (self.ground_truth_has_known_entity_id() and self.true_entity.entity_id == self.predicted_entity.entity_id) or \
                        self.is_true_quantity_or_datetime():
                    # optent / ent: IGN, REQ (true)
                    return []
                else:
                    # optent / ent: IGN, REQ (false)
                    # optunk / ent: IGN, REQ
                    return [EvaluationType.FP]
            else:
                if (self.ground_truth_has_known_entity_id() or self.ground_truth_is_datetime_or_quantity()) and \
                        eval_mode == EvaluationMode.REQUIRED:
                    # optent / unk: REQ
                    return [EvaluationType.FP]
                # optent / unk: IGN
                # optunk / unk: IGN
                # optunk / unk: REQ
                return []
        elif self.ground_truth_has_known_entity_id():
            if self.prediction_is_known():
                if self.true_entity.entity_id == self.predicted_entity.entity_id:
                    # ent / ent: IGN, REQ (true)
                    return [EvaluationType.TP]
                else:
                    # ent / ent: IGN, REQ (false)
                    return [EvaluationType.FN, EvaluationType.FP]
            else:
                if eval_mode == EvaluationMode.IGNORED:
                    # ent / unk: IGN
                    return [EvaluationType.FN]
                # ent / unk: REQ
                return [EvaluationType.FN, EvaluationType.FP]
        else:
            if self.prediction_is_known():
                if eval_mode == EvaluationMode.IGNORED:
                    # unk / ent: IGN
                    return [EvaluationType.FP]
                # unk / ent: REQ
                return [EvaluationType.FN, EvaluationType.FP]
            else:
                if eval_mode == EvaluationMode.IGNORED:
                    # unk / unk: IGN
                    return []
                # unk / unk: REQ
                return [EvaluationType.TP]

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
                # This case should never happen, since cases with factor = 0 are always cases
                # with a GT and therefore have at least one FN or TP.
                # Unless children are unknown and mode is IGNORED.
                return []

        if not self.has_ground_truth():
            if self.has_prediction():
                if eval_mode == EvaluationMode.IGNORED and not self.prediction_is_known():
                    # --- / unk: IGN
                    return []
                # --- / unk: REQ
                # --- / ent: IGN, REQ
                return [EvaluationType.FP]
            else:
                # The case (not self.predicted_entity) should not happen
                # but just to be safe
                return []

        if not self.has_prediction():
            if self.is_optional() and not self.has_non_optional_children:
                # An optional ground truth label without corresponding prediction might still be
                # an FN if it has non-optional children (often the case with descriptive GT labels)
                # optent / ---: IGN, REQ
                # optunk / ---: IGN, REQ
                return []
            elif self.has_ground_truth():
                if eval_mode == EvaluationMode.IGNORED and not self.ground_truth_has_known_entity_id():
                    # unk / ---: IGN
                    return []
                # unk / ---: REQ
                # ent / ---: IGN, REQ
                return [EvaluationType.FN]
            else:
                # The case (not self.true_entity) should not happen
                # but just to be safe
                return []

        if self.is_optional():
            if not (self.ground_truth_has_known_entity_id() or self.ground_truth_is_datetime_or_quantity()) and \
                    self.prediction_is_known() and eval_mode == EvaluationMode.IGNORED:
                # optunk / ent: IGN
                return [EvaluationType.FP]
            # optent / ent: IGN, REQ
            # optent / unk: IGN, REQ
            # optunk / ent: REQ
            # optunk / unk: IGN, REQ
            return []
        elif self.ground_truth_has_known_entity_id():
            if self.prediction_is_known():
                # ent / ent: IGN, REQ
                return [EvaluationType.TP]
            else:
                if eval_mode == EvaluationMode.IGNORED:
                    # ent / unk: IGN
                    return [EvaluationType.FN]
                # ent / unk: REQ
                return [EvaluationType.TP]
        else:
            if self.prediction_is_known():
                if eval_mode == EvaluationMode.IGNORED:
                    # unk / ent: IGN
                    return [EvaluationType.FP]
                # unk / ent: REQ
                return [EvaluationType.TP]
            else:
                if eval_mode == EvaluationMode.IGNORED:
                    # unk / unk: IGN
                    return []
                # unk / unk: REQ
                return [EvaluationType.TP]

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

    def ground_truth_has_known_entity_id(self) -> bool:
        return self.true_entity is not None and not KnowledgeBaseMapper.is_unknown_entity(self.true_entity.entity_id) \
               and not self.true_entity.is_datetime() and not self.true_entity.is_quantity()

    def ground_truth_is_unknown_entity(self) -> bool:
        return self.true_entity is None or KnowledgeBaseMapper.is_unknown_entity(self.true_entity.entity_id)

    def ground_truth_is_datetime_or_quantity(self):
        return self.true_entity and (self.true_entity.is_quantity() or self.true_entity.is_datetime())

    def prediction_is_known(self) -> bool:
        return (self.predicted_entity is not None and
                not KnowledgeBaseMapper.is_unknown_entity(self.predicted_entity.entity_id))

    def has_relevant_ground_truth(self, eval_mode: EvaluationMode) -> bool:
        if eval_mode == EvaluationMode.IGNORED:
            return self.ground_truth_has_known_entity_id() and not self.is_optional()
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

    def add_error_label(self, error_label: ErrorLabel, eval_mode: EvaluationMode):
        self.error_labels[eval_mode].add(error_label)

    def __lt__(self, other) -> bool:
        return self.span < other.span

    def to_dict(self) -> Dict:
        data = {"span": self.span,
                "text": self.text,
                "candidates": [{"entity_id": cand.entity_id, "name": cand.name} for cand in sorted(self.candidates)],
                "predicted_by": self.predicted_by,
                "error_labels": {mode.value: sorted([label.value for label in self.error_labels[mode]])
                                 for mode in EvaluationMode},
                "factor": self.factor,
                "linking_eval_types": {mode.value: sorted([et.value for et in self.linking_eval_types[mode]])
                                       for mode in EvaluationMode},
                "ner_eval_types": {mode.value: sorted([et.value for et in self.ner_eval_types[mode]])
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
            data["child_linking_eval_types"] = {m.value: sorted([et.value for et in self.child_linking_eval_types[m]])
                                                for m in EvaluationMode}
        if self.child_ner_eval_types is not None:
            data["child_ner_eval_types"] = {m.value: sorted([et.value for et in self.child_ner_eval_types[m]])
                                            for m in EvaluationMode}
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


def case_from_dict(data) -> Case:
    # eval_types are freshly computed.
    true_entity = None
    if "true_entity" in data:
        gt_label_id = data["true_entity"]["id"]
        gt_entity_id = data["true_entity"]["entity_id"]
        gt_span = data["true_entity"]["span"]
        gt_name = data["true_entity"]["name"]
        gt_type = data["true_entity"]["type"]
        gt_parent = data["true_entity"]["parent"] if "parent" in data["true_entity"] else None
        gt_children = data["true_entity"]["children"] if "children" in data["true_entity"] else None
        gt_optional = data["true_entity"]["optional"] if "optional" in data["true_entity"] else False
        gt_coref = data["true_entity"]["coref"] if "coref" in data["true_entity"] else None
        gt_desc = data["true_entity"]["desc"] if "desc" in data["true_entity"] else False
        true_entity = GroundtruthLabel(gt_label_id, gt_span, gt_entity_id, gt_name, parent=gt_parent,
                                       children=gt_children, optional=gt_optional, type=gt_type, coref=gt_coref,
                                       desc=gt_desc)
    pred_entity = None
    if "predicted_entity" in data:
        pred_entity = WikidataEntity(data["predicted_entity"]["entity_id"], data["predicted_entity"]["name"])
    candidates = set()
    if "candidates" in data:
        candidates = set([WikidataEntity(cand["entity_id"], cand["name"]) for cand in data["candidates"]])
    child_linking_eval_types = None
    if "child_linking_eval_types" in data:
        child_linking_eval_types = {EvaluationMode(m): set([EvaluationType(t)
                                                            for t in data["child_linking_eval_types"][m]])
                                    for m in data["child_linking_eval_types"]}
    child_ner_eval_types = None
    if "child_ner_eval_types" in data:
        child_ner_eval_types = {EvaluationMode(m): set([EvaluationType(t) for t in data["child_ner_eval_types"][m]])
                                for m in data["child_ner_eval_types"]}
    error_labels = {EvaluationMode(m): {ERROR_LABELS[label] for label in data["error_labels"][m]}
                    for m in data["error_labels"]}
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
