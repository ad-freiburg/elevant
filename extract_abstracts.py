from src.wikipedia_dump_reader import WikipediaDumpReader


if __name__ == "__main__":
    for article in WikipediaDumpReader.article_iterator():
        print(article.id)
        print(article.title)
        print(article.url)
        paragraphs = article.text.split("\n\n")
        if len(paragraphs) > 1:
            abstract = paragraphs[1]
            if len(abstract) < 100 and "°" in abstract and len(paragraphs) > 2:
                abstract = paragraphs[2]
        else:
            abstract = article.text
        abstract = abstract.replace("\n", " ")
        print(abstract)
        print("\n" * 2)