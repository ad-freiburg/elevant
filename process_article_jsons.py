import sys
import json

from src.wikipedia_article import WikipediaArticle, Paragraph


if __name__ == "__main__":
    path = sys.argv[1]
    out_path = path + "_processed"
    with open(out_path, "w", encoding="utf8") as out_file:
        for i, line in enumerate(open(path)):
            data = json.loads(line[:-1])
            paragraphs = [Paragraph(text, links) for text, links in zip(data["paragraphs"], data["links"])]
            article = WikipediaArticle(data["id"], data["title"], paragraphs=paragraphs)
            article_data = article.to_dict()
            article_dump = json.dumps(article_data)
            out_file.write(article_dump + '\n')
            print("\r%i lines" % (i + 1), end='')
        print()
