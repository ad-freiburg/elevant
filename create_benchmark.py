from typing import List, Tuple

from src.models.wikipedia_article import article_from_json


START_TAG = "<START>"
END_TAG = "<END>"
N_ARTICLES = 23
ARTICLES_SPLIT = 10
SKIP_ARTICLES = {2, 10, 14}


def read_labeled_texts(path: str, n: int) -> List[str]:
    texts = []
    lines = []
    for line in open(path):
        if line.startswith("**** ARTICLE"):
            if len(lines) > 0:
                texts.append("".join(lines))
                lines = []
                if len(texts) == n:
                    return texts
        else:
            line = line.replace(START_TAG, "")
            line = line.replace(END_TAG, "")
            lines.append(line)


def get_labels(labeled_text: str) -> List[Tuple[Tuple[int, int], str]]:
    pos = 0
    text_inside = ""
    inside = False
    labels = []
    start_pos = None
    for char in labeled_text:
        if char == "[":
            if inside:
                pos += len(text_inside) + 1
            inside = True
            start_pos = pos
        elif inside and char == "]":
            #print(text_inside)
            if "|" in text_inside:
                qid, snippet = text_inside.split("|")
                pos += len(snippet)
                inside = False
                text_inside = ""
                labels.append(((start_pos, pos), qid))
            else:
                pos += len(text_inside) + 2
                inside = False
                text_inside = ""
        elif inside:
            text_inside += char
        else:
            pos += 1
    return labels


if __name__ == "__main__":
    benchmark_dir = "benchmark/"
    json_path = benchmark_dir + "development.jsonl"
    natalies_labels_path = benchmark_dir + "development_annotated_natalie.txt"
    matthias_labels_path = benchmark_dir + "development.txt"

    natalies_labels_texts = read_labeled_texts(natalies_labels_path, N_ARTICLES)
    matthias_labels_texts = read_labeled_texts(matthias_labels_path, N_ARTICLES)

    benchmark_articles = []

    with open(json_path) as json_file:
        for i in range(N_ARTICLES):
            json = next(json_file)
            if i not in SKIP_ARTICLES:
                article = article_from_json(json)
                #print("*** " + article.title + " ***")
                if len(benchmark_articles) < ARTICLES_SPLIT:
                    labels_text = natalies_labels_texts[i]
                else:
                    labels_text = matthias_labels_texts[i]
                #print(labels_text)
                labels = get_labels(labels_text)
                """for span, qid in labels:
                    begin, end = span
                    print(span, qid, article.text[begin:end])"""
                article.labels = labels
                benchmark_articles.append(article)
                print(article.to_json())
