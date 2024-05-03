from typing import List

from elevant.evaluation.groundtruth_label import GroundtruthLabel


class NestedGroundtruthHandler:
    @staticmethod
    def get_child_indices(curr_label_idx: int, gt_labels: List[GroundtruthLabel]) -> List[int]:
        """
        For the groundtruth label at the given index in the label list get list
        indices of its children.
        """
        child_indices = []
        curr_span = gt_labels[curr_label_idx].span
        for i, gt_label in enumerate(gt_labels):
            if gt_label.span[0] >= curr_span[0] and gt_label.span[1] <= curr_span[1] and curr_label_idx != i:
                child_indices.append(i)
        return child_indices

    @staticmethod
    def assign_parent_and_child_ids(labels: List[GroundtruthLabel]):
        """
        Assign parent and child ids to GT labels in case of nested GT labels.
        """
        for i, gt_label in enumerate(labels):
            child_indices = NestedGroundtruthHandler.get_child_indices(i, labels)
            for child_idx in child_indices:
                child_gt_label = labels[child_idx]
                child_gt_label.parent = gt_label.id
                gt_label.children.append(child_gt_label.id)
