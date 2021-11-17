import argparse
import log
import sys

from src.evaluation.benchmark import Benchmark
from src.evaluation.examples_generator import get_example_generator


def main(args):
    logger.info("Writing %s articles in jsonl format to %s ..." % (args.benchmark, args.output_file))
    example_generator = get_example_generator(args.benchmark)

    output_file = open(args.output_file, 'w', encoding='utf8')

    for i, article in enumerate(example_generator.iterate(args.n_articles)):
        output_file.write(article.to_json() + '\n')
        print("\r%i articles" % (i + 1), end='')
    print()

    output_file.close()
    logger.info("Wrote %d articles to %s" % (i+1, args.output_file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=__doc__)

    parser.add_argument("output_file", type=str, default=None,
                        help="Output file.")
    parser.add_argument("-b", "--benchmark", choices=[b.value for b in Benchmark], default=Benchmark.WIKI_EX.value,
                        help="Benchmark for which to write the article with labels.")
    parser.add_argument("-n", "--n_articles", type=int, default=-1,
                        help="Number of articles to write.")

    logger = log.setup_logger(sys.argv[0])
    logger.debug(' '.join(sys.argv))

    main(parser.parse_args())
