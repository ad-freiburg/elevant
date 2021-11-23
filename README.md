# Entity Linking

## Docker Instructions
Get the code, and build and start the container:

    git clone git@github.com:ad-freiburg/wiki_entity_linker.git .
    docker build -t wiki-entity-linker .
    docker run -it -v <data_directory>:/data wiki-entity-linker

where `<data_directory>` is the directory that either already contains the necessary data files
or where you want to store the generated data files.

At our chair, the necessary data files already exist on wolga at `/local/data/entity-linking`,
so you can run the docker container using

    docker run -it -v /local/data/entity-linking:/data wiki-entity-linker

## Data Generation
If you do not already have access to existing data files, you can generate all necessary data files with a single command.

First however, make sure to set the `DATA_DIR` variable in the Makefile to `/data/` if you're using docker or to your `<data_directory>` otherwise.
In `src/settings.py` set the `EXTRACTED_WIKIPEDIA_DUMP_NAME` variable to `"enwiki-latest-extracted.jsonl"`

Then simply run

    make setup
    
This will generate all necessary data files.
The setup includes downloading and extracting the latest Wikipedia dump and will take several hours (~ 10h).

NOTE: This will overwrite existing Wikidata and Wikipedia mappings so make sure this is what you want to do.


## Usage

### Link Wikipedia Dump
To link an entire Wikipedia dump using our best system run
    
    make link_wiki
    
This uses our link-text-linker which links entities based on Wikipedia hyperlinks,
our popular-entities linker which links entities based on their Wikidata sitelink count with special rules for demonyms,
and our own coreference linker which uses type and gender information of previously linked entities and dependency parse information.

NOTE: Linking the entire Wikipedia dump will take several days.
You can adjust the number of threads used for linking via the Makefile variable `NUM_LINKER_THREADS`.
You can also limit the number of articles you want to link using command line arguments.
Type `python3 link_entities.py -h` for more information on the available command line arguments.

### Link Benchmark Articles
To link all benchmarks specified in the Makefile's `BENCHMARK_NAMES` variable
using all linking systems specified in the Makefile's `LINKING_SYSTEMS` variable run

    make link_benchmarks

The linking results are written to subdirectories in the directory specified in the Makefile's `EVALUATION_RESULTS_DIR` variable.
You can examine or adjust each system's exact linking arguments in the Makefile's `link_benchmark` target if needed.

If you don't want to use the Makefile for linking, e.g. if you want to link only a single benchmark with a
single specified linker configuration, use the script `link_benchmark_entities.py`, e.g.

    python3 link_benchmark_entities.py <linking_result_jsonl_file> popular_entities 15 --link_linker link-text-linker -coref entity -b wiki-ex

Use the `-h` option for more information on the command line arguments.
The linking result will be written to `<linking_result_jsonl_file> ` with one WikipediaArticle json object per line.


### Evaluate Linked Benchmark Articles

To evaluate the linking results in the subdirectories of the directory `EVALUATION_RESULTS_DIR`
for benchmarks specified in the Makefile's `BENCHMARK_NAMES` variable run

    make evaluate_linked_benchmarks

The evaluation results will be written to the same subdirectories in `EVALUATION_RESULTS_DIR`. 

This will create the files necessary for the `evaluation-webapp` and print precision, recall and F1 scores.
To show the evaluation results in the webapp, follow the instructions in `evaluation-webapp`.

If you don't want to use the Makefile for the evaluation, e.g. if you want to evaluate only a single linking result file,
use the script `evaluate_linked_entities.py`:

    python3 evaluate_linked_entities.py <linking_result_jsonl_file>


### Initialize and Train Spacy Entity Linker

1. Generate word vectors:

       python3 create_entity_word_vectors.py 0
2. Create the knowledge base:

       python3 create_knowledge_base_wikipedia.py
3. Train the entity linker:

       python3 train_spacy_entity_linker.py <linker_name> <n_batches> wikipedia

## Notes

If you want to be able to run coreference with the Stanford CoreNLP coreference resolution system, make sure to setup Stanford CoreNLP by running

    ./setup_stanford_coref.sh
