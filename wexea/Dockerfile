FROM ubuntu:18.04
LABEL maintainer="prange@informatik.uni-freiburg.de"

ENV PYTHONIOENCODING=UTF-8

RUN apt-get update && apt-get install -y python3-pip vim
RUN python3 -m pip install --upgrade pip

# Install python packages
COPY ./ /home/
RUN pip3 install -r /home/requirements.txt
RUN python3 -W ignore -m nltk.downloader stopwords
RUN python3 -W ignore -m nltk.downloader punkt

ENTRYPOINT /bin/bash
WORKDIR /home/

# docker build -t wexea .
# docker run -it -p 8080:8080 -v /nfs/students/natalie-prange/wexea_output:/results -v <directory_with_wikipedia_xml_dump>:/wikipedia-dump:ro wexea

# Note: the wikipedia_dumps mount path can be omitted if the preprocessing has already been done.