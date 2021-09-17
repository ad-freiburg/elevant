FROM ubuntu:18.04
LABEL maintainer="prange@informatik.uni-freiburg.de"

RUN apt-get update && apt-get install -y vim make
# Install OpenJDK-8
# See https://stackoverflow.com/questions/31196567/installing-java-in-docker-image
RUN apt-get update && \
    apt-get install -y openjdk-8-jdk && \
    apt-get install -y ant && \
    apt-get clean;

# Fix certificate issues
RUN apt-get update && \
    apt-get install ca-certificates-java && \
    apt-get clean && \
    update-ca-certificates -f;

# Setup JAVA_HOME -- useful for docker commandline
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64/
RUN export JAVA_HOME

# Don't copy the data folder because it's huge (11GB). Mount it instead.
COPY ./ /home/

ENTRYPOINT /bin/bash
WORKDIR /home/

# docker build -t wikifier .
# docker run -it -v <data_directory>:/home/data -v <articles_directory>:/home/benchmark_articles/ <output_directory>:/home/linked_benchmark_articles/ wikifier
# E.g.
# docker run -it -v /local/data/prangen/src/wiki_entity_linker/wikifier/Wikifier2013/data/:/home/data -v /nfs/students/natalie-prange/wikifier_data/input/:/home/input_articles/ -v /nfs/students/natalie-prange/wikifier_data/output/:/home/output_articles/ wikifier