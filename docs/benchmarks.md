# Benchmarks

This document gives an overview of the benchmarks that are included in ELEVANT. Additionally, this document contains a
 list of popular benchmarks that are not included in ELEVANT and the reasons why they have been excluded.

## Included Benchmarks

The following benchmarks are included in ELEVANT and can be used out of the box with the `link_benchmark_entities.py`
 script with the provided benchmark name.

### Wiki-Fair
*Bast et al., 2023*

**Paper:** [A Fair and In-Depth Evaluation of Existing End-to-End Entity Linking Systems](https://arxiv.org/abs/2305.14937)

**ELEVANT benchmark name:** `wiki-fair` and `wiki-fair-no-coref`

**Volume:** 80 random Wikipedia articles from a Wikipedia dump from 2020. In each article, 3 consecutive paragraphs were
 manually exhaustively annotated. The remainder of each article is left unannotated but kept in the benchmark to
 provide context for entity linkers.

**Method:** Bast et al. aimed at creating a benchmark that allows a fair comparison of different entity linkers.
 Unlike most entity linking benchmarks, the benchmark contains not only named entities, but also non-named entities.
 Which kinds of entities were annotated was determined by a [type whitelist](../small-data-files/whitelist_types.tsv).
 To ensure a fair comparison of different linkers, the benchmark includes alternative ground truth mentions in cases
 where it is unclear what the best ground truth annotation is. The benchmark also contains optional mentions, e.g.,
 for datetimes and quantities. Coreferences are annotated, too, but there also exists a version without coreferences.
 See https://github.com/ad-freiburg/entity-linking-annotation-guidelines for a comprehensive list of annotation
 guidelines.

**Official Download:** The benchmark should be used within ELEVANT, since ELEVANT automatically handles the
 evaluation of alternative or optional mentions as well as the evaluation of only the annotated parts of the benchmark.
 The benchmark can be found in this repository [here](../benchmarks/wiki-fair.benchmark.jsonl)
 ([or here](../benchmarks/wiki-fair-no-coref.benchmark.jsonl) for the version without coreferences).

### News-Fair
*Bast et al., 2023*

**Paper:** [A Fair and In-Depth Evaluation of Existing End-to-End Entity Linking Systems](https://arxiv.org/abs/2305.14937)

**ELEVANT benchmark name:** `news-fair` and `news-fair-no-coref`

**Volume:** 40 random articles from a news crawl. In each article, 3 consecutive paragraphs were manually exhaustively
 annotated. The remainder of each article is left unannotated but kept in the benchmark to provide context for entity
 linkers.

**Method:** Same as for [Wiki-Fair](#wiki-fair). 
 See https://github.com/ad-freiburg/entity-linking-annotation-guidelines for a comprehensive list of annotation
 guidelines.

**Official Download:** The benchmark should be used within ELEVANT, since ELEVANT automatically handles the
 evaluation of alternative or optional mentions as well as the evaluation of only the annotated parts of the benchmark.
 The benchmark can be found in this repository [here](../benchmarks/news-fair.benchmark.jsonl)
 ([or here](../benchmarks/news-fair-no-coref.benchmark.jsonl) for the version without coreferences).

### AIDA-CoNLL
*Hoffart et al., 2011*

**Paper:** [Robust Disambiguation of Named Entities in Text](https://www.aclweb.org/anthology/D11-1072.pdf)

**ELEVANT benchmark name:** `aida-conll-test` and `aida-conll-dev`

**Volume:** 1393 articles with 34,956 mentions all in all, 7,136 of which link to NIL. Thus, the dataset contains
 27,820 non-NIL mentions. The dataset is split into train, dev and test set where the training dataset contains the
 first 946 articles, the dev set the next 216 articles and the test set the last 231 articles.

**Method:** The dataset is based on the CoNLL-2003 dataset for NER tagging with proper noun annotations for 1393
 Reuters newswire articles. Hoffart et al. hand-annotated these proper noun mentions with corresponding entities in
 the YAGO2 knowledge base. Each mention was disambiguated by two students and resolved by Hoffart et al. in case of
 conflict.

**Official Download** (Annotations only): <http://resources.mpi-inf.mpg.de/yago-naga/aida/download/aida-yago2-dataset.zip>

**Inofficial CoNLL 2003 Download:** <https://data.deepai.org/conll2003.zip>.
 With this and the annotations, the complete dataset can be constructed using the java program that comes with the
 annotations.

**Notes**
- **IMPORTANT:** While the licence for the AIDA-CoNLL annotations permits redistribution, the licence for the Reuters
 texts does not. We therefore only include a version of the AIDA-CoNLL test and dev sets in which parts of the
 article texts are obscured. If you have your own (unobscured) copy of the dataset, you can however easily add it to
 ELEVANT as described in [Add a Benchmark](add_benchmark.md).
- Strong tendency towards sports articles. The dev set for example with 216 articles overall contains ca. 100
 articles about sports. Certain kinds of entity linking problems occur more frequently in such articles, e.g. 
 metonymy: *"Germany won against Brasil"* - Should the country be linked or the sports team?.


### KORE50
*Hoffart et al., 2012*

**Paper:** [KORE: Keyphrase Overlap Relatedness for Entity Disambiguation](https://dl.acm.org/doi/pdf/10.1145/2396761.2396832)

**ELEVANT benchmark name:** `kore50`

**Volume:** 50 difficult, hand-crafted test sentences from five domains: celebrities, music, business, sports, and
 politics.

**Method:** The dataset was hand-crafted by Hoffart et al.

**Official Download:** <https://www.mpi-inf.mpg.de/departments/databases-and-information-systems/research/ambiverse-nlu/aida/downloads>


### MSNBC
*Cucerzan, 2007*

**Paper:** [Large-Scale Named Entity Disambiguation Based on Wikipedia Data](https://www.aclweb.org/anthology/D07-1074.pdf)

**ELEVANT benchmark name:** `msnbc` and `msnbc-updated`

**Volume:** \
*Original Dataset:* According to the paper, the dataset contains 20 articles with 756 mentions. The dataset used by
 us (and GERBIL) contains 755 mentions of which 8 are linked to NIL. For ca. 87 of the non-NIL mentions, the
 corresponding Wikipedia article can not be found (anymore - this of course depends on the used Wikipedia version).
 Some of the labels in the original dataset are overlapping, e.g. `[Frank [Blake]]`, `[The [Home Depot]]`.

*Updated Dataset:* A cleaned version of the MSNBC dataset with no-longer existing Wikipedia entities removed was
 released by [Guo & Barbosa](http://webdocs.cs.ualberta.ca/~denilson/files/publications/swj1511.pdf). This version
 contains 739 mentions in total and 656 non-NIL mentions. For ca. 3 of the non-NIL mentions, the corresponding
 Wikipedia article can not be found (anymore - depending on the used Wikipedia version). At least 6 articles strongly
 differ from the corresponding articles in the original dataset, but revolve around the same topics. The IDs of the
 affected articles are 16417540, 16443053, 16447720, 16452612, 16455207 and 3683270.

**Method:** Cucerzan took the top 2 stories of the 10 MSNBC News categories (January 2, 2007), used them as input to
 his system and then performed a post-hoc evaluation of the disambiguations. From the paper: "We defined a
 disambiguation to be correct if it represented the best possible Wikipedia article that would satisfy a user’s need
 for information and incorrect otherwise. For example, the article *Viking program* is judged as correct for “Viking
 Landers”, for which there is no separate article in the Wikipedia collection".

**Download:**\
**Gerbil Version:** UTF-8 and XML problems from the
 [Wikification dataset](http://cogcomp.org/Data/ACL2011WikificationData.zip) (assumed to be close to the original)
 fixed without additional adjustments: <https://github.com/dice-group/gerbil/releases/download/v1.2.6/gerbil_data.zip>

**Original Dataset:** Broken link: <http://research.microsoft.com/users/silviu/WebAssistant/TestData>

**Updated Version:** Cleaned version of the original dataset. The number of mentions and partly the texts differs from
 the original version: <www.cs.ualberta.ca/~denilson/data/deos14_ualberta_experiments.tgz>

**Notes:**
- For ca. 87 non-NIL mentions, the corresponding Wikipedia article cannot be determined with ELEVANT's mappings. This is
 partly because no corresponding Wikipedia article exists (anymore?), e.g. "*Daniel Venegas*". Partly it's because of
 obvious spelling mistakes in the annotated entity names and urls, e.g. "*Los Angeles. California*" Most (all?) of
 these entities are linked to NIL in the updated dataset or not included in the list of mentions.
- Some of the mentions in the original dataset overlap for no obvious reason. E.g. for "*Frank Blake*" the entire
 mention is annotated, as well as "*Blake*". Both link to the same entity. These overlapping mentions don't seem to
 be included in the updated version.


### Reuters-128
*Röder et al., 2014*

**Paper:**
[N³ - A Collection of Datasets for Named Entity Recognition and Disambiguation in the NLP Interchange Format](http://www.lrec-conf.org/proceedings/lrec2014/pdf/856_Paper.pdf)

**ELEVANT benchmark name:** `reuters-128`

**Volume:** 128 articles from the Reuters-21578 corpus which contains economic news articles. Each article contains
 at least one named entity. The benchmark contains 880 entity mentions, 650 of which are non-NIL mentions. 27 originally
 non-NIL mentions could not be mapped to a Wikidata QID and are thus additional NIL-mentions in ELEVANT, such that in
 ELEVANT, the Reuters-128 benchmark has 623 non-NIL ground truth mentions.

**Method:** In a first step, entities were recognized using FOX (Ngomo et al., 2011). Domain experts then
 manually corrected recognition mistakes and two scientists annotated the named entities with a corresponding URI.

**Official Download:** <https://github.com/dice-group/n3-collection/blob/master/Reuters-128.ttl>

**Notes:**
- Demonyms are not annotated, e.g. in "2,600 Iraqis had been killed", "Iraqis" is not annotated.
- Adjectival modifiers and compounds are not annotated, e.g. in "Reagans decision was based on inaccurate data.",
 "Reagans" is not annotated and in "there are no plans to try to reduce the U.S. budget deficit", "U.S." is not
 annotated.
- Annotations are missing, e.g. in "Edelman was unsuccessful last year", "Edelman" is not annotated, even though it
 is annotated in previous sentences.


### Derczynski
*Derczynski et al., 2015*

**Paper:** [Analysis of named entity recognition and linking for tweets](https://www.sciencedirect.com/science/article/pii/S0306457314001034)

**ELEVANT benchmark name:** `derczynski`

**Volume:** 183 Tweets.

**Method:** Derczynski et al. asked 10 volunteer NLP experts to annotate tweets. The annotators could choose from a
 set of entity candidates as well as select "none of the above", "not an entity" or "cannot decide". Each entity
 mention was annotated by 3 volunteers. If an annotation decision was unclear, a fourth expert adjudicated on the
 annotation decision.

**GERBIL Download:** <https://github.com/dice-group/gerbil/releases/download/v1.2.6/gerbil_data.zip>


### OKE-2015
*Nuzzolese et al., 2015*

**Paper**:
[Open Knowledge Extraction Challenge](https://link.springer.com/chapter/10.1007/978-3-319-25518-7_1)

**ELEVANT benchmark name:** `oke-2015-train` and `oke-2015-eval`

**Volume:** Sentences from Wikipedia articles about the biographies of scholars. The dataset is split into training
 and evaluation dataset. The training dataset contains 95 sentences, the evaluation dataset contains 101 sentences.

**Method:** The sentences were manually annotated. The annotators considered as entity "any discourse referent (the
 actors and objects around which story unfolds), either named or anonymous that is an individual of one of the
 following DOLCE Ultra Lite classes, i.e., dul:Person, dul:Place, dul:Organization, and dul:Role.". Importantly,
 co-references to such entities are also considered as entities.

**Download:**\
**Official Download:** <https://github.com/anuzzolese/oke-challenge/>\
The folder `GoldStandard_sampleData/task1` contains the training set and the folder `evaluation-data/task1/` contains
 the evaluation dataset.

**GERBIL Download (identical to the official version):** <https://github.com/dice-group/gerbil/releases/download/v1.2.6
/gerbil_data.zip>

**Notes:**
- Some ground truth mention spans are not correct, e.g. in the training dataset in sentence #49, the span for the
 mention text "candidate" does not include the first letter and in sentence #62 the span for the mention text "civil
 engineering" is moved by one character to the right.
- Some annotations don't match the annotation guidelines, e.g. "civil engineering" is annotated even though it's
 neither a place, person, organization nor role.
- Inconsistent annotations: "Irish" in "Irish stone carver" (training set, sentence 50) is annotated (with "Irish
 people"), but "American" in "American poet" or "Canadian" in "Canadian musician" is not. Similarly, "street" is
 annotated, but "county" is not.
- The definition of an entity in this benchmark excludes things that are widely accepted as entities, such as languages.


### OKE-2016
*Nuzzolese et al., 2016*

**Paper**:
[The Second Open Knowledge Extraction Challenge](https://link.springer.com/book/10.1007/978-3-319-46565-4)

**ELEVANT benchmark name:** `oke-2016-train` and `oke-2016-eval`

**Volume:** As for OKE-2015, the datasets consist of sentences from Wikipedia articles about the biographies of
 scholars. The dataset is split into training and evaluation dataset. The training dataset consists of the 196
 sentences of the combined OKE-2015 training and evaluation dataset. The evaluation dataset contains 55 sentences.

**Method:** The sentences were manually annotated using a CrowdFlower task. Similarly to the OKE-2015 dataset, the
 annotators were asked to consider as entity "any discourse referent (the actors and objects around which a story
 unfolds), either named (e.g., Albert Einstein) or anonymous (e.g., a man)" of the types Person, Place, Organization
 or Role. As in the OKE-2015 dataset, co-references to such entities are also considered as entities.

**Download:**\
**Official Download:** <https://github.com/anuzzolese/oke-challenge-2016/>

**GERBIL Download (identical to the official version):** <https://github.com/dice-group/gerbil/releases/download/v1.2.6
/gerbil_data.zip>

**Notes**:
See notes for OKE-2015. However, in the OKE-2016 evaluation set, we could not find any span errors as reported for
 OKE-2015.

## Excluded Benchmarks

The following benchmarks are not included in ELEVANT for various reasons, mostly because we consider them as not
 beneficial for end-to-end entity linking evaluation. Most of them can however easily be added to ELEVANT by
 downloading the original benchmark from the given source and simply running the `add_benchmark.py` script with the
 appropriate `benchmark_file` and `benchmark_format` arguments.

### ACE 2004
**Not recommended for entity linking evaluation! See notes below.**

*Ratinov et al., 2011*

**Paper:** [Local and Global Algorithms for Disambiguation to Wikipedia](https://www.aclweb.org/anthology/P11-1138.pdf)

**Volume:** 57 articles with 306 mentions and 257 non-NIL mentions. Only 36 articles contain any (non-NIL-)mentions
 at all.

**Method:** Ratinov et al. took a subset of the ACE coreference dataset (Coreference is resolved and mentions and
 their types are given) and asked Amazon Mechanical Turk annotators to link the first nominal mention of each
 coreference chain to Wikipedia if possible. They then manually corrected the annotations.

**Download**\
**Updated Version** (cleaned version of the original dataset):
<https://dataverse.library.ualberta.ca/file.xhtml?fileId=6884&version=1.0>

**Gerbil Version** (UTF-8 and XML problems fixed without additional adjustments):
<https://github.com/dice-group/gerbil/releases/download/v1.2.6/gerbil_data.zip>

**Original Dataset** (with invalid XML files): <http://cogcomp.org/Data/ACL2011WikificationData.zip>

**Notes:**
- Only very few entities are annotated. Probably those, that form the first occurrence of an entity in a coreference
 chain (and therefore only entities that are being referred to more than once). The dataset can therefore not be used
 to reasonably compute precision or F1 score unless ground truth mention spans are given.
- Mention boundaries are sometimes chosen in a very unintuitive way: e.g. *"D.C."* instead of *"Washington, D.C."*,
 *"Ministry of Defense"* instead of *"Iranian Ministry of Defense"*, *"Green Party"* instead of
 *"Florida Green Party"*, and then *"Ocean Spray Cranberries"* instead of *"Ocean Spray"* (with link to Company
 *"Ocean Spray"*)


### AQUAINT
**Not recommended for entity linking evaluation! See notes below.**

*Milne and Witten, 2008*

**Paper:** [Learning to Link with Wikipedia](https://dl.acm.org/doi/pdf/10.1145/1458082.1458150)

**Volume:** 50 short (250 - 300 words) newswire articles from the Associated Press.

**Method:** The documents are a subset from the AQUAINT text corpus which contains newswire articles from the Xinhua
 News Service, the New York Times, and the Associated Press. 50 articles from the Associated Press were randomly
 selected, but the selection was limited to short articles (250 - 300 words). No information is given in the original
 paper about the annotation process.

**Inofficial Download, e.g.:**
<https://github.com/kermitt2/entity-fishing/tree/6364840573e7766feaa93458b386d5ba6aec9cdc/data/corpus/corpus-long/aquaint>

**Notes:**
- Only one occurrence of an entity seems to be annotated in each article (and not necessarily the first one).
- The benchmark annotation is very inconsistent, for example obvious mentions like "Iraq" and "Hungary" are not
 annotated in some articles.
- Lowercase mentions are sometimes annotated, but here too, the annotation is very inconsistent and it is unclear why
 a certain mention is annotated and another is not. E.g. "capillaries" is annotated, but "veins" in the same article is
 not.


### RSS-500
**Not recommended for entity linking evaluation! See notes below.**

*Röder et al., 2014*

**Paper:**
[N³ - A Collection of Datasets for Named Entity Recognition and Disambiguation in the NLP Interchange Format](http://www.lrec-conf.org/proceedings/lrec2014/pdf/856_Paper.pdf)

**Volume:** 500 random sentences from a set of RSS feeds including all major worldwide newspapers. From the paper:
 "These sentences were a subset of those which contained a natural language representation of a formal relation, like
 “... , who was born in ... ” for dpo:birthPlace [...]. The relations had to occur more than 5 times in the 1% corpus."
 The dataset contains 1000 mentions, of which 524 are non-NIL mentions and 476 are NIL-mentions.

*Wikidata version:*
 Delpeuch converted the DBpedia annotations from the original RSS-500 dataset to Wikidata as described in the paper
 [OpenTapioca: Lightweight Entity Linking for Wikidata](http://ceur-ws.org/Vol-2773/paper-02.pdf). During this process,
 63 of the original NIL-mentions were linked to a Wikidata entity and some of these were split into several mentions
 (e.g. "CBS NFL" into the mentions "CBS" and "NFL"), amounting to 1002 mentions all in all, 588 of which are
 non-NIL mentions.

**Method:** A researcher manually annotated the sentences.

**Download:** <https://github.com/dice-group/n3-collection/blob/master/RSS-500.ttl>

**Download Wikidata version:** <https://github.com/wetneb/opentapioca/blob/master/data/RSS-500_wd.ttl>

**Notes:**
- In each sentence, exactly 2 entity references are marked as ground truth entities. This means that often,
  obvious entity references mentions, e.g. "Bill Clinton" or "Afghanistan" are not included in the ground truth. The
  dataset can therefore not be used to compute precision or F1 score unless ground truth mention spans are given.
- Some sentences (at least one) appear twice in the benchmark, but with different ground truth mentions, e.g.:
 "FLAGSTAFF , Ariz. -- No sooner had six-time Pro Bowl receiver Larry Fitzgerald arrived in Uganda in July on a
  humanitarian mission than former president Bill Clinton hit him with the question : Does n't matter who is
  quarterback is , Larry Fitzgerald still finds a way to make big plays for the Cardinals ."
  In one occurrence of this sentence, only the spans "Larry Fitzgerald" and "Uganda" are marked as ground truth
  entities, while in the other occurrence only the spans "Bowl" and "Larry Fitzgerald" are marked as ground truth
  entities.
- Mention spans are sometimes not intuitive, e.g. in the phrase "Pro Bowl receiver Larry Fitzgerald", "Bowl" is
  linked to the entity "Pro Bowl"


### DBPedia Spotlight
**Not recommended for entity linking evaluation! See notes below.**

*Mendes et al., 2011*

**Paper:**
[DBpedia Spotlight: Shedding Light on the Web of Documents](https://dl.acm.org/doi/pdf/10.1145/2063518.2063519)

**Volume:** In the paper, they state that the test set consists of 35 paragraphs from NY Times articles from 8
 different categories. The entire dataset downloadable e.g. via GERBIL consists of 58 individual sentences.

**Method:** From the paper: "[T]he annotators were asked to add links to DBpedia resources for all phrases that would
 add information to the provided text." and "In order to construct a gold standard, each evaluator first
 independently annotated the corpus, after which they met and agreed upon the ground truth evaluation choices. The
 ratio of annotated to not-annotated tokens was 33%."

**GERBIL Download:** <https://github.com/dice-group/gerbil/releases/download/v1.2.6/gerbil_data.zip>

**Notes:**
- Some ground truth labels are overlapping, e.g. `[[Turku]'s harbour]`
- The annotation decisions seem arbitrary. The benchmark contains annotations for words like "curved", "idea", or
 "house". On the other hand, phrases like "story", "Russian" or "Web language" are not annotated (even though "Web"
  and "Web pages" are).
- 75% of annotations are non-named entities.


### WNED-CWEB
**Not recommended for entity linking evaluation! See notes below.**

*Guo and Barbosa, 2018*

**Paper:**
[Robust Named Entity Disambiguation with Random Walks](http://webdocs.cs.ualberta.ca/~denilson/files/publications/swj1511.pdf)

**Volume:** The dataset consists of 320 articles from the annotated ClueWeb12 (FACC1) dataset.

**Method:** The FACC1 dataset was annotated automatically at Google Research. The annotators aimed for high precision
 at the cost of a lower recall. According to the [project website](http://lemurproject.org/clueweb12/FACC1/),
 precision is believed to be around 80-85% and recall around 70-85%. Guo and Barbosa linked all documents using a
 simple baseline and grouped the documents by the resulting average accuracy. They randomly selected 40 documents for
 each accuracy bracket (for accuracies from 0.3 to 1.0).

**Download:** <https://borealisdata.ca/file.xhtml?fileId=219564&version=1.0>

**Notes:**
- The annotation was done automatically and is thus inherently erroneous.


### WNED-WIKI
**Not recommended for entity linking evaluation! See notes below.**

*Guo and Barbosa, 2018*

**Paper:**
[Robust Named Entity Disambiguation with Random Walks](http://webdocs.cs.ualberta.ca/~denilson/files/publications/swj1511.pdf)

**Volume:** The dataset consists of 345 articles from Wikipedia.

**Method:** Guo and Barbosa linked all documents in a Wikipedia dump from 2013 using a simple baseline and grouped
 the documents by the resulting average accuracy (apparently using Wikipedia hyperlinks as ground truth). They randomly
 selected 40 documents for each accuracy bracket (for accuracies from 0.3 to 1.0).

**Download:** <https://borealisdata.ca/file.xhtml?fileId=219564&version=1.0>

**Notes:**
- Wikipedia hyperlinks, which serve as ground truth labels in this benchmark, are incomplete since Wikipedia
 contributors are encouraged to omit hyperlinks if entities are very well known and only the first occurrence of an
 entity is linked in an article. The dataset can therefore not be used to reasonably compute precision or F1 score
 unless ground truth mention spans are given.
