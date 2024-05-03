from typing import List, Dict, Tuple, Optional

import json
import numpy as np

from elevant.evaluation.groundtruth_label import GroundtruthLabel, groundtruth_label_from_dict
from elevant.models.entity_mention import EntityMention, entity_mention_from_dict
from elevant.models.entity_prediction import EntityPrediction

ABSTRACT_INDICATOR = "ABSTRACT"


class Article:
    def __init__(self,
                 id: int,
                 title: str,
                 text: str,
                 hyperlinks: Optional[List[Tuple[Tuple[int, int], str]]] = None,
                 title_synonyms: Optional[List[Tuple[int, int]]] = None,
                 url: Optional[str] = None,
                 entity_mentions: Optional[List[EntityMention]] = None,
                 evaluation_span: Optional[Tuple[int, int]] = None,
                 labels: Optional[List[GroundtruthLabel]] = None,
                 sections: Optional[List[Tuple[Tuple[int, int], str]]] = None):
        self.id = id
        self.title = title
        self.text = text
        self.hyperlinks = hyperlinks if hyperlinks else []
        self.title_synonyms = title_synonyms if title_synonyms else []
        self.url = url
        self.entity_mentions = {}
        self.entity_coverage = None
        self.span_to_span_id = dict()
        self.spans = []
        self.add_entity_mentions(entity_mentions)
        self.evaluation_span = evaluation_span if evaluation_span is not None else (0, len(self.text))
        self.labels = labels if labels else []
        self.sections = sections

    def to_dict(self, evaluation_format: Optional[bool] = True) -> Dict:
        data = {"id": self.id,
                "title": self.title,
                "text": self.text}
        if self.hyperlinks:
            data["hyperlinks"] = self.hyperlinks
        if self.title_synonyms:
            data["title_synonyms"] = self.title_synonyms
        if self.url is not None:
            data["url"] = self.url
        if self.entity_mentions:
            data["entity_mentions"] = [self.entity_mentions[span].to_dict(evaluation_format)
                                       for span in sorted(self.entity_mentions)]
        if evaluation_format and self.evaluation_span is not None:
            data["evaluation_span"] = self.evaluation_span
        if evaluation_format and self.labels is not None:
            data["labels"] = [label.to_dict() for label in sorted(self.labels)]
        if self.sections:
            data["sections"] = self.sections
        return data

    def to_json(self, evaluation_format: Optional[bool] = True) -> str:
        return json.dumps(self.to_dict(evaluation_format))

    def add_entity_mentions(self, entity_mentions: Optional[List[EntityMention]]):
        if entity_mentions is not None:
            for entity_mention in entity_mentions:
                self.entity_mentions[entity_mention.span] = entity_mention

                # Int ids are not zero based such that 0 indicates no entity in entity_coverage
                new_span_id = len(self.span_to_span_id) + 1
                self.span_to_span_id[entity_mention.span] = new_span_id
                self.spans.append(entity_mention.span)

        self._update_entity_coverage()

    def _update_entity_coverage(self):
        self.entity_coverage = np.zeros(len(self.text), dtype=int)
        if self.entity_mentions is not None:
            for span in self.entity_mentions:
                begin, end = span
                self.entity_coverage[begin:end] = self.span_to_span_id[span]

    def get_overlapping_entity(self, span: Tuple[int, int]) -> EntityMention:
        begin, end = span
        for val in self.entity_coverage[begin:end]:
            if val != 0:
                return self.entity_mentions[self.get_span_by_id(val)]

    def link_entities(self,
                      predictions: Dict[Tuple[int, int], EntityPrediction],
                      recognized_by: str,
                      linked_by: str):
        new_entity_mentions = []
        for span in predictions:
            if not self.get_overlapping_entity(span):
                prediction = predictions[span]
                entity_mention = EntityMention(span,
                                               recognized_by=recognized_by,
                                               entity_id=prediction.entity_id,
                                               linked_by=linked_by,
                                               candidates=prediction.candidates)
                new_entity_mentions.append(entity_mention)
        self.add_entity_mentions(new_entity_mentions)

    def is_entity_mention(self, span: Tuple[int, int]) -> bool:
        return self.entity_mentions is not None and span in self.entity_mentions

    def get_entity_mention(self, span: Tuple[int, int]) -> EntityMention:
        return self.entity_mentions[span]

    def set_evaluation_span(self, start: int, end: int):
        self.evaluation_span = (start, end)

    def get_span_by_id(self, span_id: int) -> Tuple[int, int]:
        if span_id - 1 < len(self.spans):
            return self.spans[span_id - 1]

    def get_abstract_span(self) -> Tuple[int, int]:
        """
        Get the abstract of an Wikipedia article with sections.
        Throws an error if no sections are provided in the file from which the article was created.
        """
        if self.sections is None:
            raise AttributeError("Tried to get abstract span but the article does not contain any section data.")
        first_section_span = self.sections[0][0]
        first_section_text = self.text[first_section_span[0]:first_section_span[1]]
        title_end = first_section_text.find("\n\n") + len("\n\n")
        abstract_start = title_end
        abstract_text = self.text[abstract_start:first_section_span[1]]
        first_newline_ind = abstract_text.find("\n")
        if 0 < first_newline_ind < 60 and "°" in abstract_text[:first_newline_ind] and \
                len(abstract_text) > first_newline_ind + 2:
            # Filter out leading coordinates from abstract
            abstract_start = title_end + first_newline_ind + 1
        return abstract_start, first_section_span[1]

    def __str__(self) -> str:
        return str(self.to_dict())

    def __repr__(self) -> str:
        return str(self)


def article_from_dict(data: Dict) -> Article:
    # spans are saved as lists, but must be tuples
    hyperlinks = [(tuple(span), target) for span, target in data["hyperlinks"]] if "hyperlinks" in data else None
    title_synonyms = [tuple(span) for span in data["title_synonyms"]] if "title_synonyms" in data else None
    sections = [(tuple(span), title) for span, title in data["sections"]] if "sections" in data else None
    labels = None
    if "labels" in data and len(data["labels"]) > 0:
        labels = [groundtruth_label_from_dict(groundtruth_label_dict) for groundtruth_label_dict in data["labels"]]
    return Article(id=int(data["id"]),
                   title=data["title"],
                   text=data["text"],
                   hyperlinks=hyperlinks,
                   title_synonyms=title_synonyms,
                   url=data["url"] if "url" in data else None,
                   entity_mentions=[entity_mention_from_dict(entity_mention_dict) for entity_mention_dict in
                                    data["entity_mentions"]] if "entity_mentions" in data else None,
                   evaluation_span=data["evaluation_span"] if "evaluation_span" in data else None,
                   labels=labels,
                   sections=sections)


def article_from_json(dump: str) -> Article:
    return article_from_dict(json.loads(dump))
