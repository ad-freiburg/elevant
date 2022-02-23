# Wikifier

This lets you download and run a dockered version of the Wikifier code from the EMNLP 2013 paper *Relational Inference for Wikification* by Cheng and Roth.

## Setup

To download the code and data and setup the necessary files, simply run
    
    ./setup.sh
    
## Run

* `cd` into the Wikifier2013 directory and build the docker container with

      cd Wikifier2013
      docker build -t wikifier .

* Run the docker container with

      docker run -it -v <data_directory>:/home/data -v <articles_directory>:/home/input_articles/ -v <output_directory>:/home/output_articles/ wikifier
  
  where `<data_directory>` is the path to the `Wikifier2013/data/` folder (which is included in the `.dockerignore` file to keep the docker image small)
  `<articles_directory>` is the path to a folder that contains one folder per benchmark with article txt files
  and `<output_directory>` is the path to a folder to which the output will be written to.
  
* Within the docker container run `make help` for additional information.

* To link benchmark entities you only need to run `make link_benchmarks`.
    This assumes benchmark articles are stored in the expected format in subdirectories of `<articles_directory>`.
    The resulting linked articles are written to the subdirectories of `<output_directory>`.
    
    To write benchmark articles into the proper location in Wikifier format use wiki entity linker's `write_articles.py` with the following options:
            
      python3 write_articles.py --output_dir <articles_directory>/<benchmark_name>/ --ascii --input_benchmark <benchmark_name>


## Observed Problems:
* Wikifier can't seem to handle non-ASCII characters properly.
    If an input article contains non-ASCII characters, they are replaced in the Wikifier output by the corresponding number of replacement symbols.
    This messes up the start and end indices of the reported mention spans.
    We therefore preprocess benchmarks in such a way, that non-ASCII characters are replaced by `_`.
    This is automatically done when running the `write_articles.py` script with the options specified above.
    This also ensures that words are not tokenized at the replacement symbol which would be the case if e.g. the standard `?` was used as replacement symbol.

* A similar problem applies to the links predicted by Wikifier.
    If a predicted Wikipedia title contains non-ASCII characters, they are replaced in the Wikifier output by a replacement symbol.
    This prevents a mapping of the reported Wikipedia title to a Wikipedia url or a Wikidata ID using our mappings.
    The Wikifier output additionally contains Wikipedia page IDs.
    However, these often contain errors (for some unknown reason, many predicted links have the wrong Wikipedia ID 3658264 which corresponds to the Wikipedia page *Williams Lake Water Aerodrome*) or point to an (now) empty page.
    For now, we deal with this in the following manner:
    If the reported Wikipedia title contains a replacement symbol `?`, we retrieve the Wikipedia title that corresponds to the reported Wikipedia page ID.
    If this ID is 3658264 or no Wikipedia page exists for this ID in our mapping, we use the reported Wikipedia title, otherwise we use the Wikipedia title retrieved using the Wikipedia page ID.

* The Wikifier output is not deterministic.
    Multiple runs over the same input can result in different outputs.
