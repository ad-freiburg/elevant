import argparse
import json
import log
import sys

from src.evaluation.benchmark import get_available_benchmarks
from src.evaluation.mention_type import is_named_entity
from src.helpers.entity_database_reader import EntityDatabaseReader
from src.models.article import article_from_json


def main(args):
    benchmark_name = args.benchmark_name
    in_file = "benchmarks/benchmark_labels_%s.jsonl" % benchmark_name
    logger.info("Analyzing entity types in %s" % in_file)

    # read whitelist
    whitelist = EntityDatabaseReader.read_whitelist_types()

    # read benchmark
    articles = []
    entity_ids = set()
    with open(in_file) as f:
        for line in f:
            article = article_from_json(line)
            articles.append(article)
            for label in article.labels:
                entity_ids.add(label.entity_id)

    # read entity labels
    entity_names = {}
    for entity_id, name in EntityDatabaseReader.entity_to_label_iterator():
        if entity_id in entity_ids:
            entity_names[entity_id] = name

    labels_tsv_filename = "benchmarks/" + benchmark_name + ".labels.tsv"
    types_json_filename = "benchmarks/" + benchmark_name + ".types.json"
    labels_tsv_file = open(labels_tsv_filename, "w", encoding="utf8")

    type_counts = {}
    total_counts = {True: 0, False: 0}
    num_labels = 0
    traditional_entity_types = {"Q18336849",  # person
                                "Q27096213",  # location
                                "Q43229"}  # organization
    known_labels = 0
    n_traditional_entities = 0
    for article in articles:
        for label in article.labels:
            if label.parent is not None:
                continue
            num_labels += 1
            mention = article.text[label.span[0]:label.span[1]]
            if label.entity_id.startswith("Unknown"):
                types = ["UNKNOWN"]
            else:
                types = label.type.split("|")
            entity_name = entity_names[label.entity_id] if label.entity_id in entity_names else "Unknown"
            labels_tsv_file.write("\t".join((mention,
                                             label.entity_id,
                                             entity_name,
                                             ", ".join(types),
                                             str(is_named_entity(label.name))))
                                  + "\n")
            if "UNKNOWN" not in types:
                known_labels += 1
            is_traditional_entity_type = False
            for type in types:
                if type not in type_counts:
                    type_counts[type] = {True: 0, False: 0}
                type_counts[type][is_named_entity(label.name)] += 1
                if type in traditional_entity_types:
                    is_traditional_entity_type = True
            if is_traditional_entity_type:
                n_traditional_entities += 1
            total_counts[is_named_entity(label.name)] += 1

    labels_tsv_file.close()

    type_name_counts = {}
    for type in sorted(whitelist) + ["DATETIME", "QUANTITY", "OTHER", "UNKNOWN"]:
        type_name = whitelist[type] if type in whitelist else type
        if type in type_counts:
            lvl1_count = type_counts[type][True]
            other_count = type_counts[type][False]
        else:
            lvl1_count = other_count = 0
        type_name_counts[type_name] = [lvl1_count, other_count]

    with open(types_json_filename, "w", encoding="utf8") as f:
        f.write(json.dumps({"total": [total_counts[True], total_counts[False]],
                            "types": type_name_counts}))

    logger.info(f"{n_traditional_entities / known_labels * 100:.2f}% of the known mentions are covered by "
                f"{traditional_entity_types}")
    logger.info("Wrote analyzed entity types to %s and %s." % (labels_tsv_filename, types_json_filename))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=__doc__)

    parser.add_argument("benchmark_name", type=str, required=True, choices=get_available_benchmarks(),
                        help="Name of the benchmark to be analyzed.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main(parser.parse_args())
