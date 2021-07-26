import argparse
import sys

from src import settings
from src.evaluation.benchmark import Benchmark
from src.evaluation.evaluator import is_level_one
from src.evaluation.examples_generator import get_example_generator
from src.evaluation.groundtruth_label import GroundtruthLabel
from src.helpers.entity_database_reader import EntityDatabaseReader


def main(args):
    if not (args.level or args.type):
        print("Specify at least one type of annotation: -t for type or -l for level")
        sys.exit()

    output_file = open(args.output_file, "w", encoding="utf8")

    example_iterator = get_example_generator(args.benchmark, from_json_file=False)
    label_entity_ids = set()
    for article in example_iterator.iterate():
        for label in article.labels:
            label_entity_ids.add(label.entity_id)

    print("Read whitelist type mapping file..")
    entities = EntityDatabaseReader.get_wikidata_entities_with_types(label_entity_ids)

    for article in example_iterator.iterate():
        for label in article.labels:
            if label.entity_id.startswith("Unknown"):
                continue
            if args.type:
                if label.type in (GroundtruthLabel.QUANTITY, GroundtruthLabel.DATETIME):
                    continue
                if label.entity_id in entities:
                    label.type = entities[label.entity_id].type
                else:
                    print("Entity %s:%s was not found in entity-type mapping." %
                          (label.entity_id, label.name))
            if args.level:
                if label.entity_id in entities:
                    label.level1 = is_level_one(entities[label.entity_id].name)
                else:
                    label.level1 = False
            if args.name:
                label.name = entities[label.entity_id].name if label.entity_id in entities else "Unknown"

        output_file.write(article.to_json() + '\n')

    output_file.close()
    print("Wrote new articles to %s" % args.output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("-out", "--output_file", type=str, required=True,
                        help="Output file with one benchmark article in json format per line.")
    parser.add_argument("-t", "--type", action="store_true",
                        help="Annotate benchmark labels with their Wikidata whitelist type(s).")
    parser.add_argument("-l", "--level", action="store_true",
                        help="Annotate benchmark labels with level (level 1 or not level 1).")
    parser.add_argument("-n", "--name", action="store_true",
                        help="Annotate benchmark labels with their Wikidata name.")
    parser.add_argument("--type_file", type=str, default=settings.WHITELIST_TYPE_MAPPING,
                        help="The entity-to-type-mapping file. Default: settings.WHITELIST_TYPE_MAPPING")
    parser.add_argument("-b", "--benchmark", choices=[b.value for b in Benchmark], default=Benchmark.OURS.value,
                        help="Benchmark in which to annotate the labels. Default: Our benchmark.")

    main(parser.parse_args())
