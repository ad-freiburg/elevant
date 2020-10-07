import sys

from src import settings
from src.models.conll_benchmark import conll_documents, ConllDocument
from src.models.wikipedia_article import WikipediaArticle, article_from_json, EntityMention


def set_tags(document: ConllDocument, article: WikipediaArticle):
    document_pos = 0
    em_i = 0
    entity_mentions = [article.entity_mentions[span] for span in sorted(article.entity_mentions)]
    for token in document.tokens:
        t_start = document_pos
        t_end = t_start + len(token.text)
        # print(em_i, len(entity_mentions))
        entity_mention = entity_mentions[em_i] if em_i < len(entity_mentions) else None
        label = "O"
        if entity_mention is not None:
            entity_mention: EntityMention
            em_start, em_end = entity_mention.span
            if t_start == em_start:
                label = entity_mention.entity_id if entity_mention.entity_id is not None else "B"
            elif em_start <= t_end:
                label = "I"
            if t_end >= em_end:
                em_i += 1
        token.set_predicted_label(label)
        document_pos = t_end + 1


if __name__ == "__main__":
    file_name = sys.argv[1]

    with open(settings.DATA_DIRECTORY + file_name) as f:
        for line, document in zip(f, conll_documents()):
            article = article_from_json(line)
            set_tags(document, article)
            print("\t".join([document.id,
                             document.get_truth(),
                             document.get_predicted()]))
