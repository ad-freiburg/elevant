# Add a Benchmark
You can easily add a benchmark if you have a benchmark file that is in the JSONL format we use, in the common NLP
 Interchange Format (NIF) or in the IOB-based format used by Hoffart et al. for their AIDA/CoNLL benchmark. Benchmarks
 in other formats have to be converted into one of these formats first.

To add a benchmark, simply run

    python3 create_benchmark_labels.py -name <benchmark_name> -bfile <benchmark_file> -bformat <nif|ours|aida-conll>

This converts the `<benchmark_file>` into our JSONL format (if it is not in this format already), annotates ground
 truth labels with their Wikidata label and Wikidata types as given in
 `<data_directory>/wikidata_mappings/entity-types.tsv` and writes the result to the file
 `benchmarks/benchmark_labels_<benchmark_name>.jsonl`.


## Benchmark Formats

This section describes the three file formats that can be used as input to the `create_benchmark_labels.py` script.

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
- entity identifiers can be either from Wikidata or from Wikipedia
- `<benchmark_file>` can be the path to a single NIF file that contains all benchmark articles or the path to a
 directory that contains multiple such NIF files
 
The NIF benchmark reader is implemented [here](../src/benchmark_readers/nif_benchmark_reader.py).

#### AIDA/CoNLL IOB format
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
- column 5 is the corresponding Wikipedia URL of the entity.
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

The AIDA-CoNLL benchmark reader is implemented [here](../src/benchmark_readers/aida_conll_benchmark_reader.py).

#### Our JSONL format

Our JSONL format is described in detail [here](our_jsonl_format.md).