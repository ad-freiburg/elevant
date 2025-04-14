import argparse
import pickle
import time
import lmdb
import sys
from typing import Optional
from urllib.parse import unquote
from enum import Enum

sys.path.append(".")

from elevant.utils import log


WIKI_URL_PREFIX = "https://en.wikipedia.org/wiki/"


class StorageFormat(Enum):
    SINGLE_VAL = "single_value"
    MULTI_VALS = "multiple_values"
    MULTI_VALS_TS = "multiple_values_tab_separated"
    MULTI_VALS_SS = "multiple_values_semicolon_separated"


class ValueProcessingMethod(Enum):
    NAME_FROM_URL = "name_from_url"


def read_from_pkl(filename: str, separator: str = ","):
    logger.info(f"Reading from file {filename} ...")
    start = time.time()
    with open(filename, "rb") as f:
        d = pickle.load(f)
        if StorageFormat.MULTI_VALS:
            new_d = {}
            for key, value in d.items():
                if type(value) is list:
                    string = ""
                    for i, v in enumerate(value):
                        string += v
                        if i < len(value) - 1:
                            string += separator
                    new_d[key] = string
                else:
                    new_d[key] = value
            d = new_d
    logger.info(f"Done. Took {time.time() - start} s")
    return d


def read_from_tsv(filename, storage_format=StorageFormat.SINGLE_VAL, processing_method=None, inverse=False,
                  separator=","):
    logger.info(f"Reading from file {filename} ...")
    start = time.time()
    d = {}
    with open(filename, "r", encoding="utf8") as f:
        for line in f:
            lst = line.strip("\n").split("\t")
            if len(lst) < 2:
                logger.warning(f"Skipping line that contains less than two values: \"{line}\". "
                               f"This might be an indication that the data from {filename} is not complete.")
                continue
            if storage_format == StorageFormat.SINGLE_VAL:
                if inverse:
                    key = process(lst[1], processing_method)
                    d[key] = lst[0]
                else:
                    d[lst[0]] = process(lst[1], processing_method)
            elif storage_format == StorageFormat.MULTI_VALS:
                if inverse:
                    curr_key = process(lst[1], processing_method)
                    curr_val = lst[0]
                    if curr_key in d:
                        prev_val = d[curr_key]
                        d[curr_key] = prev_val + separator + curr_val
                    else:
                        d[curr_key] = curr_val
                else:
                    curr_key = lst[0]
                    curr_val = process(lst[1], processing_method)
                    if curr_key in d:
                        prev_val = d[curr_key]
                        d[curr_key] = prev_val + separator + curr_val
                    else:
                        d[curr_key] = curr_val
            elif storage_format in [StorageFormat.MULTI_VALS_SS, StorageFormat.MULTI_VALS_TS]:
                value_separator = ";" if storage_format == StorageFormat.MULTI_VALS_SS else "\t"
                if inverse:
                    keys = lst[1].split(value_separator)
                    for key in keys:
                        key = process(key, processing_method)
                        if key in d:
                            prev_val = d[key]
                            d[key] = prev_val + separator + lst[0]
                        else:
                            d[key] = lst[0]
                else:
                    vals = [process(v, processing_method) for v in lst[1].split(value_separator)]
                    # Use the original value separator also in the DB, since the data might contain commas
                    val = value_separator.join(vals)
                    d[lst[0]] = val

    logger.info(f"Done. Took {time.time() - start} s")
    return d


def read_most_popular_candidates(filename: str):
    logger.info(f"Reading most popular hyperlink aliases from file {filename} ...")
    start = time.time()
    with open(filename, "rb") as f:
        d = pickle.load(f)
        new_d = {}
        for link_text, frequency_dict in d.items():
            most_popular_candidates = []
            max_frequency = 0
            for entity_id, frequency in frequency_dict.items():
                if frequency > max_frequency:
                    most_popular_candidates = [entity_id]
                    max_frequency = frequency
                elif frequency == max_frequency:
                    most_popular_candidates.append(entity_id)
            if most_popular_candidates:
                new_d[link_text] = ",".join(most_popular_candidates)
        d = new_d
    logger.info(f"Done. Took {time.time() - start} s")
    return d


def process(value: str, method: Optional[ValueProcessingMethod] = None) -> str:
    if method == ValueProcessingMethod.NAME_FROM_URL:
        # Can't use rfind("/") here, because some entity names contain "/", e.g.
        # https://www.wikidata.org/wiki/Q51402020
        value = value[len(WIKI_URL_PREFIX):]
        value = unquote(value)
        value = value.replace('_', ' ')
    return value


def write_to_dbm(d, filename):
    logger.info(f"Writing database to file {filename} ...")
    start = time.time()
    count = 0
    # Set max map size to 40 GB. There is allegedly no penalty for making this huge on 64 bit systems.
    env = lmdb.open(filename, map_size=42949672960)
    with env.begin(write=True) as db:
        # Store the dictionary data in the database
        for key, value in d.items():
            try:
                db.put(key.encode("utf-8"), value.encode("utf-8"))
            except lmdb.BadValsizeError:
                logger.warning(f"\nFailed to write key \"{key}\" with value \"{value}\".")
            count += 1
            if count % 100000 == 0:
                print(f"\rWrote {count} items of {len(d)}.", end="")
        print()
    env.close()
    logger.info(f"Done. Took {time.time() - start} s")


def main(args):
    output_file = args.output_file if args.output_file else args.input_file[:args.input_file.rfind(".")] + ".db"

    storage_format = StorageFormat(args.format)
    processing_method = ValueProcessingMethod(args.processing_method) if args.processing_method else None

    if args.most_popular_candidates:
        dictionary = read_most_popular_candidates(args.input_file)
    elif args.input_file.endswith(".pkl"):
        dictionary = read_from_pkl(args.input_file)
    else:
        dictionary = read_from_tsv(args.input_file, storage_format, processing_method, inverse=args.inverse)

    write_to_dbm(dictionary, output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("input_file", type=str,
                        help="Input file to transform to DB. Either TSV or PKL file.")
    parser.add_argument("-o", "--output_file", type=str,
                        help="File name of the generated DB. Default: Input filename with suffix .db")
    parser.add_argument("-f", "--format", type=str, choices=[f.value for f in StorageFormat],
                        default=StorageFormat.SINGLE_VAL, help="Storage format of the input file")
    parser.add_argument("-m", "--processing_method", type=str, choices=[m.value for m in ValueProcessingMethod],
                        default=None, help="Processing method that will be applied to each value in the database.")
    parser.add_argument("-i", "--inverse", action="store_true",
                        help="Use the original keys (left-most element) as values, and the values as keys.")
    parser.add_argument("--most_popular_candidates", action="store_true",
                        help="Create a database that contains a mapping from hyperlink text to the its popular entity"
                             "candidates.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main(parser.parse_args())
