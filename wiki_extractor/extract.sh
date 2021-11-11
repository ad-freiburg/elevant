#!/bin/bash

INPUT=$1
OUTPUT=$2

python3 WikiExtractor.py --sections --links --bold --json --output_file $OUTPUT $INPUT
