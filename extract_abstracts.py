from src import settings
from src.helpers.wikipedia_dump_reader import WikipediaDumpReader


if __name__ == "__main__":
    with open(settings.WIKIPEDIA_ABSTRACTS_FILE, "w", encoding="utf8") as output_file:
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
            output_file.write("\t".join((
                article.id,
                article.title,
                article.url,
                abstract
            )) + "\n")
