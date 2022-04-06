# ELEVANT: Entity Linking Evaluation & Analysis Tool

ELEVANT is a tool that helps you evaluate, analyse and compare entity linking systems in detail. You can explore a
 demo instance of the ELEVANT web app [here](https://elevant.cs.uni-freiburg.de/).

## Docker Instructions
Get the code, and build and start the docker container:

    git clone https://github.com/ad-freiburg/elevant.git .
    docker build -t elevant .
    docker run -it -p 8000:8000 -v <data_directory>:/data -v $(pwd)/evaluation-results/:/home/evaluation-results -v $(pwd)/benchmarks/:/home/benchmarks elevant

where `<data_directory>` is the directory in which the required data files will be stored. What these data files are
 and how they are generated is explained in section [Get the Data](#get-the-data). Make sure you can read from and
 write to all directories that are being mounted as volumes from within the docker container (i.e. your
 `<data_directory>`, `evaluation-results` and `benchmarks`).

Unless otherwise noted, all the following commands should be run inside the docker container. If you want to use the
 system without docker, follow the instructions in [Setup without Docker](docs/setup_without_docker.md) before
 continuing with the next section.

## Get the Data
For linking entities in text or evaluating the output of a linker, our system needs information about entities and
 mention texts, e.g. entity names, aliases, popularity scores, types, the frequency with which a mention is linked
 to a certain article in Wikipedia, etc. This information is stored in and read from several files. Since these files
 are too large to upload them on GitHub, you can either download them from our servers (fast) or build them yourself
 (slow, RAM intensive, but the resulting files might be based on a more recent Wikidata/Wikipedia dump).

To download the files, run the following three commands:

    make download_wikidata_mappings
    make download_wikipedia_mappings
    make download_entity_types_mapping

This will download the compressed files, extract them and move them to the correct location. See
 [Mapping Files](docs/mapping_files.md) for a description of files generated in these steps.

NOTE: This will overwrite existing Wikidata and Wikipedia mappings in your `<data_directory>` so make sure this is what 
 you want to do.

If you rather want to build the mappings yourself, you can replace each *download* command by a *generate* command. See
 [Data Generation](docs/data_generation.md) for more details.

## Start the Web App

To start the evaluation web app, run

    make start_webapp

You can then access the webapp at <http://0.0.0.0:8000/>.

In the benchmark dropdown menu, you can select any benchmark for which a benchmark file in the correct format exists at
 `benchmarks/<benchmark_name>.benchmark.jsonl`. See [Included Benchmarks](docs/included_benchmarks.md) for
 details on benchmarks that are already included in ELEVANT. The section [Add a Benchmark](#add-a-benchmark) explains
 how you can add more benchmarks yourself.

A benchmark's evaluation results table contains one row for each experiment, that is, one row for each `.jsonl` file
 in a `evaluation-results/*/` directory with a corresponding `.cases` and `.results` file. We already added a few
 experiments, including oracle predictions for each benchmark (perfect linking results generated from the ground
 truth), so you can start exploring the web app right away. The section [Add an Experiment](#add-an-experiment)
 explains how you can add more experiments yourself.

See [Evaluation Web App](docs/evaluation_webapp.md) for a detailed overview of the web app's features.

## Add a Benchmark

You can easily add a benchmark if you have a benchmark file that is in the
 [JSONL format we use](docs/our_jsonl_format.md), in the common NLP Interchange Format (NIF) or in the IOB-based
 format used by Hoffart et al. for their AIDA/CoNLL benchmark. Benchmarks in other formats have to be converted into
 one of these formats first.

To add a benchmark, simply run

    python3 annotate_and_add_benchmark.py -name <benchmark_name> -bfile <benchmark_file> -bformat <nif|ours|aida-conll>

This converts the `<benchmark_file>` into our JSONL format (if it is not in this format already), annotates ground
 truth labels with their Wikidata label and Wikidata types and writes the result to the file
 `benchmarks/<benchmark_name>.benchmark.jsonl`.

In the web app, reload the page and the benchmark will show up in the benchmark dropdown menu.

The benchmark can now be linked with a linker of your choice using the `link_benchmark_entities.py` script with the
 parameter `-b <benchmark_name>`. See section [Add an Experiment](#add-an-experiment) for details on how to link a
 benchmark.

See [Add A Benchmark](docs/add_benchmark.md) for more details on adding a benchmark including a description of the
 supported file formats.
 
## Add an Experiment

You can add an experiment, i.e. a row in the table for a particular benchmark, in two steps: 1) link the benchmark
 articles and 2) evaluate the linking results. Both steps are explained in the following two sections.

### Link Benchmark Articles
To link the articles of a benchmark with a single linker configuration, use the script `link_benchmark_entities.py`:

    python3 link_benchmark_entities.py <experiment_name> <linker_type> <linker_info> -b <benchmark_name>

The linking results will be written to `evaluation-results/<linker_type>/<experiment_name>.<benchmark_name>.jsonl`.
For example

    python3 link_benchmark_entities.py tagme.thresh02 tagme 0.2 -b kore50

will create the file `evaluation-results/tagme/tagme.thresh02.kore50.jsonl`. The result file contains one article as
 JSON object per line. Each JSON object contains benchmark article information such as the article title, text, and
 ground truth labels, as well as the entity mentions produced by the specified linker. `<experiment_name>` is the
 name that will be displayed in the first column of the evaluation results table in the web app.

See [Link Benchmark Articles](docs/link_benchmark_articles.md) for information on how you can transform your existing
 linking result files into our format, and instructions for how to link multiple benchmarks using multiple linkers
 with a single command.

### Evaluate Linked Benchmark Articles

To evaluate a linking result file use the script `evaluate_linked_entities.py`:

    python3 evaluate_linked_entities.py <path_to_linking_result_file>

This will print precision, recall and F1 scores and create two new files where the `.jsonl` file extension is
 replaced by `.cases` and `.results` respectively. For example

    python3 evaluate_linked_entities.py evaluation-results/tagme/tagme.thresh02.kore50.jsonl

will create the files `evaluation-results/tagme/tagme.thresh02.kore50.cases` and
`evaluation-results/tagme/tagme.thresh02.kore50.results`. The `.cases` file contains information about each true
 positive, false positive and false negative case. The `.results` file contains the scores that are shown in the web
 app's evaluation results table.

In the web app, simply reload the page and the experiment will show up as a row in the evaluation results table of
 the corresponding benchmark.

See [Evaluate Linked Benchmark Articles](docs/evaluate_linked_benchmark_articles.md) for instructions on how to
 evaluate multiple linking results with a single command.
