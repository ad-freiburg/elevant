FROM pytorch/pytorch:1.6.0-cuda10.1-cudnn7-runtime
MAINTAINER Matthias Hertel hertelm@login.informatik.uni-freiburg.de
WORKDIR /home/
RUN apt-get update
RUN apt-get install -y python3 python3-pip git wget vim curl
RUN git clone https://github.com/huggingface/neuralcoref.git
RUN python3 -m pip install -r neuralcoref/requirements.txt
RUN python3 -m pip install -e neuralcoref
COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt
RUN python3 -m spacy download en_core_web_lg
RUN python3 -m spacy download en_core_web_sm
COPY src src
COPY benchmark-webapp benchmark-webapp
COPY evaluation-webapp evaluation-webapp
RUN mkdir third-party
COPY third-party/wiki_extractor third-party/wiki_extractor
COPY wikidata-types wikidata-types
COPY data data
COPY Makefile .
COPY *.py ./
COPY *.sh ./
# Set DATA_DIR variable in Makefile to /data/ within the container
RUN sed -i 's|^DATA_DIR =.*|DATA_DIR = /data/|' Makefile
# Enable Makefile target autocompletion
RUN echo "complete -W \"\`grep -oE '^[a-zA-Z0-9_.-]+:([^=]|$)' ?akefile | sed 's/[^a-zA-Z0-9_.-]*$//'\`\" make" >> ~/.bashrc
# Files created in the docker container should be easily accessible from the outside
CMD umask 000; /bin/bash;


# Build the container:
# docker build -t elevant .

# Run the container:
# docker run -it -p 8000:8000 -v <data_directory>:/data -v $(pwd)/evaluation-results/:/home/evaluation-results -v $(pwd)/benchmarks/:/home/benchmarks elevant
