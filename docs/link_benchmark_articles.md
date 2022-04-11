# Link Benchmark Articles
To link the articles of a benchmark with a single linker configuration, use the script `link_benchmark_entities.py`:

    python3 link_benchmark_entities.py <experiment_name> <linker_type> <linker_info> -b <benchmark_name>

The linking results will be written to `evaluation-results/<linker_type>/<experiment_name>.<benchmark_name>.jsonl`.
 For example

    python3 link_benchmark_entities.py tagme.thresh02 tagme 0.2 -b kore50

will create the file `evaluation-results/tagme/tagme.thresh02.kore50.jsonl`. The result file contains one article as
 JSON object per line. Each JSON object contains benchmark article information such as the article title, text, and
 ground truth labels, as well as the entity mentions predicted by the specified linker.

## Use Existing Linking Results
If you already have linking results for a certain benchmark that you want to evaluate with ELEVANT, you can use the
 `link_benchmark_entities.py` script to convert your linking results into the JSONL format used by us. This works if
 the text of the benchmark you linked corresponds to the text of one of the benchmarks in the `benchmarks` directory
 and if your linking results are in one of the following formats:

- NLP Interchange Format (NIF)
- a very simple JSONL format
- Ambiverse output format

Each of these formats is explained in the following sections.

Alternatively you can write your own prediction reader, as explained in section
 [Writing a Custom Prediction Reader](#writing-a-custom-prediction-reader).

#### Linking Results in NIF
If you have linking results for a certain benchmark in NIF format, run

    python3 link_benchmark_entities.py <experiment_name> nif <path_to_linking_results> -b <benchmark_name>

to convert your linking results into the JSONL format used by us.

Your linking results file should look something like this:

    @prefix itsrdf: <http://www.w3.org/2005/11/its/rdf#> .
    @prefix nif: <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    
    <http://www.aksw.org/gerbil/NifWebService/request_0#char=0,87> a nif:Context,
        nif:OffsetBasedString ;
    nif:beginIndex "0"^^xsd:nonNegativeInteger ;
    nif:endIndex "87"^^xsd:nonNegativeInteger ;
    nif:isString "Angelina, her father Jon, and her partner Brad never played together in the same movie." .
    
    <http://www.aksw.org/gerbil/NifWebService/request_0#offset_42_46> a nif:OffsetBasedString,
            nif:Phrase ;
        nif:anchorOf "Brad" ;
        nif:beginIndex "42"^^xsd:nonNegativeInteger ;
        nif:endIndex "46"^^xsd:nonNegativeInteger ;
        nif:referenceContext <http://www.aksw.org/gerbil/NifWebService/request_0#char=0,87> ;
        itsrdf:taIdentRef <https://en.wikipedia.org/wiki/Brad_Pitt> .
    
- Entity identifiers can be either from Wikidata or from Wikipedia or DBpedia.
- `<path_to_linking_results>` can be the path to a single NIF file that contains all benchmark articles and the
 predicted links or the path to a directory that contains multiple such NIF files.

The NIF prediction reader is implemented [here](../src/prediction_readers/nif_prediction_reader.py).

#### Linking Results in a Simple JSONL Format
If you have linking results in a very simple JSONL format as described below, run

    python3 link_benchmark_entities.py <experiment_name> simple_jsonl <path_to_linking_results_file> -b <benchmark_name>

The file `<path_to_linking_results_file>` should contain one line per benchmark article. The order of the predictions
 should correspond to the article order of the benchmark in the `benchmarks` directory. The linking results file
 should look something like this:

    {"predictions": [{"entity_reference": "Angelina Jolie", "start_char": 0, "end_char": 8}, {"entity_reference": "Jon Stewart", "start_char": 21, "end_char": 24}, {"entity_reference": "Brad Paisley", "start_char": 42, "end_char": 46}]}
    {"predictions": [{"entity_reference": "Heidi", "start_char": 0, "end_char": 5}, {"entity_reference": "Las Vegas", "start_char": 35, "end_char": 40}]}
    ...

- `entity_reference` is a reference to the predicted entity in one of the knowledge bases [Wikidata, Wikipedia
 , DBpedia]. The reference is either a complete link to the entity (e.g.
 "https://en.wikipedia.org/wiki/Angelina_Jolie") or just the Wikidata QID / Wikipedia title / DBpedia title. Note
 however, if no complete link is given the knowledge base is inferred from the format of the entity reference
 and predicted Wikipedia titles that match the regular expression `Q[0-9]+` will be interpreted as Wikidata QIDs.
- `start_char` is the character offset of the start of the mention (including) within the article text
- `end_char` is the character offset of the end of the mention (excluding) within the article text

The simple JSONL prediction reader is implemented [here](../src/prediction_readers/simple_jsonl_prediction_reader.py).

#### Linking Results in Ambiverse Output Format
If you have linking results in the Ambiverse output format, run

    python3 link_benchmark_entities.py <experiment_name> ambiverse <path_to_linking_results_directory> -b <benchmark_name>

`<path_to_linking_results_directory>` should contain files with linking results for one benchmark article per file.
 When sorting the files by file name, the order should correspond to the article order of the benchmark in the
 `benchmarks` directory. Your linking result files should look something like this:

    {
       "docId":"xyz",
       "language":"en",
       "matches":[
          {
             "charLength":10,
             "charOffset":413,
             "text":"Red Planet",
             "entity":{
                "id":"http://www.wikidata.org/entity/Q111",
                "confidence":0.697028442167754
             },
             "type":"ORG"
          },
          ...
       ],
       "entities":[
          {
             "id":"http://www.wikidata.org/entity/Q111",
             "name":"Mars",
             "url":"http://en.wikipedia.org/wiki/Mars",
             "type":"OTHER",
             "salience":0.6872184020986541
          },
          ...
       ]
    }

The Ambiverse prediction reader is implemented [here](../src/prediction_readers/ambiverse_prediction_reader.py).

### Writing a Custom Prediction Reader
As an alternative to converting your predictions into one of the formats mentioned above, you can write your own
 prediction reader, such that you can use your prediction files with the `link_benchmark_entities.py` script directly.
 This requires three steps:

1) Implement a prediction reader in `src/prediction_readers/` that inherits from
 `src.prediction_readers.abstract_prediction_reader.AbstractPredictionReader`. You must either implement the
 `predictions_iterator()` method or the `get_predictions_with_text_from_file()` method.

    Implement `predictions_iterator()` if you are sure that the order in which the predictions are read corresponds
     to the article order in the benchmark. Set `predictions_iterator_implemented = True` when calling
     `super().__init__()`. See [here](../src/prediction_readers/simple_jsonl_prediction_reader.py) for an example.

    Implement `get_predictions_with_text_from_file()` if you are not sure that the order in which the predictions are
     read corresponds to the article order in the benchmark and the prediction file contains the original article
     texts. Set `predictions_iterator_implemented = False` when calling `super().__init__()`. See
     [here](../src/prediction_readers/nif_prediction_reader.py) for an example.

2) Add your custom prediction reader name to the `src.linkers.linkers.Linkers` enum, e.g. `MY_FORMAT = "my_format"`.

3) In `src.linkers.linking_system.LinkingSystem._initialize_linker` add an `elif` case in which you load necessary
 mappings (if any) and initialize the `LinkingSystem`'s `prediction_reader`. This could look something like this:

        elif linker_type == Linkers.MY_FORMAT.value:
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA, MappingName.REDIRECTS})
            self.prediction_reader = MyCustomPredictionReader(linker_info, self.entity_db)

    where `linker_info` is the path to the prediction file. The `load_missing_mappings()` line is necessary if you
     predict Wikipedia entities and therefore have to convert them to Wikidata entities. The mappings are loaded into
     `self.entity_db`. You can then get a Wikidata QID from a Wikipedia title by calling

        qid = self.entity_db.link2id(wikipedia_title)

You can then convert your linking results into our JSONL format by running

    python3 link_benchmark_entities.py <experiment_name> my_format <path_to_linking_results> -b <benchmark_name>


## Link Multiple Benchmarks with Multiple Linkers
You can use the Makefile to link multiple benchmarks using multiple linkers with one command.

To link all benchmarks specified in the Makefile's `BENCHMARK_NAMES` variable using all linking systems specified in
 the Makefile's `LINKING_SYSTEMS` variable run

    make link_benchmarks

You can examine or adjust each system's exact linking arguments in the Makefile's `link_benchmark` target if needed.

NOTE: The linking results for some systems like Neural-EL, Wikifier and Ambiverse need to be created separately and
 stored at a path that can then be passed to `link_benchmark_entities.py` as linker argument. See the READMEs in the
 `neural-el` or `wikifier` directories for more information. For other systems like Spacy or Explosion you first need
 to train the respective linker (explained later in this README).
