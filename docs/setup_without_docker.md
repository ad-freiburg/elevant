# Setup without Docker

To run our system without using docker, follow the *RUN* commands in the [Dockerfile](../Dockerfile) up until

    RUN python3 -m spacy download en_core_web_sm

Then set the `DATA_DIR` variable in the Makefile to the directory in which you want to store the ELEVANT data files.

In `src/settings.py` add your data directory to the `_DATA_DIRECTORIES` list.

Finally, run

    export PYTHONPATH=$PYTHONPATH:src

to add elevant's `src` directory to your python path in your current shell or add this command to your `.bashrc` file,
to add it permanently.