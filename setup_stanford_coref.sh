# Set up Stanford CoreNLP for coreference resolution.
python3 -c "import stanza; stanza.install_corenlp(dir='/home/Stanford_CoreNLP')"
export CORENLP_HOME=/home/Stanford_CoreNLP
apt-get update && apt-get install default-jre