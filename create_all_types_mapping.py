from typing import Set

import operator
import copy
import argparse

from src import settings
from src.helpers.entity_database_reader import EntityDatabaseReader


def get_super_classes_with_depth(qid: str, seen_classes: Set[str], depth: int):
    if qid not in qid_to_subclass_of_mapping:
        return set()

    all_classes = set()
    new_seen_classes = copy.copy(seen_classes)
    super_classes = qid_to_subclass_of_mapping[qid]
    new_seen_classes.update(super_classes)
    super_classes_with_depth = [(cl, depth) for cl in super_classes]
    all_classes.update(super_classes_with_depth)
    for cl in super_classes:
        if cl in seen_classes:
            continue
        new_super_classes = get_super_classes_with_depth(cl, new_seen_classes, depth + 1)
        all_classes.update(new_super_classes)

    return all_classes


def main(args):
    print("Create mapping from QID to all its types...")
    output_file = open(args.output_file, "w", encoding="utf8")
    for i, (qid, instance_of_set) in enumerate(qid_to_instance_of_mapping.items()):
        if qid in qid_to_subclass_of_mapping:
            instance_of_set.update(qid_to_subclass_of_mapping[qid])
        output_file.write("%s" % qid)
        distinct_classes = {cl: 0 for cl in instance_of_set}

        for cls in instance_of_set:
            super_classes = get_super_classes_with_depth(cls, set(), 1)
            for super_class, depth in super_classes:
                if super_class not in distinct_classes or depth < distinct_classes[super_class]:
                    distinct_classes[super_class] = depth
        for cls, depth in sorted(distinct_classes.items(), key=operator.itemgetter(1, 0)):
            output_file.write("\t%d:%s" % (depth, cls))
        output_file.write("\n")

        if (i + 1) % 1000 == 0:
            print("\rProcessed %d qids" % (i + 1), end='')

    print()
    print("Wrote mapping to %s" % args.output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("-o", "--output_file", type=str, default=settings.QID_TO_ALL_TYPES_FILE,
                        help="Output file.")

    print("Loading instance-of mapping...")
    qid_to_instance_of_mapping = EntityDatabaseReader.get_instance_of_mapping()
    print("Loading subclass-of mapping...")
    qid_to_subclass_of_mapping = EntityDatabaseReader.get_subclass_of_mapping()

    main(parser.parse_args())
