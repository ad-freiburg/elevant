import json
import sys

from src.helpers.entity_database_reader import EntityDatabaseReader
from src.models.wikipedia_article import article_from_json


if __name__ == "__main__":
    benchmark_name = sys.argv[1]
    in_file = "benchmarks/benchmark_labels_%s.jsonl" % benchmark_name

    # read whitelist
    whitelist = EntityDatabaseReader.read_whitelist_types()
    print(whitelist)

    # read benchmark
    articles = []
    entity_ids = set()
    with open(in_file) as f:
        for line in f:
            article = article_from_json(line)
            articles.append(article)
            for label in article.labels:
                entity_ids.add(label.entity_id)

    # read entity names from whitelist-to-type mapping
    entity_names = {}
    for entity_id, name in EntityDatabaseReader.entity_to_label_iterator():
        if entity_id in entity_ids:
            entity_names[entity_id] = name

    labels_tsv_file = "benchmarks/" + benchmark_name + ".labels.tsv"
    types_json_file = "benchmarks/" + benchmark_name + ".types.json"
    labels_tsv_file = open(labels_tsv_file, "w", encoding="utf8")

    print(len(articles))
    type_counts = {}
    total_counts = {True: 0, False: 0}
    num_labels = 0
    traditional_entity_types = {"Q18336849",  # person
                                "Q27096213",  # location
                                "Q43229"}  # organization
    known_labels = 0
    n_traditional_entities = 0
    for article in articles:
        num_labels += len(article.labels)
        for label in article.labels:
            mention = article.text[label.span[0]:label.span[1]]
            if label.entity_id.startswith("Unknown"):
                types = ["UNKNOWN"]
            else:
                types = label.type.split("|")
            entity_name = entity_names[label.entity_id] if label.entity_id in entity_names else "Unknown"
            print(mention, label.entity_id, entity_name, types, label.level1)
            labels_tsv_file.write("\t".join((mention,
                                             label.entity_id,
                                             entity_name,
                                             ", ".join(types),
                                             str(bool(label.level1))))
                                  + "\n")
            if "UNKNOWN" not in types:
                known_labels += 1
                is_traditional_entity_type = False
                for type in types:
                    if type not in type_counts:
                        type_counts[type] = {True: 0, False : 0}
                    type_counts[type][bool(label.level1)] += 1
                    if type in traditional_entity_types:
                        is_traditional_entity_type = True
                if is_traditional_entity_type:
                    n_traditional_entities += 1
                total_counts[bool(label.level1)] += 1

    labels_tsv_file.close()

    type_name_counts = {}
    for type in sorted(whitelist) + ["DATETIME", "QUANTITY", "OTHER", "UNKNOWN"]:
        type_name = whitelist[type] if type in whitelist else type
        if type in type_counts:
            lvl1_count = type_counts[type][True]
            other_count = type_counts[type][False]
        else:
            lvl1_count = other_count = 0
        print(type_name, lvl1_count, other_count)
        type_name_counts[type_name] = [lvl1_count, other_count]

    with open(types_json_file, "w", encoding="utf8") as f:
        f.write(json.dumps({"total": [total_counts[True], total_counts[False]],
                            "types": type_name_counts}))

    print(f"{n_traditional_entities / known_labels * 100:.2f}% of the known mentions are covered by "
          f"{traditional_entity_types}")
