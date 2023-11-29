# Evaluate Linked Benchmark Articles

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

## Evaluate Multiple Linking Result Files

You can evaluate multiple linking result files at the same time using the evaluation script. E.g.

    python3 evaluate_linking_results.py evaluation-results/*/*.linked_articles.jsonl

will evaluate all linking results files in the `evaluation-results` subdirectories. This saves a lot of time in
 comparison to calling `evaluate_linking_results.py` multiple times, since most of the time (ca. 7 mins) is needed to
 load entity information which only has to be done once per call, while the evaluation itself only takes a few seconds.

Alternatively, you can use the Makefile to evaluate multiple linking result files with one command. The Makefile
 gives you more control over which result files are being evaluated. Running

    make evaluate_linking_results

will evaluate all linking result files in the `evaluation-results/*/` directories for all benchmarks specified in the
 Makefile's `BENCHMARK_NAMES` variable.
