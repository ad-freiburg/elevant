# WEXEA
Wikipedia EXhaustive Entity Annotator (LREC 2020)

WEXEA is an exhaustive Wikipedia entity annotation system, to create a text corpus based on Wikipedia with exhaustive annotations of entity mentions, i.e. linking all mentions of entities to their corresponding articles. 

This is a modified and dockered version of the [original code](https://github.com/mjstrobl/WEXEA).

The original repository is based on our LREC 2020 paper: 

"WEXEA: Wikipedia EXhaustive Entity Annotation"

https://www.aclweb.org/anthology/2020.lrec-1.240

WEXEA runs through several stages of article annotation and the final articles can be found in the 'final_articles' folder in the output directory.
Articles are separately stored in a folder named after the first 3 letters of the title (lowercase) and sentences are split up leading to one sentence per line.
Annotations follow the Wikipedia conventions, just the type of the annotation is added at the end.

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
        
        python3 write_articles.py --input_benchmark --output_dir <output_directory>/original_articles_benchmark/new/ --title_in_filename --print_hyperlinks --print_entity_list

## Server Visualization

Run `make run_server` to start the server (per default on port 8080).
The Webapp visualizes Wikipedia articles (not the benchmark articles) with Wikipedia links (blue), WEXEA links (red) and unknown entities (green).

## Hardware requirements

32GB of RAM are required (it may work with 16, but not tested) and it should take around 48 hours to finish with a full Wikipedia dump.

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
