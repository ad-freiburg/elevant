# List of Included Linkers
ELEVANT comes with a number of entity linkers that can be used out of the box and some that have to be trained first.
This document gives an overview of these entity linkers and how they can be used.

#### TagMe
TagMe was introduced by Ferragina & Scaiella in the 2010 paper [TAGME: On-the-fly Annotation of Short Text Fragments
 (by Wikipedia Entities)](https://dl.acm.org/doi/pdf/10.1145/1871437.1871689). TagMe particularly aims at linking
 entities in very short texts like tweets or snippets of search engine results. The code is available on [Github
 ](https://github.com/marcocor/tagme-python).
 
In ELEVANT, you can use the TagMe linker with the `link_benchmark_entities.py` script and the linker name `tagme`. In
 the corresponding config file `configs/tagme.config.json` you can additionally specify a score threshold. The
 threshold is a value between 0 and 1. Predicted entities with a score lower than the threshold will be discarded.
 Per default, the threshold is 0.2.
 
    python3 link_benchmark_entities.py <experiment_name> -l tagme -b <benchmark_name>

The TagMe linker class is implemented [here](../src/linkers/tagme_linker.py) and uses the TagMe API. TagMe predicts
 Wikipedia entity links. We map the predicted Wikipedia entities to Wikidata using our mappings.

#### DBpedia Spotlight
DBpedia Spotlight is a linking system developed by Daiber et al. and described in the 2013 paper
 [Improving Efficiency and Accuracy in Multilingual Entity Extraction](http://jodaiber.de/doc/entity.pdf). The system
 links entities to their entries in DBpedia.

In ELEVANT, you can use the DBpedia linker with the `link_benchmark_entities.py` script and the linker name
 `dbpedia_spotlight`. In the corresponding config file `configs/dbpedia_spotlight.config.json` you can set the API
 URL - the official DBpedia Spotlight API URL per default, but you can also run the system yourself, e.g. using Docker
 as described in the [GitHub repo](https://github.com/dbpedia-spotlight/dbpedia-spotlight-model), and provide a custom
 API URL. You can also specify a confidence threshold, which is set to 0.35 per default.

    python3 link_benchmark_entities.py <experiment_name> -l dbpedia_spotlight -b <benchmark_name>

DBpedia predicts DBpedia entities which we map to Wikidata entities using our mappings. The DBpedia Spotlight linker
 class is implemented [here](../src/linkers/dbpedia_spotlight_linker.py).

#### Baseline
ELEVANT comes with a simple baseline that performs Entity Recognition using the SpaCy NER component and that links
 entities based on prior probabilities for recognized mention texts. These prior probabilities are computed using
 Wikipedia hyperlinks. The prior probability for an entity *e* given a mention text *m* is computed as the number of
 times the text *m* was linked to *e* in our Wikipedia training split) over the number of times the text *m* was
 linked to any entity in our Wikipedia training split.
 
You can use the Baseline by providing the linker name `baseline` to the linking script:
 
    python3 link_benchmark_entities.py <experiment_name> -l baseline -b <benchmark_name>

The Baseline linker class is implemented [here](../src/linkers/baseline_linker.py).

#### POS Prior
This linker is similar to the baseline linker described above. The main difference is, that instead of using the
 SpaCy NER component, a set of simple rules based on POS tags are used for entity recognition.
 
You can use the POS Prior linker by providing the linker name `pos_prior`.

    python3 link_benchmark_entities.py <experiment_name> -l pos_prior -b <benchmark_name>

The POS Prior linker class is implemented [here](../src/linkers/prior_linker.py).


#### SpaCy

The SpaCy linker does not work out of the box and needs to be trained first.
This requires the following steps:

1. Generate word vectors:

       python3 create_entity_word_vectors.py 0

2. Create the Wikipedia knowledge base:

       python3 create_knowledge_base_wikipedia.py

3. Train the entity linker:

       python3 train_spacy_entity_linker.py <linker_name> <n_batches> wikipedia
       
The SpaCy linker can then be used with the created wikipedia knowledge base by providing the linker name `spacy` and
 setting the knowledge base name to `wikipedia` in the corresponding config file `configs/spacy.config.json`.
 
    python3 link_benchmark_entities.py <experiment_name> -l spacy -b <benchmark_name>

The Spacy linker class is implemented [here](../src/linkers/spacy_linker.py).