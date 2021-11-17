import argparse
import log
import sys

from src import settings
from src.evaluation.benchmark import Benchmark
from src.evaluation.examples_generator import get_example_generator
from src.evaluation.groundtruth_label import GroundtruthLabel, is_level_one
from src.helpers.entity_database_reader import EntityDatabaseReader


def main(args):
    logger.info("Annotate %s groundtruth labels with Wikidata label, type and level-1 information." % args.benchmark)
    output_file = open(args.output_file, "w", encoding="utf8")

    example_iterator = get_example_generator(args.benchmark, from_json_file=False)
    label_entity_ids = set()
    for article in example_iterator.iterate():
        for label in article.labels:
            label_entity_ids.add(label.entity_id)

    logger.info("Loading entity information..")
    entities = EntityDatabaseReader.get_wikidata_entities_with_types(label_entity_ids, settings.WHITELIST_TYPE_MAPPING)

    for article in example_iterator.iterate():
        for label in article.labels:
            if label.entity_id.startswith("Unknown"):
                continue
            if label.type in (GroundtruthLabel.QUANTITY, GroundtruthLabel.DATETIME):
                continue

            if label.entity_id in entities:
                label.type = entities[label.entity_id].type
            else:
                logger.warning("Entity %s:%s was not found in entity-type mapping." %
                               (label.entity_id, label.name))

            if label.entity_id in entities:
                label.level1 = is_level_one(entities[label.entity_id].name)
            else:
                label.level1 = False

            label.name = entities[label.entity_id].name if label.entity_id in entities else "Unknown"

        output_file.write(article.to_json() + '\n')

    output_file.close()
    logger.info("Wrote new articles to %s" % args.output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=__doc__)

    parser.add_argument("-o", "--output_file", type=str, required=True,
                        help="Output file with one benchmark article in json format per line.")
    parser.add_argument("-b", "--benchmark", choices=[b.value for b in Benchmark], default=Benchmark.WIKI_EX.value,
                        help="Benchmark in which to annotate the labels. Default: Our benchmark.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main(parser.parse_args())
