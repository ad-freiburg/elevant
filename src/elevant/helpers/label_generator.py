from typing import Iterator, Tuple, Dict, Optional
import spacy
from spacy.training import Example
from spacy.kb import KnowledgeBase
from spacy.language import Doc
from spacy.pipeline import Sentencizer

from elevant import settings
from elevant.helpers.wikipedia_corpus import WikipediaCorpus


class LabelGenerator:
    DISABLE_TRAINING = ["entity_linker", "tagger"]

    def __init__(self, kb: KnowledgeBase, mapping: Dict[str, str]):
        """
        Provide data for the generation of entity linker training examples.

        :param model: The language pipeline to be used to generate spacy documents. Used for entity recognition.
        :param kb: The knowledge base to link to. Candidate and ground truth entities come from the knowledge base.
        :param mapping: Mapping between link targets and entity IDs.
        """
        self.model = spacy.load(settings.LARGE_MODEL_NAME)
        self.model.add_pipe("sentencizer")
        self.kb = kb
        self.mapping = mapping
        self.sentencizer = Sentencizer()

    def read_examples(self,
                      n: int = -1,
                      test: Optional[bool] = False) -> Iterator[Tuple[Doc, Dict[str, Dict[Tuple[int, int], str]]]]:
        """
        Generate training examples for the entity linker.

        The ground truth labels are generated from the page references in the article.
        The labels include all page references for which the reference target can be mapped to an entity ID that is
        contained in the knowledge base and where the reference span is detected as an entity by the NER.
        Articles without ground truth labels are skipped.

        The yielded training examples have the format
          (document, labels)
        with document being a spacy Doc and labels a dictionary of the format
          {"links": [(span1, entity_id1), (span2, entity_id2), ...]}

        :param n: number of training examples
        :param test: articles are read from the development instead of the training set
        :return: iterator over training examples
        """
        # disable_training = [pipe for pipe in LabelGenerator.DISABLE_TRAINING if pipe in self.model.pipeline]
        iterator = WikipediaCorpus.training_articles(n) if not test else WikipediaCorpus.development_articles(n)
        for article in iterator:
            link_dict = {}
            for span, link_target in article.hyperlinks:
                # check if target can be mapped to ID:
                if link_target in self.mapping:
                    entity_id = self.mapping[link_target]
                    # check if the ID is in the knowledge base:
                    if self.kb.contains_entity(entity_id):
                        begin, end = span
                        snippet = article.text[begin:end]
                        candidate_entities = [candidate.entity_ for candidate in self.kb.get_alias_candidates(snippet)]
                        # check if the ground truth entity is in the candidates:
                        if entity_id in candidate_entities:
                            # generate ground truth labels for all candidates:
                            link_dict[span] = {candidate_id: 1.0 if candidate_id == entity_id else 0.0
                                               for candidate_id in candidate_entities}
            # skip if no link could be mapped:
            if len(link_dict) > 0:
                doc = self.model(article.text)
                ner_dict = {(ent.start_char, ent.end_char): ent.label for ent in doc.ents}
                # filter entities not recognized by the NER:
                doc_entity_spans = {(e.start_char, e.end_char) for e in doc.ents}
                link_dict = {span: link_dict[span] for span in link_dict if span in doc_entity_spans}
                entities = [(span[0], span[1], ner_dict.get(span, "UNK")) for span in link_dict]
                # skip if no entities remain after filtering:
                if len(link_dict) > 0:
                    annotation = {"links": link_dict, "entities": entities}
                    example = Example.from_dict(self.model.make_doc(article.text), annotation)
                    example.reference = self.sentencizer(example.reference)
                    yield example
