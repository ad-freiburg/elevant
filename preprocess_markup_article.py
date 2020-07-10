from src.wikipedia_article import WikipediaArticle
from src.markup_processor import MarkupProcessor
from src.wikipedia_dump_reader import WikipediaDumpReader

if __name__ == "__main__":
    path = "/home/hertel/wikipedia/wikipedia_2020-06-08/libya_markup.txt"
    with open(path) as f:
        page = f.read()
    article = WikipediaDumpReader.parse_article(page)
    MarkupProcessor.link_entities(article)

    for paragraph, links in zip(article.paragraphs, article.wikipedia_links):
        print(paragraph)
        print(links)

    # TODO: make article with paragraphs
