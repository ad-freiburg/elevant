FROM ubuntu:20.04
MAINTAINER Natalie Prange prange@cs.uni-freiburg.de
WORKDIR /home/
RUN apt-get update
RUN apt-get install -y python3 python3-pip git wget vim curl python3-gdbm bc
# Install docker so that sibling docker containers can be started within the container.
# This is only needed for the entity type generation and can be removed if `make download_all` is used.
RUN curl -sSL https://get.docker.com/ | sh > /dev/null
COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt
RUN python3 -m spacy download en_core_web_lg
RUN python3 -m spacy download en_core_web_sm
COPY src src
COPY scripts scripts
COPY evaluation-webapp evaluation-webapp
RUN mkdir third-party
COPY third-party/wiki_extractor third-party/wiki_extractor
COPY small-data-files small-data-files
COPY configs configs
COPY Makefile .
COPY *.py ./
COPY evaluation-results-emnlp2023 evaluation-results-emnlp2023
COPY evaluation-results-arxiv2023 evaluation-results-arxiv2023
COPY evaluation-results-diss evaluation-results-diss
COPY evaluation-results-diss-wiki evaluation-results-diss-wiki
COPY benchmarks-emnlp2023 benchmarks-emnlp2023
COPY benchmarks-arxiv2023 benchmarks-arxiv2023
COPY benchmarks-diss benchmarks-diss
COPY benchmarks-diss-wiki benchmarks-diss-wiki
# Set DATA_DIR variable in Makefile to /data/ within the container
RUN sed -i 's|^DATA_DIR =.*|DATA_DIR = /data/|' Makefile
# Enable Makefile target autocompletion
RUN echo "complete -W \"\`grep -oE '^[a-zA-Z0-9_.-]+:([^=]|$)' ?akefile | sed 's/[^a-zA-Z0-9_.-]*$//'\`\" make" >> ~/.bashrc
# Add Elevant's src directory to the PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:src"
# Files created in the docker container should be easily accessible from the outside
CMD umask 000; make start_webapp;


# Build the container:
# docker build -t elevant-stable .

# Run the container:
# docker run -it -p 8003:8000 -d --restart always -v /local/data-ssd/entity-linking/:/data -v $(pwd)/evaluation-results/:/home/evaluation-results -v $(pwd)/benchmarks/:/home/benchmarks elevant-stable
