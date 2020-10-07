#!/bin/bash

INPUT=$1
OUTPUT=$2

python3 WikiExtractor.py --links --json --output_file $OUTPUT $INPUT
