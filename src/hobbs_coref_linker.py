from typing import Optional, Tuple, Set
from spacy.language import Language

import re
from benepar.spacy_plugin import BeneparComponent
from nltk import Tree

from src.entity_coref_linker import EntityCorefLinker
from src.entity_database import EntityDatabase
from src.offset_converter import OffsetConverter
from src.hobbs_coref_algorithm import HobbsCorefAlgorithm


def get_constituency_trees(span, doc):
    parse_trees = []
    sents = OffsetConverter.get_containing_sents(span[0], doc, 4)
    for s in sents:
        string_before = s._.parse_string.replace("\n", "<br>")
        # This is necessary, since otherwise nltk throws an error about non-matching brackets
        string = re.sub(r"(\([\S]+ )[^\s()]*\(([\S]+\))", r"\1 -LRB-\2", string_before)
        parse_trees.append(string)
    trees = [Tree.fromstring(s) for s in parse_trees]
    return trees


def get_tree_pos(pos, trees):
    return trees[-1].leaf_treeposition(pos)


class HobbsCorefLinker(EntityCorefLinker):
    MAX_NUM_SENTS = 4

    def __init__(self, entity_db: EntityDatabase, model: Optional[Language] = None):
        super().__init__(entity_db, model)
        self.model.add_pipe(BeneparComponent("benepar_en2"))

    def get_referenced_entity(self, span, preceding_entities, tok_text, doc=None, max_distance=None, type_reference=False):
        trees = get_constituency_trees(span, doc)
        idx_in_sent = OffsetConverter.get_token_idx_in_sent(span[0], doc)
        pos = get_tree_pos(idx_in_sent, trees)
        hobbs_resolver = HobbsCorefAlgorithm()
        referenced_entity = hobbs_resolver.hobbs(trees, pos[:-1], tok_text.lower(), preceding_entities,
                                                 self.sent_start_idxs, type_reference=type_reference)
        return referenced_entity

    @staticmethod
    def get_preceding_entities(recent_ents_per_sent, gender, typ):
        preceding_entities = dict()
        if gender:
            for d in recent_ents_per_sent:
                preceding_entities.update(d)
        elif typ:
            for d in recent_ents_per_sent:
                for idx_span, recent_ent in d.items():
                    if typ in recent_ent.types:
                        preceding_entities[idx_span] = recent_ent
        return preceding_entities
