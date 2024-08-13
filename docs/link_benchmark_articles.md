# Link Benchmark Articles
To link the articles of a benchmark with a single linker configuration, use the script `link_benchmark.py`:

    python3 link_benchmark.py <experiment_name> -l <linker_name> -b <benchmark_name>

The linking results will be written to
 `evaluation-results/<linker_name>/<adjusted_experiment_name>.<benchmark_name>.linked_articles.jsonl` where
 `<adjusted_experiment_name>` is `<experiment_name>` in lowercase and characters other than `[a-z0-9-]` replaced by
 `_`.

Properties specific to the selected linker such as confidence thresholds, model paths, etc. are read from the linker's
 config file at `configs/<linker_name>.config.json`.

Additionally, this will create a file
`evaluation-results/<linker_name>/<adjusted_experiment_name>.<benchmark_name>.metadata.jsonl` that contains metadata
 information such as an experiment description and the experiment name that will be displayed in the evaluation
 webapp. The description can be specified using the `-desc` argument. Per default, the description from the linker's
 config file is used. You can also simply adjust the description and experiment name in the metadata file at any time.

For a list of entity linkers included in ELEVANT, see [Included Linkers](linkers).

## Use NIF API
If you implemented a NIF API for your linker as is needed to evaluate a linker using GERBIL, you can use that same
 NIF API to link benchmark articles with ELEVANT. To do so, use the `-api` option of the `link_benchmark.py` script:

    python3 link_benchmark.py <experiment_name> -api <api_url> -pname <linker_name> -b <benchmark_name>

Each benchmark article text will then be sent as NIF context in a separate HTTP POST request to your NIF API.
The API should return the linking results in NIF format. See also the
[GERBIL documentation](https://github.com/dice-group/gerbil/wiki/How-to-create-a-NIF-based-web-service)
for more information on how to implement a NIF API.

The linking results will be written to
 `evaluation-results/<adjusted_linker_name>/<adjusted_experiment_name>.<benchmark_name>.linked_articles.jsonl` where
 `<adjusted_name>` is `<name>` in lowercase and characters other than `[a-z0-9-]` replaced by `_`.
 If the `-pname` option is omitted, `<adjusted_linker_name>` is `unknown_linker`.


## Use Existing Linking Results
If you already have linking results for a certain benchmark that you want to evaluate with ELEVANT, you can use the
 `link_benchmark.py` script to convert your linking results into the JSONL format used by us. This works if
 the text of the benchmark you linked corresponds to the text of one of the benchmarks in the `benchmarks` directory
 and if your linking results are in one of the following formats:

- NLP Interchange Format (NIF)
- a very simple JSONL format
- Ambiverse output format

Each of these formats is explained in the following sections.

If you don't want to use any of the supported formats you can write your own prediction reader, as explained in section
 [Writing a Custom Prediction Reader](#writing-a-custom-prediction-reader).

The script call to convert linking results into our format is

    python3 link_benchmark.py <experiment_name> -pfile <path_to_linking_results> -pformat <linking_results_format> -pname <linker_name> -b <benchmark_name>

The converted linking results will be written to
 `evaluation-results/<adjusted_linker_name>/<adjusted_experiment_name>.<benchmark_name>.linked_articles.jsonl` where
 `<adjusted_linker_name>` and `<adjusted_experiment_name>` are lowercased versions of `<linker_name>` and
 `<experiment_name>` with characters other than `[a-z0-9-]` replaced by `_`. If the `-pname` option is omitted,
 `<adjusted_linker_name>` is `unknown_linker`.

#### Linking Results in NIF
If you have linking results for a certain benchmark in NIF format, use `-pformat nif` in the script call described
 above, i.e.

    python3 link_benchmark.py <experiment_name> -pfile <path_to_linking_results> -pformat nif -pname <linker_name> -b <benchmark_name>

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
    
- Entity identifiers can be either from Wikidata, Wikipedia or DBpedia.
- `<path_to_linking_results>` can be the path to a single NIF file that contains all benchmark articles and the
 predicted links or the path to a directory that contains multiple such NIF files.

The NIF prediction reader is implemented [here](../src/elevant/prediction_readers/nif_prediction_reader.py).

#### Linking Results in a Simple JSONL Format
If you have linking results for a certain benchmark in a very simple JSONL format as described below, use
 `-pformat simple-jsonl` in the script call described above, i.e.

    python3 link_benchmark.py <experiment_name> -pfile <path_to_linking_results> -pformat simple-jsonl -pname <linker_name> -b <benchmark_name>

The file `<path_to_linking_results>` should contain one line per benchmark article. The order of the predictions
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
- Optionally, you can specify a field `candidates` for each prediction that contains a list of candidate entity
  references that were considered for the mention.

The simple JSONL prediction reader is implemented [here](../src/elevant/prediction_readers/simple_jsonl_prediction_reader.py).

#### Linking Results in Ambiverse Output Format
If you have linking results for a certain benchmark in the Ambiverse output format, use `-pformat ambiverse` in the
 script call described above, i.e.

    python3 link_benchmark.py <experiment_name> -pfile <path_to_linking_results> -pformat ambiverse -pname <linker_name> -b <benchmark_name>

`<path_to_linking_results>` should be the path to a directory that contain files with linking results for one benchmark
 article per file. When sorting the files by file name, the order should correspond to the article order of the
 benchmark in the `benchmarks` directory. Your linking result files should look something like this:

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

The Ambiverse prediction reader is implemented [here](../src/elevant/prediction_readers/ambiverse_prediction_reader.py).

### Writing a Custom Prediction Reader
As an alternative to converting your predictions into one of the formats mentioned above, you can write your own
 prediction reader, such that you can use your prediction files with the `link_benchmark.py` script directly.
 This requires three steps. **Note: Make sure you perform the following steps outside of the docker container,
 otherwise your changes will be lost when exiting the container.**:

1) Implement a prediction reader in `src/elevant/prediction_readers/` that inherits from
 `src.elevant.prediction_readers.abstract_prediction_reader.AbstractPredictionReader`. You must either implement the
 `predictions_iterator()` method or the `get_predictions_with_text_from_file()` method.

    Implement `predictions_iterator()` if you are sure that the order in which the predictions are read corresponds
     to the article order in the benchmark. Set `predictions_iterator_implemented = True` when calling
     `super().__init__()`. See [here](../src/elevant/prediction_readers/simple_jsonl_prediction_reader.py) for an example.

    Implement `get_predictions_with_text_from_file()` if you are not sure that the order in which the predictions are
     read corresponds to the article order in the benchmark and the prediction file contains the original article
     texts. Set `predictions_iterator_implemented = False` when calling `super().__init__()`. See
     [here](../src/elevant/prediction_readers/nif_prediction_reader.py) for an example.

2) Add your custom prediction reader name to the `src.elevant.linkers.linkers.PredictionFormats` enum, e.g.
 `MY_FORMAT = "my_format"`.

3) In `src.elevant.linkers.linking_system.LinkingSystem._initialize_linker` add an `elif` case in which you load 
   necessary
 mappings (if any) and initialize the `LinkingSystem`'s `prediction_reader`. This could look something like this:

        elif linker_type == Linkers.MY_FORMAT.value:
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA, MappingName.REDIRECTS})
            self.prediction_reader = MyCustomPredictionReader(prediction_file, self.entity_db)

    where `prediction_file` is the path to the prediction file. The `load_missing_mappings()` line is necessary if you
     predict Wikipedia entities and therefore have to convert them to Wikidata entities. The mappings are loaded into
     `self.entity_db`. You can then get a Wikidata QID from a Wikipedia title by calling

        entity_id = KnowledgeBaseMapper.get_wikidata_qid(entity_reference, self.entity_db)

You can then convert your linking results into our JSONL format by running

    python3 link_benchmark.py <experiment_name> -pfile <path_to_linking_results> -pformat my_format -pname <linker_name> -b <benchmark_name>

## Integrating an Entity Linker
To integrate a new entity linker into ELEVANT, such that it can be used out of the box with the
`link_benchmark.py` script as any other linker, you need to follow the steps outlined in this section.
**Note: Make sure you perform the following steps outside of the docker container, otherwise your changes will be lost
when exiting the container.**:

1) First, you need to create a new config file in the `configs` directory. The config file should contain the linker
 name, an experiment description and configurable parameters, such as confidence thresholds, model paths, API keys, etc.
 The config file should be named `<linker_name>.config.json` where `<linker_name>` is the name of the linker.
 See the existing config files in the `configs` directory for examples.

2) Implement a new entity linker in `src/elevant/linkers/` that inherits from
 `src.elevant.linkers.abstract_entity_linker.AbstractEntityLinker`. Your linker class must implement the `__init__()`,
 `predict()` and `has_entity()` method.

     In the `__init__()` method you should load config values from the linker's config file and initialize the linker.
     Typically, if your system predicts Wikipedia or DBpedia entity references, the method should take an EntityDatabase
     oject as argument. It should also take a config dictionary as argument (`config: Dict[str, Any]`) from which to load
     the linker's config parameters.

     The `predict()` method takes an article text, a spaCy document and a boolean indicating whether only capitalized
     mentions should be linked. Within that method, your linker should predict entities for the mentions in the text and
     convert them to `elevant.models.entity_prediction.EntityPrediction` objects. If your linker does not return information
     on which candidates were considererd for a mention, the candidates attribute should consist only of the predicted
     entity. If your linker returns Wikipedia or DBpedia entity references, use the
     `elevant.utils.knowledge_base_mapper.KnowledgeBaseMapper` to map the references to Wikidata.
     The `predict()` method should return a dictionary, mapping mention spans (a tuple consisting of start character
     and end character) to their `EntityPrediction` objects.

     The `has_entity()` method takes an entity reference and returns whether the entity reference is known to the linker.
     This is not crucial for the functionality of ELEVANT and can be implemented to simply return True.

     See for example the [TagMe linker](../src/elevant/linkers/tagme_linker.py) or the
     [ReFinED linker](../src/elevant/linkers/refined_linker.py).

3) Add your entity linker name to the `elevant.linkers.linkers.Linkers` enum, e.g. `LINKER_NAME = "linker_name"`.

4) In `elevant/linkers/linking_system.py`, add an `elif` case in the `_initialize_linker` method in which you
 load necessary mappings (if any) and initialize your linker. This could look something like this:

        elif linker_type == Linkers.LINKER_NAME.value:
            from elevant.linkers.linker_name import LinkerName
            self.load_missing_mappings({MappingName.WIKIPEDIA_WIKIDATA,
                                        MappingName.REDIRECTS})
            self.linker = LinkerName(self.entity_db, self.linker_config)

     If your linker predicts Wikipedia or DBpedia entity references, you need to load the mappings `WIKIPEDIA_WIKIDATA` and
     `REDIRECTS` into `self.entity_db` using the `load_missing_mappings()` method. You can then get a Wikidata QID from a
        Wikipedia title by calling

        entity_id = KnowledgeBaseMapper.get_wikidata_qid(entity_reference, self.entity_db)

After following these steps, you can use your linker just like any other included linker by running

    python3 link_benchmark.py <experiment_name> -l linker_name -b benchmark_name

## Linking Multiple Benchmarks with Multiple Linkers
You can provide multiple benchmark names to link all of them at once with the specified linker. E.g.

    python3 link_benchmark.py baseline -l baseline -b kore50 msnbc spotlight

will link the KORE50, MSNBC and DBpedia Spotlight benchmarks using the baseline entity linker. This saves a lot of time
 in comparison to calling `link_benchmark.py` separately for each benchmark, since a lot of the time is
 needed to load entity information which only has to be done once per call.

If you want to link all benchmarks contained in the `benchmarks` directory, you can use the `ALL` keyword. E.g.:

    python3 link_benchmark.py baseline -l baseline -b ALL

You can use the Makefile to link multiple benchmarks using multiple linkers with one command.

To link all benchmarks specified in the Makefile's `BENCHMARK_NAMES` variable using all linking systems specified in
 the Makefile's `LINKING_SYSTEMS` variable run

    make link_benchmarks

You can examine or adjust each system's exact linking arguments in the Makefile's `link_benchmark` target if needed.

## Converting Linking Results of Multiple Systems for Multiple Benchmarks
You can use the Makefile to convert the linking results of multiple systems for multiple benchmarks with one command.

To convert the results for all benchmarks specified in the Makefile's `BENCHMARK_NAMES` variable for all systems
 specified in the Makefile's `PREDICTIONS` variable run

    make convert_predictions

You can examine or adjust each system's linking results path and other linking arguments in the Makefile's
 `convert_benchmark_predictions` target. Note that the linking results for the systems under `PREDICTIONS` need to be
 created first and stored at a path that can then be passed to `link_benchmark.py` as linker argument.
 See the READMEs in the `neural-el` or `wikifier` directories for more information.
