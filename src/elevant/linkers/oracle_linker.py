from elevant.evaluation.groundtruth_label import GroundtruthLabel
from elevant.models.entity_prediction import EntityPrediction
from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper, UnknownEntity


def link_entities_with_oracle(article):
    """
    Link the article with oracle predictions, i.e. with ground truth labels.
    This can be used e.g., in order to examine benchmark ground truth labels.
    """

    def get_label(gt_label: GroundtruthLabel):
        entity_id = gt_label.entity_id
        if KnowledgeBaseMapper.is_unknown_entity(entity_id):
            entity_id = UnknownEntity.NIL.value
        return EntityPrediction(gt_label.span, entity_id, {entity_id})

    predicted_entities = dict()
    label_dict = {gt_label.id: gt_label for gt_label in article.labels}
    for gt_label in article.labels:
        # Only include non-optional (no optionals, descriptives, quantities or datetimes)
        # root gt labels in the predictions
        # or non-optional child gt labels with optional parents.
        if gt_label.parent is None:
            if not gt_label.is_optional():
                predicted_entities[gt_label.span] = get_label(gt_label)
            elif gt_label.has_non_optional_child(label_dict):
                # Due to this part, it is now not enough anymore to count the number of oracle
                # predictions on our benchmarks to find out the number of parent labels.
                child_ids = gt_label.children[:]
                while len(child_ids) > 0:
                    child_id = child_ids.pop()
                    child_label = label_dict[child_id]
                    if not child_label.is_optional():
                        predicted_entities[child_label.span] = get_label(child_label)
                    elif child_label.has_non_optional_child(label_dict):
                        child_ids.extend(child_label.children)

    article.link_entities(predicted_entities, "ORACLE", "ORACLE")
