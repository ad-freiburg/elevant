from src.wikipedia_dump_reader import WikipediaDumpReader


if __name__ == "__main__":
    for article in WikipediaDumpReader.article_iterator():
        print(article.id)
        print(article.title)
        print(article.url)
        abstract = " ".join(article.text.split("\n\n")[:2]).replace("\n", " ")
        print(abstract)
        print("\n" * 2)