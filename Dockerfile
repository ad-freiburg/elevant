FROM pytorch/pytorch:1.6.0-cuda10.1-cudnn7-runtime
MAINTAINER Matthias Hertel hertelm@login.informatik.uni-freiburg.de
WORKDIR /
RUN apt-get update
RUN apt-get install -y python3 python3-pip git
RUN git clone https://github.com/huggingface/neuralcoref.git
RUN python3 -m pip install -r neuralcoref/requirements.txt
RUN python3 -m pip install -e neuralcoref
COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt
RUN python3 -m spacy download en_core_web_lg
RUN python3 -m spacy download en_core_web_sm
COPY src src
COPY Makefile .
COPY *.py ./
COPY *.sh ./


# Build the container:
# docker build -t wiki-entity-linker .

# Run the container on my machine:
# docker run -it -v /home/hertel/wikipedia/wikipedia_2020-06-08:/data wiki-entity-linker

# Run the container at the lab:
# docker run -it -v /nfs/students/matthias-hertel/wiki_entity_linker:/data wiki-entity-linker
