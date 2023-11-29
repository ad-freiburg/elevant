# Use a Custom Knowledge Base

This section explains the steps you need to take if you want to use ELEVANT to evaluate linking results for linkers and
 benchmarks that link to a custom knowledge base or ontology.
 
Note that some features are not available when using a custom knowledge base. E.g. some error categories like metonyms,
 demonyms (which might not even make sense for your knowledge base) and rare errors can not be evaluated separately.
 
Instead of following the instructions in [Get the Data](../README.md#get-the-data), perform the following steps
 within the docker container to setup ELEVANT for your custom KB:
 
1) Remove all subdirectories in `evaluation-results/` and all contents of the `benchmarks/` directory:
 
       rm evaluation-results/* -r
       rm benchmarks/*
  
    The evaluation results and benchmarks contained in these folders per default are targeted at Wikidata / Wikipedia
    / DBpedia.

2) Run the Python script `scripts/extract_custom_mappings.py` to extract the necessary name and type mappings from your
 KB. For this script to work, your KB must be in the turtle (ttl) format.
 
       python3 scripts/extract_custom_mappings.py <custom_kb_in_ttl_format> --name_predicate <predicate_for_entity_name> --type_predicate <predicate_for_entity_type>
   
    Per default, the predicate used to extract the entity name is `http://www.w3.org/2004/02/skos/core#prefLabel` and
     the default predicate used to extract the entity type is `http://www.w3.org/2000/01/rdf-schema#subClassOf`.
    
    This will create three tsv files in `<data_directory>/custom_mappings/`:
    - `entity_to_name.tsv` where the first column contains the entity URI and the second column contains the entity
     name, e.g.
     
          http://emmo.info/emmo/domain/fatigue#EMMO_c502dbc5-3a11-50c7-baf5-f3ef9c4fe636	Glass Transition Temperature
    - `entity_to_types.tsv` where the first column contains the entity URI and all further columns contain URIs
     of types of this entity, e.g.
     
          http://emmo.info/emmo/domain/fatigue#EMMO_6e8610b1-1717-53ff-a2ac-3d48950773fc	http://emmo.info/emmo/domain/fatigue#EMMO_15a16e99-19cb-5d5e-84d0-b74029837f28  http://emmo.info/emmo/domain/fatigue#EMMO_cfe4071d-224e-5ae9-abe5-083dc57ee6f9

    - `whitelist_types.tsv` where the first column contains the URI of an entity type and the second column contains
     the name for the entity type, e.g.
      
          http://emmo.info/emmo/domain/fatigue#EMMO_15a16e99-19cb-5d5e-84d0-b74029837f28 Mechanical Property
          
         In the web app you will then be able to see evaluation results for each of these whitelist types individually.
         You can manually filter the set of whitelist types (this is especially important if you have a lot of entity
         types, e.g. > 50, because then your web app will become cluttered), but then make sure to only include types in
         the `entity_to_types.tsv` file that are included in this whitelist.
    
    If you don't have your knowledge base in ttl format or can't use the script for other reasons, it is enough to
     create the three tsv files mentioned above yourself and move them to a directory
     `<data_directory>/custom_mappings/`.
     
3) To add a benchmark that links mentions to your custom knowledge base, run the `add_benchmark.py` script with the
 option `-c` (for **c**ustom KB). The supported benchmark formats for custom KB benchmarks are `nif` and `simple-jsonl`. E.g.
 
        python3 add_benchmark.py <benchmark_name> -bfile <benchmark_file> -bformat <nif|simple-jsonl> -c
 
    See [Add A Benchmark](add_benchmark.md) for more detailed information on adding a benchmark and the benchmark
     formats.

4) To add linking results for such a benchmark to ELEVANT, run the `python3 link_benchmark_entities.py` script with the
 option `-c`. The supported linking results formats for custom KB linking results are `nif` and `simple-jsonl`. E.g.
 
       python3 link_benchmark_entities.py <experiment_name> -pfile <linking_results_file> -pformat <nif|simple-jsonl> -b <benchmark_name> -c

    See [Link Benchmark Articles](link_benchmark_articles.md) for more detailed information on adding linking results
     to ELEVANT and the linking results formats.

5) To evaluate the linking results, run the `evaluate_linking_results.py` script with the option `-c`, e.g.

       python3 evaluate_linking_results.py <linking_result_file> -c
   where `<linking_result_file>` is the file generated in the previous step. See 
   [Evaluate Linking Results](evaluate_linking_results.md) for more detailed information.

6) Before you start the web app for the first time, in the `evaluation-webapp` directory run

       ln -s <data-directory>/custom_mappings/whitelist_types.tsv whitelist_types.tsv

7) You can then start the web app and inspect your linking results at <http://0.0.0.0:8000/> with

       make start_webapp