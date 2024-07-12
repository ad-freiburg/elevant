import os
import logging

from typing import Iterator, List, Optional

from pynif import NIFCollection
from urllib.parse import quote, unquote

from elevant.evaluation.groundtruth_label import GroundtruthLabel
from elevant.models.entity_mention import EntityMention
from elevant.models.article import Article
from elevant.utils.knowledge_base_mapper import KnowledgeBaseMapper

logger = logging.getLogger("main." + __name__.split(".")[-1])


class NIFParser:
    @staticmethod
    def has_children(curr_label_idx: int, gt_labels: List[GroundtruthLabel]):
        child_indices = []
        curr_span = gt_labels[curr_label_idx].span
        for i, gt_label in enumerate(gt_labels):
            if gt_label.span[0] >= curr_span[0] and gt_label.span[1] <= curr_span[1] and curr_label_idx != i:
                child_indices.append(i)
        return child_indices

    def get_articles_from_nif_content(self, nif_content: str, groundtruth: bool) -> Iterator[Article]:
        """
        Create a WikipediaArticle from the given file in NIF format.
        """
        nif_doc = NIFCollection.loads(nif_content)
        article_id_counter = 0
        for context in nif_doc.contexts:
            label_id_counter = 0
            text = context.mention
            title = unquote(context.uri[context.uri.find("/"):])
            entity_mentions = []
            labels = []
            for phrase in context.phrases:
                entity_uri = phrase.taIdentRef
                entity_id = entity_uri[entity_uri.rfind("/") + 1:]
                span = phrase.beginIndex, phrase.endIndex
                if groundtruth:
                    labels.append(GroundtruthLabel(label_id_counter, span, entity_id, "Unknown"))
                    label_id_counter += 1
                else:
                    entity_mentions.append(EntityMention(span, "NIF_READER", entity_id))

            # Assign parent and child ids to groundtruth labels
            for i, gt_label in enumerate(labels):
                child_indices = self.has_children(i, labels)
                for child_idx in child_indices:
                    child_gt_label = labels[child_idx]
                    child_gt_label.parent = gt_label.id
                    gt_label.children.append(child_gt_label.id)

            article = Article(id=article_id_counter, title=title, text=text, hyperlinks=[], labels=labels,
                              entity_mentions=entity_mentions)
            article_id_counter += 1
            yield article

    def get_articles_from_file(self, filename: str, groundtruth: bool) -> Iterator[Article]:
        with open(filename, "r", encoding="utf8") as file:
            file_content = file.readlines()
            file_content = "".join(file_content)
            for article in self.get_articles_from_nif_content(file_content, groundtruth):
                yield article

    def article_iterator(self, nif_path: str, groundtruth: Optional[bool] = False) -> Iterator[Article]:
        """
        Yields for each NIF context a WikipediaArticle.
        """
        if os.path.isdir(nif_path):
            for filename in sorted(os.listdir(nif_path)):
                for article in self.get_articles_from_file(filename, groundtruth):
                    yield article
        else:
            for article in self.get_articles_from_file(nif_path, groundtruth):
                yield article

    @staticmethod
    def get_nif_from_articles(articles: List[Article],
                              collection_uri: Optional[str] = "http://example.org/",
                              groundtruth: Optional[bool] = False) -> str:
        wikidata_prefix = 'http://www.wikidata.org/entity/'
        collection = NIFCollection(uri=collection_uri)
        for article in articles:
            uri = collection_uri + quote(article.title)
            context = collection.add_context(uri=uri, mention=article.text)
            if groundtruth:
                for gt_label in article.labels:
                    entity_uri = wikidata_prefix + gt_label.entity_id \
                        if gt_label.entity_id and not KnowledgeBaseMapper.is_unknown_entity(gt_label.entity_id) else None
                    annotator = "groundtruth"
                    types = [wikidata_prefix + typ for typ in gt_label.get_types()]
                    context.add_phrase(
                        beginIndex=gt_label.span[0],
                        endIndex=gt_label.span[1],
                        taClassRef=types,
                        annotator=annotator,
                        taIdentRef=entity_uri)
            elif article.entity_mentions:
                for span, em in sorted(article.entity_mentions.items()):
                    entity_uri = wikidata_prefix + em.entity_id \
                        if em.entity_id and not KnowledgeBaseMapper.is_unknown_entity(em.entity_id) else None
                    annotator = em.linked_by
                    context.add_phrase(
                        beginIndex=span[0],
                        endIndex=span[1],
                        annotator=annotator,
                        taIdentRef=entity_uri)

        generated_nif = collection.dumps(format='turtle')
        return generated_nif
