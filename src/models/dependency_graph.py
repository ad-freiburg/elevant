from nltk.parse.dependencygraph import DependencyGraph


class EnhancedDependencyGraph(DependencyGraph):
    def get_by_address(self, address):
        """Returns the node with the given address.

        But without creating a new node if it doesn't exist.

        Args:
            address (int): address of the node to be retrieved

        Returns:
            dict: the node
        """
        if address in self.nodes:
            return self.nodes[address]

    def remove_by_address(self, address):
        """Removes the node with the given address if it exists.

        Args:
            address (int): address of the node to be removed

        Returns:
            dict: the node
        """
        if address in self.nodes:
            del self.nodes[address]

    def get_by_rel(self, rels):
        """Returns all nodes in the graph which have the given relations.

        Args:
            rels (list): list of rels for which to search

        Returns:
            list: list of nodes
        """
        nodes = []
        for i, n in sorted(self.nodes.items()):
            if n['rel'] in rels:
                nodes.append(n)
        return nodes

    def get_root(self):
        """Returns the root node of the graph if it exists.

        Returns:
            dict: the root node
        """
        root_list = self.get_by_rel(['root'])
        if len(root_list) == 1:
            return root_list[0]

    def get_predicate_list(self, predicate):
        """Returns the predicate, its advmod, negation and particle ("hand over",
        "shut down") if it has one.

        Args:
            predicate (dict): the predicate node of the sentence

        Returns:
            list: list of certain predicate dependent nodes
        """
        lst = [predicate]
        for k, v in predicate['deps'].items():
            if k in ['advmod', 'neg', 'prt']:
                for el in v:
                    node = self.get_by_address(el)
                    if node and node['address'] is not None:
                        lst.append(node)
        return sorted(lst, key=lambda x: x['address'])

    def get_subtree(self, node, exclude=None):
        """Returns all child-nodes of a given node in the graph as a list.

        Args:
            node (dict): the parent node of the subtree that has to be extracted
            exclude (list): list of addresses of nodes to exclude from the subtree

        Returns:
            list: list of child nodes
        """
        if exclude is None:
            exclude = []
        lst = []
        for k, v in node['deps'].items():
            for el in v:
                if el in exclude:
                    continue
                dep_node = self.get_by_address(el)
                if not dep_node:
                    continue
                lst += self.get_subtree(dep_node)
                lst.append(dep_node)
        return lst

    def to_sentence(self, mask_entities=False):
        """Forms a sentence from the graph.

        Args:
            mask_entities (bool): if True, entities are masked in the sentence

        Returns:
            str: sentence represented by the graph
        """
        word_list = []
        for _, n in sorted(self.nodes.items()):
            if n['word'] is not None:
                if n['entity'] is not None:
                    if mask_entities:
                        word_list.append("[x]")
                    else:
                        e = n['entity']
                        word_list.append(e.to_entity_format())
                else:
                    word_list.append(n['word'])
        return ' '.join(word_list)

    def in_main_dependencies(self, node, dependent_node):
        """Checks if a given node is within the main-dependencies of another
        node.

        Args:
            node (dict): main node
            dependent_node (dict): dependent node

        Returns:
            bool: True iff dependent node is in the main-dependencies of node
        """
        if node == dependent_node:
            return True

        address = dependent_node['address']
        for k, v in node['deps'].items():
            if k in ['prep', 'pobj', 'dobj', 'nsubj', 'nsubjpass', 'iobj', 'poss', 'nummod']:
                if address in v:
                    return True
                for adr in v:
                    new_node = self.get_by_address(adr)
                    if new_node:
                        found = self.in_main_dependencies(new_node, dependent_node)
                        if found:
                            return True
        return False

    def has_word(self, word):
        """Returns True if the graph contains the specified word.

        Args:
            word (str): the word for which to check

        Returns:
            bool: True iff the graph contains word
        """
        for n in self.nodes.values():
            if n['word'] == word:
                return True
        return False

    def has_subj(self):
        """Returns true if the graph contains a subject.

        Returns:
            bool: True iff the graph contains a subject
        """
        for n in self.nodes.values():
            if n['rel'] in ['nsubj', 'nsubjpass']:
                return True
        return False

    def rm_deps_recursively(self, node):
        """Removes all dependencies of a given node in the graph.

        Args:
            node (dict): the node
        """
        if node is None:
            return
        for k, v in node['deps'].items():
            for el in v:
                self.rm_deps_recursively(self.get_by_address(el))
                self.remove_by_address(el)

    def is_problematic_it(self, address):
        node = self.get_by_address(address)
        if node and node["word"].lower() == "it" and node["rel"].startswith("nsubj"):
            head = self.get_by_address(node["head"])
            if head["tag"] and head["tag"].startswith("VB"):
                head_deps = head['deps']
                if "ccomp" in head_deps:
                    return True
                # The following two if-branches detect anticipatory it
                if 'acomp' in head_deps and ('xcomp' in head_deps or 'ccomp' in head_deps):
                    return True
                if 'acomp' in head_deps:
                    for acomp_address in head_deps['acomp']:
                        acomp = self.get_by_address(acomp_address)
                        if 'xcomp' in acomp['deps'] or 'ccomp' in acomp['deps']:
                            return True
        return False
