# Evaluate Linked Benchmark Articles

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