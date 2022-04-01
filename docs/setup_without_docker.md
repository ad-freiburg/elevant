# Setup without Docker

To run our system without using docker, follow the *RUN* commands in the [Dockerfile](../Dockerfile) up until

    RUN python3 -m spacy download en_core_web_sm

and set the `DATA_DIR` variable in the Makefile to the directory in which you want to store the ELEVANT data files.

In `src/settings.py` add your data directory to the `_DATA_DIRECTORIES` list.

