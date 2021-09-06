import argparse
import re
from typing import List, Tuple, Optional

from src import settings
from src.evaluation.groundtruth_label import GroundtruthLabel
from src.models.wikipedia_article import article_from_json


START_TAG = "<START>"
END_TAG = "<END>"
N_ARTICLES = 83
ARTICLES_SPLIT = 100
SKIP_ARTICLES = {2, 10, 14}


def read_labeled_texts(path: str, n: Optional[int] = None) -> List[str]:
    texts = []
    lines = []
    for line in open(path):
        if line.startswith("**** ARTICLE"):
            if len(lines) > 0:
                texts.append("".join(lines))
                lines = []
                if n is not None and len(texts) == n:
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
    optional_tags = []
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
                optional_tags.append(False)
        elif inside > 0 and char == "|":
            # Inside of an annotation reaching the original text cell
            original_text_cell = True
            entity_name_cell = False
        elif inside > 0 and char == "]":
            # At the end of an annotation
            original_text = original_texts[inside-1][-1]
            end_pos = len(original_text)
            parent = label_ids[inside-2][-1] if inside-2 >= 0 else None
            children = label_ids[inside] if inside < len(label_ids) else None
            label_id = label_ids[inside-1][-1]
            label_type = labels[-1] if not labels[-1].startswith("Unknown") \
                and not re.match(r"Q[0-9]+", labels[-1]) else GroundtruthLabel.OTHER
            entity_name = "Unknown"
            groundtruth_label = GroundtruthLabel(label_id, (start_pos[-1], start_pos[-1] + end_pos), labels[-1],
                                                 entity_name, parent=parent, children=children,
                                                 optional=optional_tags[-1], type=label_type)
            article_labels.append(groundtruth_label)
            del optional_tags[-1]
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
            for k in range(0, inside-1):
                for j in range(len(original_texts[k])):
                    original_texts[k][j] += char
            pos += 1
        elif inside > 0:
            # Inside of an annotation in the label cell
            if char == ":":
                if labels[-1] == "OPTIONAL":
                    optional_tags[-1] = True
                    labels[-1] = ""
                else:
                    entity_name_cell = True
            elif not entity_name_cell:
                labels[-1] += char
        else:
            # Outside of an annotation
            pos += 1
    return article_labels


def main(args):
    labels_texts = read_labeled_texts(args.input_file, args.num_articles)

    output_file = None
    if args.output_file:
        output_file = open(args.output_file, "w", encoding="utf8")

    title_span_jsonl_file = None
    if args.title_span_jsonl_file:
        title_span_jsonl_file = open(args.title_span_jsonl_file, "r")

    article_count = 0
    skip_count = 0
    with open(args.article_jsonl_file) as jsonl_file:
        for i, json in enumerate(jsonl_file):
            if i + skip_count >= len(labels_texts) or \
                    (args.num_articles is not None and article_count >= args.num_articles):
                break
            if title_span_jsonl_file:
                title_span_json = next(title_span_jsonl_file)
            if not args.skip or i + skip_count not in SKIP_ARTICLES:
                if not args.skip and i + skip_count in SKIP_ARTICLES:
                    skip_count += 1
                article = article_from_json(json)
                labels = get_nested_labels(labels_texts[i + skip_count])
                article.labels = labels

                if title_span_jsonl_file:
                    article_title_spans = article_from_json(title_span_json)
                    article.title_synonyms = article_title_spans.title_synonyms

                if output_file:
                    output_file.write(article.to_json() + "\n")
                else:
                    print(article.to_json())
                article_count += 1

    if output_file:
        output_file.close()
    if title_span_jsonl_file:
        title_span_jsonl_file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("input_file", type=str,
                        help="Input benchmark with annotations in the format [<QID>|<original_text>].")

    parser.add_argument("-out", "--output_file", type=str, default=None,
                        help="File to write the labeled benchmark to (one json article per line).")

    parser.add_argument("-n", "--num_articles", type=int, default=None,
                        help="Number of articles to read from the input file.")

    parser.add_argument("--skip", action="store_true",
                        help="Set if the article_jsonl_file contains those articles that should be skipped.")

    parser.add_argument("--article_jsonl_file", type=str, default=settings.OWN_BENCHMARK_FILE,
                        help="File that contains the original article in jsonl format"
                             "(for additional info like hyperlink spans). If the settings.OWN_BENCHMARK_FILE"
                             "does not contain all articles because the benchmark is being extended, use e.g."
                             "benchmarks/benchmark_articles.all.jsonl")

    parser.add_argument("--title_span_jsonl_file", type=str, default=None,
                        help="File that contains the benchmark articles including bold title span info."
                             "Only needed if the benchmark is extended."
                             "(E.g. benchmarks/benchmark_articles.all.bold.jsonl. This can't simply be used as"
                             "article_jsonl_file, since the article texts slightly differ from the benchmark version)")

    main(parser.parse_args())
