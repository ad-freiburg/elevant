"""
Code taken from https://github.com/cmward/hobbs
Implementation of Hobbs' algorithm for pronoun resolution.
Chris Ward, 2014
Modifcations by Natalie Prange, these include
* use entity information to decide about gender match
* fix step 8 to not include the current path
* allow coreference resolution for possessive pronouns as well
* allow coreference resolution for "the <type>" coreferences
* fix linter errors
"""

import nltk
import queue
import logging

from src.models.gender import Gender
from src.utils.pronoun_finder import PronounFinder

logger = logging.getLogger("main." + __name__.split(".")[-1])

# Labels for nominal heads
nominal_labels = ["NN", "NNS", "NNP", "NNPS", "PRP"]


def get_pos(tree, node):
    """ Given a tree and a node, return the tree position
    of the node.
    """
    for pos in tree.treepositions():
        if tree[pos] == node:
            return pos


def get_dom_np(sents, pos):
    """ Finds the position of the NP that immediately dominates
    the pronoun.
    Args:
        sents: list of trees (or tree) to search
        pos: the tree position of the pronoun to be resolved
    Returns:
        tree: the tree containing the pronoun
        dom_pos: the position of the NP immediately dominating
            the pronoun
    """
    # start with the last tree in sents
    tree = sents[-1]
    # get the NP's position by removing the last element from
    # the pronoun's
    dom_pos = pos[:-1]
    return tree, dom_pos


def walk_to_np_or_s(tree, pos):
    """ Takes the tree being searched and the position from which
    the walk up is started. Returns the position of the first NP
    or S encountered and the path taken to get there from the
    dominating NP. The path consists of a list of tree positions.
    Args:
        tree: the tree being searched
        pos: the position from which the walk is started
    Returns:
        path: the path taken to get the an NP or S node
        pos: the position of the first NP or S node encountered
    """
    path = [pos]
    still_looking = True
    while still_looking:
        # climb one level up the tree by removing the last element
        # from the current tree position
        pos = pos[:-1]
        path.append(pos)
        # if an NP or S node is encountered, return the path and pos
        if "NP" in tree[pos].label() or tree[pos].label() == "S" or len(pos) == 0:
            still_looking = False
    return path, pos


def bft(tree):
    """ Perform a breadth-first traversal of a tree.
    Return the nodes in a list in level-order.
    Args:
        tree: a tree node
    Returns:
        lst: a list of tree nodes in left-to-right level-order
    """
    lst = []
    new_queue = queue.Queue()
    new_queue.put(tree)
    while not new_queue.empty():
        node = new_queue.get()
        lst.append(node)
        for child in node:
            if isinstance(child, nltk.Tree):
                new_queue.put(child)
    return lst


def count_np_nodes(tree):
    """ Function from class to count NP nodes.
    """
    if not isinstance(tree, nltk.Tree):
        return 0
    elif "NP" in tree.label() and tree.label() not in nominal_labels:
        return 1 + sum(count_np_nodes(c) for c in tree)
    else:
        return sum(count_np_nodes(c) for c in tree)


def check_for_intervening_np(tree, pos, proposal, pro):
    """ Check if subtree rooted at pos contains at least
    three NPs, one of which is:
        (i)   not the proposal,
        (ii)  not the pronoun, and
        (iii) greater than the proposal
    Args:
        tree: the tree being searched
        pos: the position of the root subtree being searched
        proposal: the position of the proposed NP antecedent
        pro: the pronoun being resolved (string)
    Returns:
        True if there is an NP between the proposal and the  pronoun
        False otherwise
    """
    bf = bft(tree[pos])
    bf_pos = [get_pos(tree, node) for node in bf]

    if count_np_nodes(tree[pos]) >= 3:
        for node_pos in bf_pos:
            if "NP" in tree[node_pos].label() \
                    and tree[node_pos].label() not in nominal_labels:
                if node_pos != proposal and node_pos != get_pos(tree, pro):
                    if node_pos < proposal:
                        return True
    return False


class HobbsCorefAlgorithm:
    def __init__(self):
        self.preceding_entities = None
        self.preceding_entities_by_type = None
        self.sent_start_idx_offsets = None
        self.sentence_id = None
        self.type_reference = False
        self.debug = False

    def print_debug(self, string):
        if self.debug:
            logger.debug(string)

    def linked_entity_from_proposal(self, proposal):
        if not proposal:
            return None

        tree, pos = proposal
        sentence_idx_offset = self.sent_start_idx_offsets[self.sentence_id]
        for i, _ in enumerate(tree[pos].leaves()):
            tok_idx = self.treeposition2idx(tree, pos) + sentence_idx_offset + i
            for idx_span in sorted(self.preceding_entities):
                start_idx, end_idx = idx_span
                if start_idx <= tok_idx <= end_idx:
                    return self.preceding_entities[idx_span]

    @staticmethod
    def treeposition2idx(tree, pos):
        for idx, l in enumerate(tree.leaves()):
            tree_pos = tree.leaf_treeposition(idx)
            trimmed_tree_pos = tree_pos[:len(pos)]
            if trimmed_tree_pos == pos:
                return idx
        return -1

    def traverse_left(self, tree, pos, path, pro, check=1):
        """ Traverse all branches below pos to the left of path in a
        left-to-right, breadth-first fashion. Returns the first potential
        antecedent found.

        If check is set to 1, propose as an antecedent any NP node
        that is encountered which has an NP or S node between it and pos.
        If check is set to 0, propose any NP node encountered as the antecedent.
        Args:
            tree: the tree being searched
            pos: the position of the root of the subtree being searched
            path: the path taked to get to pos
            pro: the pronoun being resolved (string)
            check: whether or not there must be an intervening NP
        Returns:
            tree: the tree containing the antecedent
            p: the position of the proposed antecedent
        """
        # get the results of breadth first search of the subtree
        # iterate over them
        breadth_first = bft(tree[pos])

        # convert the treepositions of the subtree rooted at pos
        # to their equivalents in the whole tree
        bf_pos = [get_pos(tree, node) for node in breadth_first]

        if check == 1:
            for p in bf_pos:
                if p < path[0] and p not in path:
                    if "NP" in tree[p].label() and self.match(tree, p, pro):
                        if check_for_intervening_np(tree, pos, p, pro):
                            return tree, p

        elif check == 0:
            for p in bf_pos:
                if p < path[0] and p not in path:
                    if "NP" in tree[p].label() and self.match(tree, p, pro):
                        return tree, p

        return None, None

    def traverse_right(self, tree, pos, path, pro):
        """ Traverse all the branches of pos to the right of path p in a
        left-to-right, breadth-first manner, but do not go below any NP
        or S node encountered. Propose any NP node encountered as the
        antecedent. Returns the first potential antecedent.
        Args:
            tree: the tree being searched
            pos: the position of the root of the subtree being searched
            path: the path taken to get to pos
            pro: the pronoun being resolved (string)
        Returns:
            tree: the tree containing the antecedent
            p: the position of the antecedent
        """
        breadth_first = bft(tree[pos])
        bf_pos = [get_pos(tree, node) for node in breadth_first]

        for p in bf_pos:
            # This is an adjustment over the original version. Without the startswith() test, the returned tree
            # could include the given path
            if p > path[0] and p[:len(path[0])] != path[0] and p not in path:
                if "NP" in tree[p].label() or tree[p].label() == "S":
                    if "NP" in tree[p].label() and tree[p].label() not in nominal_labels:
                        if self.match(tree, p, pro):
                            return tree, p
                    return None, None
        return None, None

    def traverse_tree(self, tree, pro):
        """ Traverse a tree in a left-to-right, breadth-first manner,
        proposing any NP encountered as an antecedent. Returns the
        tree and the position of the first possible antecedent.
        Args:
            tree: the tree being searched
            pro: the pronoun being resolved (string)
        """
        # Initialize a queue and enqueue the root of the tree
        new_queue = queue.Queue()
        new_queue.put(tree)
        while not new_queue.empty():
            node = new_queue.get()
            # if the node is an NP, return it as a potential antecedent
            if "NP" in node.label() and self.match(tree, get_pos(tree, node), pro):
                return tree, get_pos(tree, node)
            for child in node:
                if isinstance(child, nltk.Tree):
                    new_queue.put(child)
        # if no antecedent is found, return None
        return None, None

    def match(self, tree, pos, pro):
        """ Takes a proposed antecedent and checks whether it matches
        the pronoun in number and gender

        Args:
            tree: the tree in which a potential antecedent has been found
            pos: the position of the potential antecedent
            pro: the pronoun being resolved (string)
        Returns:
            True if the antecedent and pronoun match
            False otherwise
        """
        if self.number_match(tree, pos, pro) and self.gender_match(tree, pos, pro):
            return True
        return False

    def number_match(self, tree, pos, pro):
        """ Takes a proposed antecedent and pronoun and checks whether
        they match in number.
        """
        m = {"NN": "singular",
             "NNP": "singular",
             "he": "singular",
             "she": "singular",
             "him": "singular",
             "her": "singular",
             "it": "singular",
             "himself": "singular",
             "herself": "singular",
             "itself": "singular",
             "his": "singular",
             "its": "singular",
             "NNS": "plural",
             "NNPS": "plural",
             "they": "plural",
             "them": "plural",
             "themselves": "plural",
             "their": "plural",
             "PRP": None}

        # if the label of the nominal dominated by the proposed NP and
        # the pronoun both map to the same number feature, they match
        self.print_debug("Check for number match in %s" % tree[pos])
        for c in tree[pos]:
            if isinstance(c, nltk.Tree) and c.label() in nominal_labels:
                if pro in m and m[c.label()] == m[pro] or not m[c.label()] or \
                        (self.type_reference and m[c.label()] == "singular"):
                    self.print_debug("Number match")
                    return True
        self.print_debug("No number match")
        return False

    def gender_match(self, tree, pos, pro):
        """ Takes a proposed antecedent and pronoun and checks whether
        they match in gender. Only checks for mismatches between singular
        proper name antecedents and singular pronouns.
        """
        self.print_debug("Check for gender match in %s" % tree[pos])
        preceding_entity = self.linked_entity_from_proposal((tree, pos))

        if not preceding_entity:
            # If the proposed antecedent is not a linked entity, do not reject it due to gender information
            self.print_debug("not a linked entity.")
            return False

        if self.type_reference:
            return True

        p_gender = PronounFinder.pronoun_genders[pro.lower()]
        self.print_debug("gender pronoun / entity: %s / %s" % (p_gender, preceding_entity.gender))
        # TODO: this could match I/you/we to neutral entity
        return preceding_entity.gender == p_gender or p_gender == Gender.UNKNOWN

    def hobbs(self, sents, pos, pro, preceding_entities, sent_start_idx_offsets, type_reference=False):
        """ The implementation of Hobbs' algorithm.
        Args:
            sents: list of sentences to be searched
            pos: the position of the pronoun to be resolved
            pro: the pronoun in lower csae
            preceding_entities: dictionary of idx span to entity
            sent_start_idx_offsets: list of sentence start idx offsets
            type_reference: if true, reference is a "the type" reference
        Returns:
            proposal: a tuple containing the tree and position of the
                proposed antecedent
        """
        self.preceding_entities = preceding_entities
        self.sent_start_idx_offsets = sent_start_idx_offsets
        self.type_reference = type_reference

        # The index of the most recent sentence in sents
        self.sentence_id = len(sents) - 1

        # Step 1: begin at the NP node immediately dominating the pronoun
        tree, pos = get_dom_np(sents, pos)
        self.print_debug("Step 1: immediately dominating NP: %s" % tree[pos])

        # Step 2: Go up the tree to the first NP or S node encountered
        path, pos = walk_to_np_or_s(tree, pos)
        self.print_debug("Step 2: first NP/S in path: %s" % tree[pos])

        # Step 3: Traverse all branches below pos to the left of path
        # left-to-right, breadth-first. Propose as an antecedent any NP
        # node that is encountered which has an NP or S node between it and pos
        proposal = self.traverse_left(tree, pos, path, pro)
        if proposal and proposal[0]:
            self.print_debug("Step 3: Traverse left to right: %s" % proposal[0][proposal[1]])

        while proposal == (None, None):

            # Step 4: If pos is the highest S node in the sentence,
            # traverse the surface parses of previous sentences in order
            # of recency, the most recent first; each tree is traversed in
            # a left-to-right, breadth-first manner, and when an NP node is
            # encountered, it is proposed as an antecedent
            if pos == ():
                # go to the previous sentence
                self.sentence_id -= 1
                # if there are no more sentences, no antecedent found
                if self.sentence_id < 0:
                    return None
                # search new sentence
                proposal = self.traverse_tree(sents[self.sentence_id], pro)
                if proposal != (None, None):
                    self.print_debug("Step 4: %s" % proposal[0][proposal[1]])
                    return self.linked_entity_from_proposal(proposal)

            # Step 5: If pos is not the highest S in the sentence, from pos,
            # go up the tree to the first NP or S node encountered.
            path, pos = walk_to_np_or_s(tree, pos)
            self.print_debug("Step 5: %s" % tree[pos])

            # Step 6: If pos is an NP node and if the path to pos did not pass
            # through the nominal node that pos immediately dominates, propose pos
            # as the antecedent.
            if "NP" in tree[pos].label() and tree[pos].label() not in nominal_labels:
                for c in tree[pos]:
                    if isinstance(c, nltk.Tree) and c.label() in nominal_labels:
                        if get_pos(tree, c) not in path and self.match(tree, pos, pro):
                            proposal = (tree, pos)
                            if proposal != (None, None):
                                self.print_debug("Step 6: %s" % proposal[0][proposal[1]])
                                return self.linked_entity_from_proposal(proposal)

            # Step 7: Traverse all branches below pos to the left of path,
            # in a left-to-right, breadth-first manner. Propose any NP node
            # encountered as the antecedent.
            proposal = self.traverse_left(tree, pos, path, pro, check=0)
            if proposal != (None, None):
                self.print_debug("Step 7: %s" % proposal[0][proposal[1]])
                return self.linked_entity_from_proposal(proposal)

            # Step 8: If pos is an S node, traverse all the branches of pos
            # to the right of path in a left-to-right, breadth-forst manner, but
            # do not go below any NP or S node encountered. Propose any NP node
            # encountered as the antecedent.
            if tree[pos].label() == "S":
                proposal = self.traverse_right(tree, pos, path, pro)
                if proposal != (None, None):
                    self.print_debug("Step 8: %s" % proposal[0][proposal[1]])
                    return self.linked_entity_from_proposal(proposal)

        return self.linked_entity_from_proposal(proposal)
