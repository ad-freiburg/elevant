# WEXEA
Wikipedia EXhaustive Entity Annotator (LREC 2020)

WEXEA is an exhaustive Wikipedia entity annotation system, to create a text corpus based on Wikipedia with exhaustive annotations of entity mentions, i.e. linking all mentions of entities to their corresponding articles. 

This is a modified and dockered version of the [original code](https://github.com/mjstrobl/WEXEA).

The original repository is based on the LREC 2020 paper: 
[WEXEA: Wikipedia EXhaustive Entity Annotation](https://www.aclweb.org/anthology/2020.lrec-1.240)


## Run
* Build the docker container with

        docker build -t wexea .

* Run the docker container with

        docker run -it -p 8080:8080 -v <output_directory>:/results -v <directory_with_wikipedia_xml_dump>:/wikipedia-dump:ro wexea

    Results will be written to `<output_directory>`.
    On our chair's machines this should be `/nfs/students/natalie-prange/wexea_output` to use pre-generated data.
    
    You only need to mount `<directory_with_wikipedia_xml_dump>` if you want to generate all data from scratch.
    It is not needed if you have pre-generated data and just want to annotate articles or run the server.
    You might have to adjust the Wikipedia dump name in `config/config.json`.
    Per default, the system assumes the dump name is `enwiki-latest-pages-articles-multistream.xml`.

* Within the docker container run `make help` for additional information.

* To annotate benchmark entities you only need to run `make annotate_benchmark`.
    This assumes benchmark articles are stored in the expected format in a subdirectory of `<output_directory>/original_articles_benchmark/`.
    The resulting linked articles can be found in the subdirectories of `<output_directory>/final_articles_benchmark/`.

To get benchmark articles into WEXEA's expected input format and location use wiki entity linker's `write_articles.py` with the following options:
        
        python3 write_articles.py --output_dir <output_directory>/original_articles_benchmark/new/ --title_in_filename --print_hyperlinks --print_entity_list --input_benchmark <benchmark_name>

## Server Visualization

Run `make run_server` to start the server (per default on port 8080).
The Webapp visualizes Wikipedia articles (not the benchmark articles) with Wikipedia links (blue), WEXEA links (red) and unknown entities (green).

## Hardware requirements

32GB of RAM are required (it may work with 16, but not tested) and it should take around 48 hours to finish with a full Wikipedia dump.

## How does it work?
In a preprocessing step, several dictionaries are created, such as a redirects dictionary, an alias dictionary and disambiguation page dictionaries.
An article is linked in the following manner:
1) Keep hyperlinks in the article if the corresponding article entity is mostly starting with a capital letter (considering most frequent anchor text of incoming links of an article).
2) Link the bold title spans in the first paragraph of an article to the article entity.
3) After a link is seen, search through the remaining article for the name or aliases (link anchor texts starting with a capital letter that appear more than once, redirects, first and last word of the entity if it's a person, ...) of the linked entity and annotate them with the corresponding entity.
4) Search for acronyms in the article: For a string "Aaaaa Bbbbb Cccc (ABC)" if the matching string before the brackets was linked to an entity, the acronym is linked to that same entity.
5) Search for mentions by looking for words starting with a capital letter (except for frequent sentence starter words). Combine pairs of mentions occuring next to each other or, if combined, are part of the alias dictionary or have one of the following words between the pair of mentions: ("de", "of", "von", "van").
6) Such mentions are linked as follows:
	- If a mention matches an alias of the article entity and does not exactly match any other entity, link to the article entity.
	- If the mention matches the 10,000 most popular entities in Wikipedia, link to that entity
	- If the mention matches a disambiguation page and one of the previously linked entities appears in this list, link to this entity
	- If the mention matches an alias from the general alias dictionary, it is linked to the most frequently linked entity given the mention
7) Resolve conflicts (more than one potential candidate for a mention using the previous rules) in the following manner:
	- If all candidates correspond to persons, the person that was linked with the mention more often (within the article?) is linked.
	- Exact name of a previously linked entity > alias of the article entity > alias of a previously linked entity
	- Apply Gupta et al.'s Neural EL on the mention given the computed candidate set.
8) If no entity can be found for a mention, annotate it with *unknown* or with a disambiguation page if one matches.

## Citation (bibtex)

@InProceedings{strobl-trabelsi-zaiane:2020:LREC,
  author    = {Strobl, Michael  and  Trabelsi, Amine  and  Zaiane, Osmar},
  title     = {WEXEA: Wikipedia EXhaustive Entity Annotation},
  booktitle      = {Proceedings of The 12th Language Resources and Evaluation Conference},
  month          = {May},
  year           = {2020},
  address        = {Marseille, France},
  publisher      = {European Language Resources Association},
  pages     = {1951--1958},
  url       = {https://www.aclweb.org/anthology/2020.lrec-1.240}
}
