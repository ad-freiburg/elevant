# Add a Benchmark
You can easily add a benchmark if you have a benchmark file that is in one of the following formats:

- [a very simple JSONL format](#simple-jsonl-format)
- [NLP Interchange Format (NIF)](#nif)
- [IOB-based format](#aida-conll-iob-format) used by Hoffart et al. for their AIDA-CoNLL benchmark
- [XML format](#xml-msnbc-format) used for example for the MSNBC benchmarks
- [TTL format](#oke) used for the OKE challenges
- [a simple TSV format](#tsv-iob-format) with IOB tags
- [our JSONL format](#our-jsonl-format)

To add a benchmark, simply run

    python3 add_benchmark.py <benchmark_name> -bfile <benchmark_file> -bformat <simple-jsonl|nif|aida-conll|xml|oke|tsv|ours>

This converts the `<benchmark_file>` into our JSONL format (if it is not in this format already), annotates ground
 truth labels with their Wikidata label and Wikidata types as given in
 `<data_directory>/wikidata_mappings/entity-types.tsv` and writes the result to the file
 `benchmarks/<benchmark_name>.benchmark.jsonl`. Additionally, a file `benchmarks/<benchmark_name>.metadata.jsonl` is
 created that contains metadata information such as a benchmark description and the benchmark name that will be
 displayed in the evaluation webapp. The description and displayed name can be specified using the `-desc` and
 `-dname` arguments. You can also simply adjust the description and experiment name in the metadata file at any time.

If your benchmark is not in one of the supported formats, you can either convert it into one of those formats
 yourself or write your own benchmark reader, as explained in section
 [Writing a Custom Benchmark Reader](#writing-a-custom-benchmark-reader).

## Benchmark Formats

This section describes the three file formats that can be used as input to the `add_benchmark.py` script.

#### Simple JSONL Format
The benchmark file should contain one line per benchmark article, where each line is a json object with the
 following keys:
- `text`: The text of the benchmark article
- `title` (*optional*): The title of the benchmark article
- `labels`: The ground truth labels for an article. An array of objects with the keys
    - `entity_reference`: The reference to the predicted entity in one of the knowledge bases [Wikidata, Wikipedia
    , DBpedia]. The reference is either a complete link to the entity (e.g.
    "https://en.wikipedia.org/wiki/Angelina_Jolie") or just the Wikidata QID / Wikipedia title / DBpedia title. Note
    however, if no complete link is given the knowledge base is inferred from the format of the entity reference and
    predicted Wikipedia titles that match the regular expression `Q[0-9]+` will be interpreted as Wikidata QIDs.
    - `start_char`: The character offset of the start of the label (including) within the article text
    - `end_char`: The character offset of the end of the label (excluding) within the article text
    - `coref`(*optional*): A boolean flag indicating whether the ground truth label is a coreference. If this is not set
    for a ground truth label ELEVANT will infer whether the label is a coreference or not from the mention text
    (a mention is marked as a coreference if it is a pronoun or of the format "the *type*").

Your benchmark file should look something like this:

    {"text": "Angelina, her father Jon, and her partner Brad never played together in the same movie.", "title": "Some Title", "labels": [{"entity_reference": "Angelina Jolie", "start_char": 0, "end_char": 8}, {"entity_reference": "Jon Voight", "start_char": 21, "end_char": 24}, {"entity_reference": "Brad Pitt", "start_char": 42, "end_char": 46}]}
    {"text": "Heidi and her husband Seal live in Vegas.", "title": "Some Title", "labels": [{"entity_reference": "Heidi Klum", "start_char": 0, "end_char": 5}, {"entity_reference": "Seal", "start_char": 22, "end_char": 26}, {"entity_reference": "Las Vegas", "start_char": 35, "end_char": 40}]}

`<benchmark_file>` can be the path to a single JSONL file that contains all benchmark articles or the path to a
 directory that contains multiple such JSONL files.

The Simple JSONL benchmark reader is implemented [here](../src/elevant/benchmark_readers/simple_jsonl_benchmark_reader.py).

#### NIF
The NIF format for the purpose of entity linking is explained in detail in the
[GERBIL Wiki](https://github.com/dice-group/gerbil/wiki/How-to-generate-a-NIF-dataset).

Your benchmark file should look something like this:

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

Note that in ELEVANT
- entity identifiers can be from Wikidata, Wikipedia or DBpedia
- `<benchmark_file>` can be the path to a single NIF file that contains all benchmark articles or the path to a
 directory that contains multiple such NIF files
 
The NIF benchmark reader is implemented [here](../src/elevant/benchmark_readers/nif_benchmark_reader.py).

#### AIDA-CoNLL IOB Format
The format should be as follows:
- Each document starts with a line that starts with the string `-DOCSTART-`
- Each following line represents a single token, sentences are separated by an empty line

Lines with tabs are tokens the are part of a mention, where
- column 1 is the token.
- column 2 is either "B" (beginning of a mention), "I" (continuation of a mention) or "O" (outside of a mention). The
 O can be omitted.
- column 3 is the full mention, *but its content is not used by our benchmark reader*.
- column 4 is the corresponding YAGO2 entity OR `--NME--`, denoting an unknown entity. *We only use this column to
 check whether its content is `--NME--`*.
- column 5 is the corresponding Wikipedia URL of the entity. *In ELEVANT, this can also be a Wikidata or DBpedia URL.*
- column 6 is the corresponding Wikipedia ID of the entity, *but its content is not used by our benchmark reader*.
- column 7 is the corresponding Freebase mid, *but its content is not used by our benchmark reader*.

Your benchmark file should look something like this:

    -DOCSTART- (1 EU)
    EU	B	EU	--NME--
    rejects
    German	B	German	Germany	http://en.wikipedia.org/wiki/Germany	11867	/m/0345h
    call
    to
    boycott
    British	B	British	United_Kingdom	http://en.wikipedia.org/wiki/United_Kingdom	31717	/m/07ssc
    lamb
    .
    
    Peter	B	Peter Blackburn	--NME--
    Blackburn	I	Peter Blackburn	--NME--

The AIDA-CoNLL benchmark reader is implemented [here](../src/elevant/benchmark_readers/aida_conll_benchmark_reader.py).


#### XML (MSNBC) Format
The benchmark reader for the XML format takes two paths as input. The first one is the path to an XML file containing
 the ground truth labels. This file should look something like this:

    ?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <msnbc.entityAnnotation>
            <document docName="3683270">
                    <annotation>
                            <mention>NEW YORK</mention>
                            <wikiName>New York City</wikiName>
                            <offset>46</offset>
                            <length>8</length>
                    </annotation>
                    <annotation>
                            <mention>New York Stock Exchange</mention>
                            <wikiName>NIL</wikiName>
                            <offset>311</offset>
                            <length>23</length>
                    </annotation>

                    ...
        </document>
    </msnbc.entityAnnotation>

Alternatively, the first path may be a path to a directory containing one file per article with annotations in a
 format like this:

    <ReferenceProblem>
    <ReferenceFileName>
    Bus16451112.txt
    </ReferenceFileName>
    <ReferenceInstance>
    <SurfaceForm>
    Home Depot
    </SurfaceForm>
    <Offset>
    0
    </Offset>
    <Length>
    10
    </Length>
    <ChosenAnnotation>
    http://en.wikipedia.org/wiki/Home_Depot
    </ChosenAnnotation>
    <NumAnnotators>
    1
    </NumAnnotators>
    <AnnotatorId>
    Silviu Cucerzan
    </AnnotatorId>
    <Annotation>
    Home Depot
    </Annotation>


The second path is the path to a directory containing txt files with the raw article texts (one article per file).
 The filename of an article text must be the same as the `docName` (or the `ReferenceFileName`) in the XML file for
 that article.

In order to add a benchmark in this format, call the `add_benchmark.py` with the following arguments:

    python3 add_benchmark.py <benchmark_name> -bfile <path_to_xml_file(s)> <path_to_raw_text_dir> -bformat xml

The XML benchmark reader is implemented [here](../src/elevant/benchmark_readers/xml_benchmark_reader.py).

#### OKE
The OKE format is based on NIF, but the taIdentRef are not valid entity URIs. Instead, it includes sameAs relations
 that map the URIs used for the taIdentRef to DBpedia URIs. The benchmark file should look something like this:

    @prefix owl:   <http://www.w3.org/2002/07/owl#> .
    @prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
    @prefix oke:   <http://www.ontologydesignpatterns.org/data/oke-challenge/task-1/sentence-> .
    @prefix itsrdf: <http://www.w3.org/2005/11/its/rdf#> .
    @prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix nif:   <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#> .
    @prefix dul:   <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#> .
    @prefix dbpedia: <http://dbpedia.org/resource/> .

    <http://www.ontologydesignpatterns.org/data/oke-challenge/task-1/sentence-24#char=0,111>
        a               nif:String , nif:RFC5147String , nif:Context ;
        nif:beginIndex  "0"^^xsd:nonNegativeInteger ;
        nif:endIndex    "111"^^xsd:nonNegativeInteger ;
        nif:isString    "Neruda derived his pen name from the Czech poet Jan Neruda and became known as a poet when he was 10 years old."@en .

    <http://www.ontologydesignpatterns.org/data/oke-challenge/task-1/sentence-24#char=0,6>
        a                     nif:String , nif:RFC5147String ;
        nif:anchorOf          "Neruda"@en ;
        nif:beginIndex        "0"^^xsd:nonNegativeInteger ;
        nif:endIndex          "6"^^xsd:nonNegativeInteger ;
        nif:referenceContext  <http://www.ontologydesignpatterns.org/data/oke-challenge/task-1/sentence-24#char=0,111> ;
        itsrdf:taIdentRef     oke:Pablo_Neruda .

    oke:Pablo_Neruda  a  owl:Individual , dul:Person ;
        rdfs:label  "Pablo Neruda"@en ;
        owl:sameAs  dbpedia:Pablo_Neruda .

The OKE benchmark reader is implemented [here](../src/elevant/benchmark_readers/oke_benchmark_reader.py).

#### TSV IOB Format
The benchmark file should contain one line per token. Each line contains at least three tab-separated columns, where
- column 1 is the token
- column 2 is the entity reference or empty if the token does not belong to an entity or the entity is NIL. The
 entity reference can be from Wikidata, Wikipedia or DBpedia.
- column 3 is either "B" (beginning of a mention), "I" (continuation of a mention) or "O" (outside of a mention).
 Only the first character of this column is considered, the rest is ignored. Therefore, this column may also
 contain something like `B-person`.
Any additional columns are ignored. Documents are separated by an empty line.

Your benchmark file could for example look something like this:

    Off             O
    camping         O
    to              O
    Robinhoods      http://dbpedia.org/resource/Robin_Hood_Bay      B
    bay     http://dbpedia.org/resource/Robin_Hood_Bay      I
    In              O
    Jasmin       B
    .               O
    Good            O
    weekend         O

The TSV benchmark reader is implemented [here](../src/elevant/benchmark_readers/tsv_benchmark_reader.py).


#### Our JSONL Format

Our JSONL format is described in detail [here](our_jsonl_format.md).

## Writing a Custom Benchmark Reader
As an alternative to converting your benchmark into one of the formats mentioned above, you can write your own
 benchmark reader, such that you can use your benchmark file with the `add_benchmark.py` script directly.
 This requires the following steps. **Note: Make sure you perform the following steps outside of the docker container,
 otherwise your changes will be lost when exiting the container.**:

1) Implement a benchmark reader in `src/benchmark_readers/`, e.g. `MyFormatBenchmarkReader`, that inherits from
 `src.benchmark_readers.abstract_benchmark_reader.AbstractBenchmarkReader` and implement the abstract method
 `article_iterator`. This method should yield an iterator over `src.models.article.Article` objects where each
 `Article` object represents a benchmark article with at the very least some unique (within the benchmark) article ID,
 article title, article text and groundtruth labels. You can use the
 `src.benchmark_readers.simple_jsonl_benchmark_reader.SimpleJsonlBenchmarkReader` as a template for how to write a
 benchmark reader. Use the `src.utils.knowledge_base_mapper.KnowledgeBaseMapper`'s `get_wikidata_qid` method to
 convert Wikipedia or DBpedia benchmark entities to Wikidata. Use the
 `src.utils.nested_groundtruth_handler.NestedGroundtruthHandler`'s `assign_parent_and_child_ids` method if your
 benchmark may contain nested groundtruth labels.

2) Add your custom benchmark reader name to the `src.evaluation.benchmark.BenchmarkFormat` enum, e.g.
 `MY_FORMAT = "my_format"`.

3) Add an elif-branch in the `src.evaluation.benchmark_iterator.get_benchmark_iterator` function under the
 `if benchmark_file` branch , e.g.

        elif benchmark_format == BenchmarkFormat.MY_FORMAT.value:
            logger.info("Load mappings for My Format benchmark reader...")
            entity_db = EntityDatabase()
            entity_db.load_wikipedia_wikidata_mapping()
            entity_db.load_redirects()
            logger.info("-> Mappings loaded.")
            benchmark_iterator = MyFormatBenchmarkReader(entity_db, benchmark_file, custom_args)

    where `custom_args` are any custom arguments your benchmark reader's `__init__` method might take. You can omit
    this if your benchmark reader takes no custom arguments. Make sure to import `MyFormatBenchmarkReader` in
    `src.evaluation.benchmark_iterator`.

You can now add benchmarks in your format by running

    python3 add_benchmark.py <benchmark_name> -bfile <benchmark_file> -bformat my_format
