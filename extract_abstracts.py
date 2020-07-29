from src.wikipedia_dump_reader import WikipediaDumpReader


if __name__ == "__main__":
    for article in WikipediaDumpReader.article_iterator():
        paragraphs = article.text.split("\n\n")
        abstract = ""
        if len(paragraphs) > 1:
            abstract = paragraphs[1]
            if len(abstract) < 100 and "°" in abstract and len(paragraphs) > 2:
                abstract = paragraphs[2]
        if len(abstract) == 0:
            abstract = article.text[:500]
        abstract = abstract.replace("\n", " ")
        print("\t".join((
            article.id,
            article.title,
            article.url,
            abstract
        )))
