import argparse
import sys

from src import settings
from src.evaluation.benchmark import Benchmark
from src.evaluation.evaluator import prediction_is_level_one
from src.evaluation.examples_generator import get_example_generator
from src.evaluation.groundtruth_label import GroundtruthLabel


def main(args):
    if not (args.level or args.type):
        print("Specify at least one type of annotation: -t for type or -l for level")
        sys.exit()

    output_file = open(args.output_file, "w", encoding="utf8")

    example_iterator = get_example_generator(args.benchmark)
    label_entity_ids = set()
    for article in example_iterator.iterate():
        for label in article.labels:
            label_entity_ids.add(label.entity_id)

    id_to_type = dict()
    id_to_name = dict()
    print("Read whitelist type mapping file..")
    with open(args.type_file, "r", encoding="utf8") as file:
        for line in file:
            lst = line.strip().split("\t")
            entity_id = lst[0][:-1].split("/")[-1]
            name = lst[1][1:-3]
            whitelist_type = lst[2][:-1].split("/")[-1]
            if entity_id in label_entity_ids:
                if entity_id not in id_to_type:  # An entity can have multiple types from the whitelist
                    id_to_type[entity_id] = []
                id_to_type[entity_id].append(whitelist_type)
                id_to_name[entity_id] = name

    for article in example_iterator.iterate():
        for label in article.labels:
            if label.entity_id.startswith("Unknown"):
                continue
            if args.type:
                if label.type in (GroundtruthLabel.QUANTITY, GroundtruthLabel.DATETIME):
                    continue
                if label.entity_id in id_to_type:
                    type_list = id_to_type[label.entity_id]
                    label.type = "|".join(type_list)
                    if len(type_list) > 1:
                        print("More than one whitelist type found for entity %s:%s. Types: %s" %
                              (label.entity_id, label.name, type_list))
                else:
                    print("Entity %s:%s was not found in entity-type mapping." %
                          (label.entity_id, label.name))
            if args.level:
                label.level1 = False
                if prediction_is_level_one(id_to_name, label.entity_id):
                    label.level1 = True

        output_file.write(article.to_json() + '\n')

    output_file.close()
    print("Wrote new articles to %s" % args.output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("-out", "--output_file", type=str, required=True,
                        help="Output file with one benchmark article in json format per line.")
    parser.add_argument("-t", "--type", action="store_true",
                        help="Annotate benchmark labels with type.")
    parser.add_argument("-l", "--level", action="store_true",
                        help="Annotate benchmark labels with level (level 1 or not level 1).")
    parser.add_argument("--type_file", type=str, default=settings.WHITELIST_TYPE_MAPPING,
                        help="The entity-to-type-mapping file. Default: settings.WHITELIST_TYPE_MAPPING")
    parser.add_argument("-b", "--benchmark", choices=[b.value for b in Benchmark], default=Benchmark.OURS.value,
                        help="Benchmark in which to annotate the labels. Default: Our benchmark.")

    main(parser.parse_args())
