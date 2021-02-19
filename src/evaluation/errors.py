from typing import List

from src.evaluation.case import Case, ErrorLabel
from src.models.entity_database import EntityDatabase


def label_errors(text: str, cases: List[Case], entity_db: EntityDatabase):
    label_demonym_errors(text, cases, entity_db)
    label_rare_entity_errors(text, cases, entity_db)
    label_partial_name_errors(text, cases, entity_db)
    label_nonentity_coreference_errors(text, cases)


def label_demonym_errors(text: str, cases: List[Case], entity_db: EntityDatabase):
    for case in cases:
        if not case.is_correct() and case.true_entity is not None:
            mention = text[case.span[0]:case.span[1]]
            if entity_db.is_demonym(mention):
                case.add_error_label(ErrorLabel.DEMONYM)


def label_rare_entity_errors(text: str, cases: List[Case], entity_db: EntityDatabase):
    for case in cases:
        if not case.is_correct() and case.true_entity is not None and case.predicted_entity is not None\
                and not case.is_true_coreference():
            mention = text[case.span[0]:case.span[1]]
            if not entity_db.is_demonym(mention):
                if entity_db.get_sitelink_count(case.true_entity.entity_id) \
                        < entity_db.get_sitelink_count(case.predicted_entity.entity_id):
                    case.add_error_label(ErrorLabel.RARE)


def label_partial_name_errors(text: str, cases: List[Case], entity_db: EntityDatabase):
    for case in cases:
        if not case.is_correct() and case.true_entity is not None and not case.is_true_coreference():
            mention = text[case.span[0]:case.span[1]]
            if not entity_db.is_demonym(mention):
                name = case.true_entity.name
                if len(mention) < len(name) and mention in name.split():
                    case.add_error_label(ErrorLabel.PARTIAL_NAME)


NONENTITY_PRONOUNS = {"it", "this", "that"}


def label_nonentity_coreference_errors(text: str, cases: List[Case]):
    for case in cases:
        if case.is_false_positive():
            snippet = text[case.span[0]:case.span[1]]
            if snippet[0].lower() + snippet[1:] in NONENTITY_PRONOUNS:
                case.add_error_label(ErrorLabel.NON_ENTITY_COREFERENCE)
