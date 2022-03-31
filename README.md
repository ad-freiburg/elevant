# Entity Linking Evaluation & Analysis Tool

## Docker Instructions
Get the code, and build and start the container:

    git clone git@github.com:ad-freiburg/elevant.git .
    docker build -t elevant .
    docker run -it -v <data_directory>:/data elevant

where `<data_directory>` is the directory in which the required data files will be stored.
What these data files are and how they are generated is explained in the [Get the Data](#get-the-data) section.

Unless otherwise noted, all the following commands should be run inside the docker container.

## Get the Data
For linking entities in a text or evaluating the output of a linker, our system needs information about entities and mention texts,
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

## Usage

### Link Benchmark Articles
If you want to link a single benchmark with a single specified linker configuration, use the script `link_benchmark_entities.py`:

    python3 link_benchmark_entities.py <experiment_name> <linker_type> <linker_info> -b <benchmark_name>

For example

    python3 link_benchmark_entities.py pos_prior.whitelist_types pos_prior data/whitelist_types.txt -b msnbc

Here is an example call for when you have linking results for a benchmark in NIF format

    python3 link_benchmark_entities.py <experiment_name> nif <path_to_nif_linking_results_file> -b <benchmark_name>

The linking results will be written to `evaluation_results/<linker_type>/<experiment_name>.<benchmark_name>.jsonl`
with one article as a json object per line.
Use the `-h` option for more information on the available command line arguments.

You can use the Makefile to link several benchmarks using several linkers with one command.
If you're using docker and want to persistently store the benchmark linking results created using a Makefile command,
make sure to set the `EVALUATION_RESULTS_DIR` variable in the Makefile to a mounted directory, e.g. `/data/evaluation_results/`.

To link all benchmarks specified in the Makefile's `BENCHMARK_NAMES` variable
using all linking systems specified in the Makefile's `LINKING_SYSTEMS` variable run

    make link_benchmarks

The linking results are written to subdirectories in the directory specified in the Makefile's `EVALUATION_RESULTS_DIR` variable.
You can examine or adjust each system's exact linking arguments in the Makefile's `link_benchmark` target if needed.

NOTE: The linking results for some systems like Neural-EL, Wikifier and Ambiverse need to be created separately
and stored at a path that can then be passed to `link_benchmark_entities.py` as linker argument.
See the READMEs in the `neural-el` or `wikifier` directories for more information.
For other systems like Spacy or Explosion you first need to train the respective linker (explained later in this README).


### Evaluate Linked Benchmark Articles

If you want to evaluate a single linking result file use the script `evaluate_linked_entities.py`:

    python3 evaluate_linked_entities.py <path_to_linking_result_file>.jsonl

This will print precision, recall and F1 scores and create two new files
`<path_to_linking_result_file>.cases` and `<path_to_linking_result_file>.results` that contain the evaluation results.
To show the evaluation results in the webapp, follow the instructions in `evaluation-webapp`.

If you want to evaluate several linking result files at once, i.e. all linking results in the subdirectories of the
directory `EVALUATION_RESULTS_DIR` for benchmarks specified in the Makefile's `BENCHMARK_NAMES` variable run

    make evaluate_linked_benchmarks


### Start the Evaluation Webapp

1. Go to the `evaluation-webapp` directory

        cd evaluation-webapp

2. Link to the results directory `evaluation-results`

        ln -s ../evaluation-results

3. Link to the benchmark directory that contains various benchmarks in jsonl format

        ln -s ../benchmarks

4. Start a file server

        python3 -m http.server <port>

5. Access the webapp at `0.0.0.0:<port>` (default port is 8000).

### Add a benchmark

You can easily add a benchmark that is in the jsonl format we use, in the common NIF (NLP Interchange Format) format
or in the IOB-based format used by Hoffart et al. for their AIDA/CoNLL benchmark.
Benchmarks in other formats first have to be converted into one of these formats.

To add a benchmark, simply run

    python3 create_benchmark_labels.py -name <benchmark_name> -bfile <benchmark_file> -bformat <nif|ours|aida-conll>

This will create a benchmark file `benchmarks/benchmark_labels_<benchmark_name>.jsonl` in our jsonl format where
groundtruth labels are annotated with their Wikidata label and types.

The benchmark can now be linked with a linker of your choice using the `link_benchmark_entities.py` script with the parameter `-b <benchmark_name>`

    python3 link_benchmark_entities.py <experiment_name> <linker_type> <linker_info> -b <benchmark_name>

Additionally, the benchmark can now be selected in the benchmarks dropdown menu of the web app.

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
