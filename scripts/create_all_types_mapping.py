from typing import Set

import operator
import copy
import argparse
import sys

sys.path.append(".")

from elevant import settings
from elevant.utils import log
from elevant.helpers.entity_database_reader import EntityDatabaseReader


class AllTypesMappingCreator:
    def __init__(self, qid_to_instanceof_mapping, qid_to_subclassof_mapping):
        self.qid_to_instanceof_mapping = qid_to_instanceof_mapping
        self.qid_to_subclassof_mapping = qid_to_subclassof_mapping

    def get_super_classes_with_depth(self, qid: str, seen_classes: Set[str], depth: int):
        if qid not in self.qid_to_subclassof_mapping:
            return set()

        all_classes = set()
        new_seen_classes = copy.copy(seen_classes)
        super_classes = self.qid_to_subclassof_mapping[qid]
        new_seen_classes.update(super_classes)
        super_classes_with_depth = [(cl, depth) for cl in super_classes]
        all_classes.update(super_classes_with_depth)
        for cl in super_classes:
            if cl in seen_classes:
                continue
            new_super_classes = self.get_super_classes_with_depth(cl, new_seen_classes, depth + 1)
            all_classes.update(new_super_classes)

        return all_classes

    def all_types_iterator(self):
        for i, (qid, instance_of_set) in enumerate(self.qid_to_instanceof_mapping.items()):
            if qid in self.qid_to_subclassof_mapping:
                instance_of_set.update(self.qid_to_subclassof_mapping[qid])
            distinct_classes = {cl: 0 for cl in instance_of_set}

            for cls in instance_of_set:
                super_classes = self.get_super_classes_with_depth(cls, set(), 1)
                for super_class, depth in super_classes:
                    if super_class not in distinct_classes or depth < distinct_classes[super_class]:
                        distinct_classes[super_class] = depth
            yield qid, distinct_classes


def main(args):
    logger.info("Read sitelink counts. Ignore entities with sitelink count < %d" % args.min_count)
    sitelink_db = EntityDatabaseReader.get_sitelink_db()
    relevant_entities = set()
    for entity_id, sitelink_count in sitelink_db.items():
        if sitelink_count >= args.min_count:
            relevant_entities.add(entity_id)
    logger.info("Number of entities with sitelink count >= %d: %d" % (args.min_count, len(relevant_entities)))

    logger.info("Loading instance-of mapping for relevant entities...")
    qid_to_instance_of_mapping = EntityDatabaseReader.get_instance_of_mapping(relevant_entities)

    logger.info("Loading subclass-of mapping...")
    qid_to_subclassof_mapping = EntityDatabaseReader.get_subclass_of_mapping()

    mapping_creator = AllTypesMappingCreator(qid_to_instance_of_mapping, qid_to_subclassof_mapping)

    output_file = open(args.output_file, "w", encoding="utf8")

    logger.info("Create mapping from entity QID to all corresponding types...")
    for i, (qid, distinct_classes) in enumerate(mapping_creator.all_types_iterator()):
        output_file.write("%s" % qid)
        for cls, depth in sorted(distinct_classes.items(), key=operator.itemgetter(1, 0)):
            output_file.write("\t%d:%s" % (depth, cls))
        output_file.write("\n")
        if (i + 1) % 1000 == 0:
            print("\rProcessed %d entities" % (i + 1), end='')

    print()
    logger.info("Wrote mapping for %d entities to %s" % (i+1, args.output_file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("-o", "--output_file", type=str, default=settings.QID_TO_ALL_TYPES_FILE,
                        help="Output file.")
    parser.add_argument("-min", "--min_count", type=int, default=2,
                        help="Write only entities to the output file with a sitelink count >= min_count.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main(parser.parse_args())
