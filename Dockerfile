FROM ubuntu:24.04
MAINTAINER Natalie Prange prange@cs.uni-freiburg.de
WORKDIR /home/
RUN apt-get update
RUN apt-get install -y python3 python3-pip git wget vim curl python3-gdbm bc
# Install docker so that sibling docker containers can be started within the container.
# This is only needed for the entity type generation and can be removed if `make download_all` is used.
RUN curl -sSL https://get.docker.com/ | sh > /dev/null
COPY requirements.txt requirements.txt
# --break-system-packages is used to avoid the need for a virtual environment within the docker container
RUN python3 -m pip install -r requirements.txt --break-system-packages
RUN python3 -m spacy download en_core_web_lg --break-system-packages
RUN python3 -m spacy download en_core_web_sm --break-system-packages
COPY src src
COPY scripts scripts
COPY evaluation-webapp evaluation-webapp
RUN mkdir third-party
COPY third-party/wiki-extractor third-party/wiki-extractor
COPY small-data-files small-data-files
COPY configs configs
COPY Makefile .
COPY *.py ./
# Set DATA_DIR variable in Makefile to /data within the container
RUN sed -i 's|^DATA_DIR =.*|DATA_DIR = /data|' Makefile
# Enable Makefile target autocompletion
RUN echo "complete -W \"\`grep -oE '^[a-zA-Z0-9_.-]+:([^=]|$)' ?akefile | sed 's/[^a-zA-Z0-9_.-]*$//'\`\" make" >> ~/.bashrc
# Add Elevant's src directory to the PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:src"
# Files created in the docker container should be easily accessible from the outside
CMD umask 000; /bin/bash;


# Build the container:
# docker build -t elevant .

# Run the container:
# docker run -it -p 8000:8000 -v <data_directory>:/data -v $(pwd)/evaluation-results/:/home/evaluation-results -v $(pwd)/benchmarks/:/home/benchmarks elevant
