# Entity Linking Evaluation & Analysis Tool

## Docker Instructions
Get the code, and build and start the container:

    git clone git@github.com:ad-freiburg/elevant.git .
    docker build -t elevant .
    docker run -it -p 8000:8000 -v <data_directory>:/data -v $(pwd)/evaluation_results/:/home/evaluation_results -v $(pwd)/benchmarks/:/home/benchmarks elevant

where `<data_directory>` is the directory in which the required data files will be stored.
What these data files are and how they are generated is explained in section [Get the Data](#get-the-data).

Unless otherwise noted, all the following commands should be run inside the docker container.

## Get the Data
For linking entities in text or evaluating the output of a linker, our system needs information about entities and mention texts,
e.g. entity labels, aliases, popularity scores, types, the frequency with which a mention is linked to a certain article in Wikipedia, etc.
This information is stored in and read from several files.
Since these files are too large to upload them on GitHub, you can either download them from our servers (fast)
or build them yourself (slow, RAM intensive, but the resulting files might be based on a more recent Wikidata/Wikipedia dump).

To download the files, run the following three commands
(if for some reason you don't want to run these commands within the docker container,
make sure to set the `DATA_DIR` variable in the Makefile to your `<data_directory>` before):

    make download_wikidata_mappings
    make download_wikipedia_mappings
    make download_entity_types_mapping

This will download the compressed files, extract them and move them to the correct location.
See [Mapping Files](docs/mapping_files.md) for a description of files generated in these steps.

NOTE: This will overwrite existing Wikidata and Wikipedia mappings in your `<data_directory>` so make sure this is
what you want to do.

If you rather want to build the mappings yourself, you can replace each *download* command by a *generate* command.
See [Data Generation](docs/data_generation.md) for more details.

## Start the Web App

To start the evaluation web app, run

    make start_webapp
You can then access the webapp at <http://0.0.0.0:8000/>.

In the benchmark dropdown menu, you can select any benchmark for which a benchmark file in the correct format exists at
`benchmarks/benchmark_labels_<benchmark_name>.jsonl`.
The section [Add a Benchmark](#add-a-benchmark) explains how you can add more benchmarks yourself.

A benchmark's evaluation results table contains one row for each experiment,
that is, one row for each `.jsonl` file in a `evaluation_results/*/` directory
with a corresponding `.cases` and `.results` file.
We already added a few experiments, in particular oracle predictions for each benchmark
(i.e. perfect linking results generated from the ground truth),
so you can start exploring the web app right away.
The section [Add an Experiment](#add-an-experiment) explains how you can add more experiments yourself.

## Add a Benchmark

You can easily add a benchmark if you have a `<benchmark_file>` that is in the jsonl format we use,
in the common NLP Interchange Format (NIF)
or in the IOB-based format used by Hoffart et al. for their AIDA/CoNLL benchmark.
Benchmarks in other formats have to be converted into one of these formats first.

To add a benchmark, simply run

    python3 create_benchmark_labels.py -name <benchmark_name> -bfile <benchmark_file> -bformat <nif|ours|aida-conll>

This will create a benchmark file `benchmarks/benchmark_labels_<benchmark_name>.jsonl` in our jsonl format where
ground truth labels are annotated with their Wikidata label and types.

In the web app, reload the page and the benchmark will show up in the benchmark dropdown menu.

The benchmark can now be linked with a linker of your choice using the
`link_benchmark_entities.py` script with the parameter `-b <benchmark_name>`.
See section [Add an Experiment](#add-an-experiment) for details on how to link a benchmark.

## Add an Experiment

You can add an experiment, i.e. a row in the table for a particular benchmark,
in two steps: 1) link the benchmark articles and 2) evaluate the linking results.
Both steps are explained in the following two sections.

### Link Benchmark Articles
To link the articles of a benchmark with a single linker configuration, use the script `link_benchmark_entities.py`:

    python3 link_benchmark_entities.py <experiment_name> <linker_type> <linker_info> -b <benchmark_name>

The linking results will be written to `evaluation_results/<linker_type>/<experiment_name>.<benchmark_name>.jsonl`
with one article as json object per line. Each json object contains benchmark article information such as the
article title, text, and ground truth labels, as well as the entity mentions produced by the specified linker.

For example

    python3 link_benchmark_entities.py tagme.thresh02 tagme 0.2 -b msnbc

will create the file `evaluation_results/tagme/tagme.thresh02.msnbc.jsonl`.

In case you have linking results in NIF format for a certain benchmark, run

    python3 link_benchmark_entities.py <experiment_name> nif <path_to_nif_linking_results_file> -b <benchmark_name>
This will transform the linking results into the json format described above.

Run `python3 link_benchmark_entities.py -h` for more information on the command line options.

#### Link Multiple Benchmarks with Multiple Linkers
You can use the Makefile to link multiple benchmarks using multiple linkers with one command.

To link all benchmarks specified in the Makefile's `BENCHMARK_NAMES` variable
using all linking systems specified in the Makefile's `LINKING_SYSTEMS` variable run

    make link_benchmarks

You can examine or adjust each system's exact linking arguments in the Makefile's `link_benchmark` target if needed.

NOTE: The linking results for some systems like Neural-EL, Wikifier and Ambiverse need to be created separately
and stored at a path that can then be passed to `link_benchmark_entities.py` as linker argument.
See the READMEs in the `neural-el` or `wikifier` directories for more information.
For other systems like Spacy or Explosion you first need to train the respective linker (explained later in this README).


### Evaluate Linked Benchmark Articles

To evaluate a linking result file use the script `evaluate_linked_entities.py`:

    python3 evaluate_linked_entities.py </path/to/linking_result_file.jsonl>

This will print precision, recall and F1 scores and create two new files
`</path/to/linking_result_file.cases>` and `</path/to/linking_result_file.results>` that contain the evaluation results.
The `.cases` file contains information about each true positive, false positive and false negative case.
The `.results` file contains the scores that are shown in the web app's evaluation results table.

For example

    python3 evaluate_linked_entities.py evaluation_results/tagme/tagme.thresh02.msnbc.jsonl

will create the files `evaluation_results/tagme/tagme.thresh02.msnbc.cases`
and `evaluation_results/tagme/tagme.thresh02.msnbc.results`.

In the web app, simply reload the page and the experiment will show up as a
row in the evaluation results table of the corresponding benchmark.

#### Evaluate Multiple Linking Result Files
You can use the Makefile to evaluate multiple linking result files with one command.

To evaluate all linking result files in the `evaluation_results/*/` directories
for all benchmarks specified in the Makefile's `BENCHMARK_NAMES` variable run

    make evaluate_linked_benchmarks

## Notes

If you want to be able to run coreference with the Stanford CoreNLP coreference resolution system, make sure to setup Stanford CoreNLP by running

    ./setup_stanford_coref.sh
