# Wikifier

This lets you download and run a dockered version of the Wikifier code from the EMNLP 2013 paper *Relational Inference for Wikification* by Cheng and Roth.

## Setup

To download the code and date and setup the necessary files, simply run
    
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
