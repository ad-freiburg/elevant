#!/bin/sh

wget cogcomp.seas.upenn.edu/software/Wikifier2013.zip
unzip Wikifier2013.zip
cd Wikifier2013

cp ../Dockerfile .
cp ../Makefile .
cp ../.dockerignore .

chmod a+w data/TextAnnotationCache/  # Prevent permission errors in docker container