# Evaluate Linked Benchmark Articles
To evaluate a linker's predictions use the script `evaluate_linking_results.py`:

    python3 evaluate_linking_results.py <path_to_linking_result_file>

This will print precision, recall and F1 scores and create two new files where the `.jsonl` file extension is
 replaced by `.cases` and `.results` respectively. For example

    python3 evaluate_linking_results.py evaluation-results/tagme/tagme.thresh02.kore50.jsonl

will create the files `evaluation-results/tagme/tagme.thresh02.kore50.cases` and
`evaluation-results/tagme/tagme.thresh02.kore50.results`. The `.cases` file contains information about each true
 positive, false positive and false negative case. The `.results` file contains the scores that are shown in the web
 app's evaluation results table.

## Evaluate Multiple Linking Result Files
You can use the Makefile to evaluate multiple linking result files with one command.

To evaluate all linking result files in the `evaluation-results/*/` directories for all benchmarks specified in the
 Makefile's `BENCHMARK_NAMES` variable run

    make evaluate_linking_results
