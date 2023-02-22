# Configure Entity Types

For the per-type evaluation, we categorize entities into a set of Wikidata whitelist types. An entity can potentially
 have more than one whitelist type. These whitelist types are defined in `small-data-files/whitelist_types.tsv`. The
 file `<data_directory>/wikidata_mappings/qid_to_whitelist_types.db` contains a database that maps Wikidata entity
 QIDs to their whitelist type QID.
 Since the Wikidata type hierarchy contains many inconsistencies, and instance-of and subclass-of
 relations are subject to constant change, we build our type mapping from a corrected version of Wikidata. For these
 corrections, we add and remove certain instance-of and subclass-of relations. These corrections are defined in
 `small-data-files/type_corrections.txt`. We provide a download link for the entity-types mapping with our default
 whitelist types and corrections (run `make download_entity_types_mapping` as described in
 [this section of the README](../README.md#get-the-data)). You can however also build the file yourself and define
 your own set of whitelist types and type corrections. For this, execute the following steps:
1) Adjust the whitelist types and corrections in the `small-data-files/whitelist_types.tsv` and
 `small-data-files/type_corrections.txt` files
2) Copy these files to `wikidata-types/types.tsv` and `wikidata-types/corrections.txt` respectively.
3) Run the steps described in [Generate Entity-Type Mapping](data_generation.md#generate-entity-type-mapping).
 
When loading the types into Elevant for the evaluation, we apply another layer of adjustments where we merge certain
 whitelist types into others, e.g. "Fictional Character" into "Person", such that all entities from the
 `entity-types.tsv` mapping with the whitelist type "Fictional Character" are instead getting the type "Person". These
 adjustments are defined in `small-data-files/type_adjustments.txt`. We could of course also remove
 "Fictional Character" from the set of whitelist types and instead add a subclass-of relation between "Fictional
 Character" and "Person" to achieve the same entity type assignment during the evaluation. However, our goal is that
 the corrections file really only contains rules that correct possible Wikidata mistakes, whereas the adjustments
 file contains rules that might not generally be accepted as correct but serves our purposes, e.g. makes the per-type
 evaluation more intuitive and clear.
 
In order for the newly configured types to take effect, you need to execute 2 more steps:

1) Re-annotate all benchmarks you are using with
 
       python3 add_benchmark.py <benchmark_name> -b <benchmark_name>
 
    This will take the benchmark `<benchmark_name>`, re-annotate it with the new entity types (and entity labels but
    unless you have updated your `qid_to_labels.tsv` mapping, nothing changes there), and write the re-annotated
    benchmark back to the same file it was read from.

2) Re-evaluate your linking results using the Makefile by running
 
       make evaluate_linking_results
       
    This will evaluate all your linking results in `EVALUATION_RESULTS_DIR` (default is `evaluation-results/`) over the
    updated benchmarks.

    Alternatively you can manually run the evaluation script for a certain linking results file with the
    `-b <benchmark_name>` option:
 
       python3 evaluate_linking_results.py <linking_results_file> -b <benchmark_name>

    where `<benchmark_name>` is the name of the benchmark over which the linking results were generated. Note however,
    that the webapp requires all displayed evaluation results to have been run with the same entity type configuration.
    Not re-evaluating all your linking results can lead to unexpected behavior.
