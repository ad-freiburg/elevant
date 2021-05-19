from typing import List, Tuple

from src import settings
from src.evaluation.groundtruth_label import GroundtruthLabel
from src.models.wikipedia_article import article_from_json


START_TAG = "<START>"
END_TAG = "<END>"
N_ARTICLES = 43
ARTICLES_SPLIT = 100
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

    # Append remaining lines if limit of n was not reached before
    if len(lines) > 0:
        texts.append("".join(lines))
        return texts


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
                if ":" in qid:
                    qid = qid.split(":")[0]
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


def get_nested_labels(labeled_text: str) -> List[GroundtruthLabel]:
    """
    Labels can be nested.
    """
    pos = 0
    labels = []
    inside = 0  # Indicates current annotation nesting level
    article_labels = []
    original_texts = []  # Maps nesting levels to a list of original texts at this nesting level
    label_ids = []  # Maps nesting levels to a list of label ids at this nesting level
    start_pos = []
    original_text_cell = False
    entity_name_cell = False
    label_id_counter = 0
    for char_idx, char in enumerate(labeled_text):
        if char == "[":
            # At the beginning of an annotation
            # Make sure it's actually an annotation and not just a feature of the original text, e.g. [to]
            # Use the fact that the label of an annotation occurs before any potential nesting, i.e. [label|...]
            next_delimiter = labeled_text.find("|", char_idx + 1)
            substring = labeled_text[char_idx + 1:next_delimiter]
            if "[" in substring or "]" in substring:
                pos += 1
            else:
                inside += 1
                original_text_cell = False
                start_pos.append(pos)
                if len(original_texts) < inside:
                    original_texts.append([])
                original_texts[inside-1].append("")

                if len(label_ids) < inside:
                    label_ids.append([])
                label_ids[inside-1].append(label_id_counter)
                label_id_counter += 1

                labels.append("")
        elif inside > 0 and char == "|":
            # Inside of an annotation reaching the original text cell
            original_text_cell = True
            entity_name_cell = False
        elif inside > 0 and char == "]":
            # At the end of an annotation
            original_text = original_texts[inside-1][-1]
            end_pos = len(original_text)
            parent = label_ids[inside-2][-1] if inside-2 >= 0 else None
            # TODO: This only adds direct children and not children of children. Depending on further implementation
            #  this is enough though. Additionally, double nesting might not even occur.
            children = label_ids[inside] if inside < len(label_ids) else None
            label_id = label_ids[inside-1][-1]
            groundtruth_label = GroundtruthLabel(label_id, (start_pos[-1], start_pos[-1] + end_pos), labels[-1],
                                                 parent=parent, children=children)
            article_labels.append(groundtruth_label)
            del labels[-1]
            del start_pos[-1]
            inside -= 1
            if inside == 0:
                original_text_cell = False
                original_texts = []
                start_pos = []
                label_ids = []
        elif inside > 0 and original_text_cell:
            # Inside of an annotation in the original text cell
            original_texts[inside-1][-1] += char
            # Also update all original texts of lower nesting levels
            for i in range(0, inside-1):
                for j in range(len(original_texts[i])):
                    original_texts[i][j] += char
            pos += 1
        elif inside > 0:
            # Inside of an annotation in the label cell
            if char == ":":
                entity_name_cell = True
            elif not entity_name_cell:
                labels[-1] += char
        else:
            # Outside of an annotation
            pos += 1
    return article_labels


if __name__ == "__main__":
    benchmark_dir = "benchmark/"
    json_path = "/local/data/prangen/benchmark/development_labels.jsonl"
    json_path2 = "benchmark/development.bold.jsonl"
    curr_benchmark_file = settings.OWN_BENCHMARK_FILE
    annotated_file = "benchmark/benchmark_ours_for_annotation.txt"
    # natalies_labels_path = "benchmark/development_annotated.txt"
    # matthias_labels_path = benchmark_dir + "development.txt"

    # natalies_labels_texts = read_labeled_texts(natalies_labels_path, N_ARTICLES)
    # matthias_labels_texts = read_labeled_texts(matthias_labels_path, N_ARTICLES)
    labels_texts = read_labeled_texts(annotated_file, N_ARTICLES)

    benchmark_articles = []

    with open(curr_benchmark_file) as json_file:
        for i in range(N_ARTICLES):
            if i not in SKIP_ARTICLES:
                json = next(json_file)
                article = article_from_json(json)
                #print("*** " + article.title + " ***")
                if len(benchmark_articles) < ARTICLES_SPLIT:
                    labels_text = labels_texts[i]
                else:
                    pass  #labels_text = matthias_labels_texts[i]
                #print(labels_text)
                labels = get_nested_labels(labels_text)
                """for span, qid in labels:
                    begin, end = span
                    print(span, qid, article.text[begin:end])"""
                article.labels = labels
                benchmark_articles.append(article)
                print(article.to_json())
