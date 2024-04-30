# List of Included Linkers
We distinguish between three classes of linkers in Elevant:
1. Some linkers can be incorporated into our framework without writing much code, e.g. by accessing an external
 linker API. These linkers can be used directly with Elevant's `link_benchmark_entities.py` script to generate linking
 results. The following linkers belong to this class:
    - [ReFinED](#refined)
    - [REL](#rel)
    - [GPT](#gpt) (requires an OpenAI API key)
    - [TagMe](#tagme) (requires an access token that can easily be obtained)
    - [WAT](#wat) (requires an access token that can easily be obtained)
    - [DBPedia Spotlight](#dbpedia-spotlight)
    - [Spacy](#spacy) (needs to be trained before usage)
    - [Our baselines](#baseline)
    - [Oracle](#oracle) (i.e. predictions that correspond exactly to the ground truth labels)

    All of these linkers are described in this document.

2. For some linkers, an entire code base is needed to produce linking results and this code base does not run
 out of the box or does not produce output in a format that can be mapped to Elevant's internal format, e.g. because
 important information such as the mention span is missing. We make the necessary adjustments to these linkers,
 dockerize them for an easy setup and put them into separate repositories. The following linkers belong to this class:
    - Neural EL (by Gupta et al.): see [our reproducible Neural EL repository](https://github.com/ad-freiburg/neural-el)
    - GENRE: see [our reproducible GENRE repository](https://github.com/ad-freiburg/GENRE)
    - Efficient EL: see [our reproducible efficient-autoregressive-EL repository](https://github.com/ad-freiburg/efficient-autoregressive-EL)

3. For linkers where an entire code base is needed which can be run without bigger problems out of the box and which
 yields output in a format that can easily be mapped to Elevant's internal format, it is enough to write a prediction
 reader that converts the linker's output into Elevant's internal format. Such prediction reader's are located in
 `src/prediction_readers/`. The following linkers are examples for this class:
    - Ambiverse


#### ReFinED
ReFinED is a fast end-to-end entity linker based on Transformers that is capable of generalizing to entities not seen
 during training. It was developed by Ayoola et al. and described in the 2022 paper
[ReFinED: An Efficient Zero-shot-capable Approach to End-to-End Entity Linking](https://arxiv.org/pdf/2207.04108v1.pdf).

In ELEVANT, you can use the ReFinED linker with the `link_benchmark_entities.py` script and the linker name `refined`.
 In the corresponding config file [configs/refined.config.json](../configs/refined.config.json) you can set the model
  name
 (e.g. `aida_model` for the fine-tuned model or `wikipedia_model` for the model trained on Wikipedia only) as well as
 the candidate set (`wikipedia` to restrict the candidate set to 6 million Wikidata entities that also have a
 Wikipedia page, or `wikidata` for a set of 33 million Wikidata entities).

    python3 link_benchmark_entities.py <experiment_name> -l refined -b <benchmark_name>

The ReFinED linker class is implemented [here](../src/elevant/linkers/refined_linker.py).
 
#### REL
REL (Radboud Entity Linker) is a modular linking system developed by van Hulst et al. and described in the 2020 paper 
 [REL: An Entity Linker Standing on the Shoulders of Giants](https://arxiv.org/pdf/2006.01969v1.pdf). The motivation
 behind REL is to provide a fast, modular state-of-the-art linking system where mention detection and disambiguation
 components can be easily exchanged and the underlying knowledge base (Wikipedia) can easily be updated.

Per default, REL uses Flair (Akbik et al., 2018) as NER component which is based on contextualized word embeddings.
 For the candidate selection, up to 4 candidate entities are selected based on their prior probability and up to 3
 candidate entities are selected based on the similarity between the candidate entity's Wikipedia2Vec embedding and
 the embeddings of the words in the mention's context. For the disambiguation step, they combine local compatibility,
 which includes prior probability and context similarity, with coherence with other linking decisions in the document.
 They use a feed forward neural network to optimize the disambiguation step and train it on the AIDA-CoNLL training
 dataset.
 
In ELEVANT, you can use the REL linker with the `link_benchmark_entities.py` script and the linker name `rel`.
 In the corresponding config file [configs/rel.config.json](../configs/rel.config.json), you can set the Wikipedia
 version and NER model name (consult the REL GitHub page for information on the available options:
 [GitHub repo](https://github.com/informagi/REL)). When you first use the corresponding model, the necessary data
 will be automatically downloaded. Alternatively you can set `use_api` to `true` and set the `api_url` config
 parameter (the official REL API URL per default), to query an API for REL linking results. Note that in this case,
 the config parameters `wiki_version` and `ner_model` have no effect.

    python3 link_benchmark_entities.py <experiment_name> -l rel -b <benchmark_name>

The REL linker class is implemented [here](../src/elevant/linkers/rel_linker.py). REL predicts Wikipedia entity links.
 We map the predicted Wikipedia entities to Wikidata using our mappings.

#### GPT
GPT probably needs no introduction. **NOTE: You will need your own OpenAI API key in order to use GPT within ELEVANT.**
 Using the OpenAI API is not free. See https://openai.com/pricing for information about the pricing.

In ELEVANT, you can use GPT for entity linking with the `link_benchmark_entities.py` script and the linker name `gpt`.
 In the corresponding config file [configs/gpt.config.json](../configs/gpt.config.json), you can set your OpenAI API key
 with the `openai_api_key` field. If this is not set, ELEVANT will try to retrieve the API key from the
 `OPENAI_API_KEY` environment variable.
 In the config, you can also set the model to be used. We recommend to use a model &gt;= `gpt-4`, since
 `gpt-3.5-turbo-1106` for example does not reliably produce the expected output format  especially for long benchmark
 texts. You can also set the model temperature as well as a seed for reproducible outputs there. If you set the
 `named_only` field to `true`, GPT will be prompted to only link named entities.
 See [here](../src/elevant/linkers/gpt_linker.py) for the exact prompt. You can adjust the prompt if you like but make sure you
 don't ask for a different output format, otherwise you will need to adjust the parser code in `parse_annotated_text()`.

    python3 link_benchmark_entities.py <experiment_name> -l gpt -b <benchmark_name>

The GPT linker class is implemented [here](../src/elevant/linkers/gpt_linker.py). GPT predicts Wikipedia entity names.
 We map the predicted Wikipedia entities to Wikidata using our mappings.

#### TagMe
TagMe was introduced by Ferragina & Scaiella in the 2010 paper [TAGME: On-the-fly Annotation of Short Text Fragments
 (by Wikipedia Entities)](https://dl.acm.org/doi/pdf/10.1145/1871437.1871689). TagMe particularly aims at linking
 entities in very short texts like tweets or snippets of search engine results. The code is available on [Github
 ](https://github.com/marcocor/tagme-python).
 
In ELEVANT, you can use the TagMe linker with the `link_benchmark_entities.py` script and the linker name `tagme`. In
 the corresponding config file [configs/tagme.config.json](../configs/tagme.config.json) you can additionally specify a
 score threshold. The threshold is a value between 0 and 1. Predicted entities with a score lower than the threshold
 will be discarded. Per default, the threshold is 0.2.
 **NOTE: You need a personal access token to access the TagMe API which ELEVANT uses.** The process is easy and is
 described at <https://github.com/marcocor/tagme-python>. Once you have your token, specify it in the config file
 under the key word `token`.
 
    python3 link_benchmark_entities.py <experiment_name> -l tagme -b <benchmark_name>

The TagMe linker class is implemented [here](../src/elevant/linkers/tagme_linker.py). TagMe predicts Wikipedia entity links.
 We map the predicted Wikipedia entities to Wikidata using our mappings.

#### WAT
WAT is an entity linker based on the TagMe linker introduced by Piccinno & Ferragina in the 2014 paper
 [From TagME to WAT: a new Entity Annotator](https://dl.acm.org/doi/pdf/10.1145/2633211.2634350). A WAT API is
 hosted at [d4science](https://sobigdata.d4science.org/web/tagme/wat-api).
 
In ELEVANT, you can use the WAT linker with the `link_benchmark_entities.py` script and the linker name `wat`. In
 the corresponding config file [configs/wat.config.json](../configs/wat.config.json) you can additionally specify a
 score threshold. The threshold is a value between 0 and 1. Predicted entities with a score lower than the threshold
 will be discarded. Per default, the threshold is 0.266.
 **NOTE: You need a personal access token to access the WAT API which ELEVANT uses.** The process is easy and is
 described at <https://github.com/marcocor/tagme-python>. Once you have your token, specify it in the config file
 under the key word `token`.
 
    python3 link_benchmark_entities.py <experiment_name> -l wat -b <benchmark_name>

The WAT linker class is implemented [here](../src/elevant/linkers/wat_linker.py). WAT predicts Wikipedia entity links.
 We map the predicted Wikipedia entities to Wikidata using our mappings.

#### DBpedia Spotlight
DBpedia Spotlight is a linking system developed by Daiber et al. and described in the 2013 paper
 [Improving Efficiency and Accuracy in Multilingual Entity Extraction](http://jodaiber.de/doc/entity.pdf). The system
 links entities to their entries in DBpedia.

In ELEVANT, you can use the DBpedia linker with the `link_benchmark_entities.py` script and the linker name
 `dbpedia-spotlight`. In the corresponding config file
 [configs/dbpedia-spotlight.config.json](../configs/dbpedia-spotlight.config.json) you can set the API
 URL - the official DBpedia Spotlight API URL per default, but you can also run the system yourself, e.g. using Docker
 as described in the [GitHub repo](https://github.com/dbpedia-spotlight/dbpedia-spotlight-model), and provide a custom
 API URL. You can also specify a confidence threshold, which is set to 0.35 per default.

    python3 link_benchmark_entities.py <experiment_name> -l dbpedia-spotlight -b <benchmark_name>

DBpedia predicts DBpedia entities which we map to Wikidata entities using our mappings. The DBpedia Spotlight linker
 class is implemented [here](../src/elevant/linkers/dbpedia_spotlight_linker.py).

#### Babelfy
Babelfy is a linking system developed by Moro et al. and described in the 2014 paper
 [Entity Linking meets Word Sense Disambiguation: a Unified Approach](http://wwwusers.di.uniroma1.it/~navigli/pubs/TACL_2014_Babelfy.pdf). The system
 links entities and word senses to their entries in DBpedia or BabelNet.

In ELEVANT, you can use the Babelffy linker with the `link_benchmark_entities.py` script and the linker name
 `babelfy`.

**NOTE: You need a personal API key to access the Babelfy API which ELEVANT uses.** The process is easy and is
 described at <http://babelfy.org/guide>. Once you have your API key, specify it in the config file
[configs/babelfy.config.json](../configs/babelfy.config.json)
 under the key word `api_key`.

    python3 link_benchmark_entities.py <experiment_name> -l babelfy -b <benchmark_name>

Babelfy predicts DBpedia entities which we map to Wikidata entities using our mappings. Predictions that only have a
 BabelNet reference and no DBpedia reference are linked to NIL. The Babelfy linker class is implemented
 [here](../src/elevant/linkers/babelfy_linker.py).

#### Baseline
ELEVANT comes with a simple baseline that performs Entity Recognition using the SpaCy NER component and that links
 entities based on prior probabilities for recognized mention texts. These prior probabilities are computed using
 Wikipedia hyperlinks. The prior probability for an entity *e* given a mention text *m* is computed as the number of
 times the text *m* was linked to *e* in our Wikipedia training split) over the number of times the text *m* was
 linked to any entity in our Wikipedia training split.
 
You can use the Baseline by providing the linker name `baseline` to the linking script:
 
    python3 link_benchmark_entities.py <experiment_name> -l baseline -b <benchmark_name>

The Baseline linker class is implemented [here](../src/elevant/linkers/baseline_linker.py).

#### POS Prior
This linker is similar to the baseline linker described above. The main difference is, that instead of using the
 SpaCy NER component, a set of simple rules based on POS tags are used for entity recognition.
 
You can use the POS Prior linker by providing the linker name `pos-prior`.

    python3 link_benchmark_entities.py <experiment_name> -l pos-prior -b <benchmark_name>

The POS Prior linker class is implemented [here](../src/elevant/linkers/prior_linker.py).


#### SpaCy

In order to run the spaCy linker, you first need to download the knowledge base, vocabulary and model files needed by
 the linker using the Makefile:

    make download_spacy_linking_files

The SpaCy linker can then be used by providing the linker name `spacy`:

    python3 link_benchmark_entities.py <experiment_name> -l spacy -b <benchmark_name>

In the corresponding config file [configs/spacy.config.json](../configs/spacy.config.json) you can adjust the model and
 knowledge base name if needed. The Spacy linker class is implemented [here](../src/elevant/linkers/spacy_linker.py).

Alternatively you can train the linker yourself. This requires the following steps:

1. Generate word vectors:

       python3 scripts/create_entity_word_vectors.py 0

2. Create the Wikipedia knowledge base:

       python3 scripts/create_knowledge_base_wikipedia.py

3. Train the entity linker:

       python3 scripts/train_spacy_entity_linker.py <linker_name> <n_batches> wikipedia
       
#### Oracle

You can also create oracle predictions (that is, predictions that correspond exactly to the ground truth labels) for
 any benchmark by specifying the linker name `oracle`. This can be useful e.g., to inspect a benchmark's ground truth
 labels.

    python3 link_benchmark_entities.py <experiment_name> -l oracle -b <benchmark_name>

The code for creating oracle predictions can be found [here](../src/elevant/linkers/oracle_linker.py)
