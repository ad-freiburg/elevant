from typing import List

from src.evaluation.case import Case, ErrorLabel
from src.models.entity_database import EntityDatabase


def label_rare_entity_errors(cases: List[Case], entity_db: EntityDatabase):
    for case in cases:
        if not case.is_correct() and case.true_entity is not None and case.predicted_entity is not None:
            if entity_db.get_sitelink_count(case.true_entity.entity_id) \
                    < entity_db.get_sitelink_count(case.predicted_entity.entity_id):
                case.add_error_label(ErrorLabel.RARE)
