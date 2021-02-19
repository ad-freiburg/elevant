from typing import List

from src.evaluation.case import Case, ErrorLabel
from src.models.entity_database import EntityDatabase


def label_errors(text: str, cases: List[Case], entity_db: EntityDatabase):
    label_demonym_errors(text, cases, entity_db)
    label_rare_entity_errors(text, cases, entity_db)


def label_demonym_errors(text: str, cases: List[Case], entity_db: EntityDatabase):
    for case in cases:
        if not case.is_correct() and case.true_entity is not None:
            snippet = text[case.span[0]:case.span[1]]
            if entity_db.is_demonym(snippet):
                case.add_error_label(ErrorLabel.DEMONYM)


def label_rare_entity_errors(text: str, cases: List[Case], entity_db: EntityDatabase):
    for case in cases:
        if not case.is_correct() and case.true_entity is not None and case.predicted_entity is not None\
                and not case.is_true_coreference():
            snippet = text[case.span[0]:case.span[1]]
            if not entity_db.is_demonym(snippet):
                if entity_db.get_sitelink_count(case.true_entity.entity_id) \
                        < entity_db.get_sitelink_count(case.predicted_entity.entity_id):
                    case.add_error_label(ErrorLabel.RARE)
