# ELEVANT: Entity Linking Evaluation & Analysis Tool

ELEVANT is a tool that helps you evaluate, analyse and compare entity linking systems in detail. You can explore a
 demo instance of the ELEVANT web app at https://elevant.cs.uni-freiburg.de/. If you are using ELEVANT for your
 research please cite our paper
 ["ELEVANT: A Fully Automatic Fine-Grained Entity Linking Evaluation and Analysis Tool"](https://aclanthology.org/2022.emnlp-demos.8.pdf).

For the ELEVANT instance of the EMNLP 2023 paper
["A Fair and In-Depth Evaluation of Existing End-to-End Entity Linking Systems"](https://arxiv.org/abs/2305.14937)
 see https://elevant.cs.uni-freiburg.de/emnlp2023.

## Docker Instructions
Get the code, and build and start the docker container:

    git clone https://github.com/ad-freiburg/elevant.git .
    docker build -t elevant .
    docker run -it -p 8000:8000 -v <data_directory>:/data -v $(pwd)/evaluation-results/:/home/evaluation-results -v $(pwd)/benchmarks/:/home/benchmarks elevant

where `<data_directory>` is the directory in which the required data files will be stored. What these data files are
 and how they are generated is explained in section [Get the Data](#get-the-data). Make sure you can read from and
 write to all directories that are being mounted as volumes from within the docker container (i.e. your
 `<data_directory>`, `evaluation-results` and `benchmarks`), for example (if security is not an issue) by giving all
 users read and write permissions to the directories in question with:

    chmod a+rw -R <data_directory> evaluation-results/ benchmarks/


Unless otherwise noted, all the following commands should be run inside the docker container. If you want to use the
 system without docker, follow the instructions in [Setup without Docker](docs/setup_without_docker.md) before
 continuing with the next section.

## Get the Data

(Note: If you want to use a custom knowledge base instead of Wikidata/Wikipedia/DBpedia you can skip this
 step and instead follow the instructions in [Use a Custom Knowledge Base](docs/use_custom_knowledge_base.md).)

For linking entities in text or evaluating the output of a linker, our system needs information about entities and
 mention texts, e.g. entity names, aliases, popularity scores, types, the frequency with which a mention is linked
 to a certain article in Wikipedia, etc. This information is stored in and read from several files. Since these files
 are too large to upload them on GitHub, you can either download them from our servers (fast) or build them yourself
 (slow, RAM intensive, but the resulting files might be based on a more recent Wikidata/Wikipedia dump).

To download the files, simply run

    make download_all

This will automatically run `make download_wikidata_mappings`, `make download_wikipedia_mappings` and
 `make download_entity_types_mapping` which will download the compressed files, extract them and move them to the
 correct location. See [Mapping Files](docs/mapping_files.md) for a description of files downloaded in this steps.

NOTE: This will overwrite existing Wikidata and Wikipedia mappings in your `<data_directory>` so make sure this is what 
 you want to do.

If you rather want to build the mappings yourself, you can replace each *download* command (except `download_all`) by a
 *generate* command. See
 [Data Generation](docs/data_generation.md) for more details.

## Start the Web App

To start the evaluation web app, run

    make start_webapp

You can then access the webapp at <http://0.0.0.0:8000/>.

The evaluation results table contains one row for each experiment. In ELEVANT, an experiment is a run of a
 particular entity linker with particular linker settings on a particular benchmark. We already added a few experiments,
 including oracle predictions (perfect linking results generated from the ground truth), so you can start exploring
 the web app right away. The section [Add a Benchmark](#add-a-benchmark) explains how you can add more benchmarks
 and the section [Add an Experiment](#add-an-experiment) explains how you can add more experiments yourself.

See [Evaluation Web App](docs/evaluation_webapp.md) for a detailed overview of the web app's features.

## Add a Benchmark

You can easily add a benchmark if you have a benchmark file that is in the
 [JSONL format we use](docs/our_jsonl_format.md), in the common NLP Interchange Format (NIF), in the IOB-based format
 used by Hoffart et al. for their AIDA/CoNLL benchmark or in a very simple JSONL format. Benchmarks in other formats
 have to be converted into one of these formats first.

To add a benchmark, simply run

    python3 add_benchmark.py <benchmark_name> -bfile <benchmark_file> -bformat <ours|nif|aida-conll|simple-jsonl>

This converts the `<benchmark_file>` into our JSONL format (if it is not in this format already), annotates ground
 truth labels with their Wikidata label and Wikidata types and writes the result to the file
 `benchmarks/<benchmark_name>.benchmark.jsonl`.

The benchmark can now be linked with a linker of your choice using the `link_benchmark_entities.py` script with the
 parameter `-b <benchmark_name>`. See section [Add an Experiment](#add-an-experiment) for details on how to link a
 benchmark and the supported formats.

See [Add A Benchmark](docs/add_benchmark.md) for more details on adding a benchmark including a description of the
 supported file formats.

Many popular entity linking benchmarks are already included in ELEVANT and can be used with ELEVANT's scripts out of the
 box. See [Benchmarks](docs/benchmarks.md) for a list of these benchmarks.

## Add an Experiment

You can add an experiment, i.e. a row in the table for a particular benchmark, in two steps: 1) link the benchmark
 articles and 2) evaluate the linking results. Both steps are explained in the following two sections.

### Link Benchmark Articles
To link the articles of a benchmark with a single linker configuration, use the script `link_benchmark_entities.py`:

    python3 link_benchmark_entities.py <experiment_name> -l <linker_name> -b <benchmark_name>

The linking results will be written to
 `evaluation-results/<linker_name>/<adjusted_experiment_name>.<benchmark_name>.linked_articles.jsonl` where
 `<adjusted_experiment_name>` is `<experiment_name>` in lowercase and characters other than `[a-z0-9-]` replaced by
 `_`.
For example

    python3 link_benchmark_entities.py Baseline -l baseline -b kore50

will create the file `evaluation-results/baseline/baseline.kore50.linked_articles.jsonl`. The result file contains
 one article as JSON object per line. Each JSON object contains benchmark article information such as the article
 title, text, and ground truth labels, as well as the entity mentions produced by the specified linker.
 `<experiment_name>` is the name that will be displayed in the first column of the evaluation results table in the
 web app.

See [Link Benchmark Articles](docs/link_benchmark_articles.md) for information on how you can transform your existing
 linking result files into our format, and instructions for how to link multiple benchmarks using multiple linkers
 with a single command.

See [Included Linkers](docs/included_linkers.md) for a list of linkers that can be used out of the box with ELEVANT.
 These are for example *ReFinED*, OpenAI's *GPT* (you'll need an OpenAI API key for that), *REL*, *TagMe* (you'll
 need an access token for that which can be obtained easily and free of cost) and *DBpediaSpotlight*.

### Evaluate Linking Results

To evaluate a linker's predictions use the script `evaluate_linking_results.py`:

    python3 evaluate_linking_results.py <path_to_linking_result_file>

This will print precision, recall and F1 scores and create two new files where the `.linked_articles.jsonl` file
 extension is replaced by `.eval_cases.jsonl` and `.eval_results.json` respectively. For example

    python3 evaluate_linking_results.py evaluation-results/baseline/baseline.kore50.linked_articles.jsonl

will create the files `evaluation-results/baseline/baseline.kore50.eval_cases.jsonl` and
`evaluation-results/baseline/baseline.kore50.eval_results.json`. The `eval_cases` file contains information about
 each true positive, false positive and false negative case. The `eval_results` file contains the scores that are shown
 in the web app's evaluation results table.

In the web app, simply reload the page (you might have to disable caching) and the experiment will show up as a row in
 the evaluation results table for the corresponding benchmark.

See [Evaluate Linking Results](docs/evaluate_linking_results.md) for instructions on how to evaluate multiple linking
 results with a single command.


## Remove an Experiment
If you want to remove an experiment from the web app, simply (re)move the corresponding `.linked_articles.jsonl`,
 `.eval_cases.jsonl` and `.eval_results.json` files from the `evaluation-results/<linker_name>/` directory and reload
 the web app (again disabling caching).
