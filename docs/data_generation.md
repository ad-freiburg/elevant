# Data Generation

If you want to generate the data files which ELEVANT needs, instead of downloading them, follow the instructions below.

If, for some reason, you don't want to run the data generation within the docker container, make sure to set the
 `DATA_DIR` variable in the Makefile to your `<data_directory>`. In the docker container, `DATA_DIR` is automatically
 set to `/data/`, so you don't have to do anything.

NOTE: The following steps will overwrite existing Wikidata and Wikipedia mappings in your `<data_directory>` so make
 sure this is what you want to do.

Data generation has to be done only once unless you want to update the generated data files to a more recent Wikidata
 or Wikipedia version.


## Generate Wikidata Mappings

To generate the Wikidata mappings run

    make generate_wikidata_mappings
    
This will use the Wikidata SPARQL endpoint defined in the Makefile variable `WIKIDATA_SPARQL_ENDPOINT` and download
 the Wikidata mappings. It will then generate Python dbm databases from the Wikidata mappings for fast
 loading and reduced RAM usage. The database generation will take several hours. Finally, it will create two additional
 files from the downloaded Wikidata mappings which are only needed if you want to use coreference resolution in
 addition to entity linking.

See [Wikidata Mappings](mapping_files.md#wikidata-mappings) for a description of files generated in this step.

## Generate Wikipedia Mappings

To generate the Wikipedia mappings run

    make generate_wikipedia_mappings

This will download and extract the most recent Wikipedia dump, split it into training, development and test files and
 generate the Wikipedia mappings. NOTE: This step needs the Wikidata mappings, so make sure you build or download them
 before.

See [Wikipedia Mappings](mapping_files.md#wikipedia-mappings) for a description of files generated in this step.


## Generate Entity-Type Mapping

To generate the entity-type mapping, do the following **outside the docker container**: First make sure the `DATA_DIR`
 variable in your `Makefile` points to your `<data_directory>`. Then run

    make generate_entity_types_mapping

This will run the steps described in detail in `wikidata-types/README.md`. Roughly, it clones the QLever code from
 Github and builds the QLever docker image if no such image exists on the machine already. It then builds a QLever
 index with corrections from `wikidata-types/corrections.txt` and issues a query for all Wikidata entities and all
 their types from a given whitelist of types (`wikidata-types/types.txt`). The resulting file is moved to
 `<data_directory>/wikidata-mappings/entity-types.tsv` . The file is then transformed to a Python dbm database
 `<data_directory>/wikidata-mappings/qid_to_whitelist_types.db` which can take several hours (Note: if the
 tranformation to a dbm database yields errors when running it outside the docker container due to missing
 dependencies, you can also run this particular step inside the docker container).

Building the entity-types mapping requires about 25 GB of RAM and 100 GB of disk space and assumes that there is a
 running QLever instance for Wikidata under the URL specified by the variable `API_WIKIDATA` in
 `wikidata-types/Makefile` (by default, this is set to https://qlever.cs.uni-freiburg.de/api/wikidata).

See [Entity-Type Mapping](mapping_files.md#entity-type-mapping) for a description of the file generated in this
 step.

## Cleanup

You can free up some disk space after running the steps mentioned above by running

    make cleanup

This will remove the `entity-types.tsv` as well as those Wikidata mappings, that have been transformed to database
 files.
