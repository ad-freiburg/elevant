# Included Benchmarks

This document gives an overview of the benchmarks that are included in ELEVANT.

## AIDA-CoNLL
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

## KORE50
*Hoffart et al., 2012*

**Paper:** [KORE: Keyphrase Overlap Relatedness for Entity Disambiguation](https://dl.acm.org/doi/pdf/10.1145/2396761.2396832)

**ELEVANT benchmark name:** `kore50`

**Volume:** 50 difficult, hand-crafted test sentences from five domains: celebrities, music, business, sports, and
 politics.

**Method:** The dataset was hand-crafted by Hoffart et al.

**Official Download:** <https://www.mpi-inf.mpg.de/departments/databases-and-information-systems/research/ambiverse-nlu/aida/downloads>

## MSNBC
*Cucerzan, 2007*

**Paper:** [Large-Scale Named Entity Disambiguation Based on Wikipedia Data](https://www.aclweb.org/anthology/D07-1074.pdf)

**ELEVANT benchmark name:** `msnbc` and `msnbc-updated`

**Volume:** \
*Original Dataset:* According to the paper, the dataset contains 20 articles with 756 mentions. The dataset used by
 us (and GERBIL) contains 755 mentions of which 8 are linked to NIL. For ca. 87 of the non-NIL mentions, the
 corresponding Wikipedia article can not be found (anymore. This of course depends on the used Wikipedia version).
 Some of the labels in the original dataset are overlapping, e.g. `[Frank [Blake]]`, `[The [Home Depot]]`.

*Updated Dataset:* A cleaned version of the MSNBC dataset with no-longer existing Wikipedia entities removed was
 released by [Guo & Barbosa](http://webdocs.cs.ualberta.ca/~denilson/files/publications/swj1511.pdf). This version
 contains 739 mentions in total and 656 non-NIL mentions. For ca. 3 of the non-NIL mentions, the corresponding
 Wikipedia article can not be found (anymore, depending on the used Wikipedia version). At least 6 articles strongly
 differ from the corresponding articles in the original dataset, but revolve around the same topics. The IDs of the
 affected articles are 16417540, 16443053, 16447720, 16452612, 16455207 and 3683270.

**Method:** Cucerzan took the top 2 stories of the 10 MSNBC News categories (January 2, 2007), used them as input to
 his system and then perform a post-hoc evaluation of the disambiguations. From the paper: "We defined a
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

## DBPedia Spotlight
*Mendes et al., 2011*

**Paper:**
[DBpedia Spotlight: Shedding Light on the Web of Documents](https://dl.acm.org/doi/pdf/10.1145/2063518.2063519)

**ELEVANT benchmark name:** `spotlight`

**Volume:** In the paper, they state that the test set consists of 35 paragraphs from NY Times articles from 8
 different categories. The entire dataset downloadable e.g. via GERBIL consists of 58 articles.

**Method:** From the paper: "[T]he annotators were asked to add links to DBpedia resources for all phrases that would
 add information to the provided text." and "In order to construct a gold standard, each evaluator first
 independently annotated the corpus, after which they met and agreed upon the ground truth evaluation choices. The
 ratio of annotated to not-annotated tokens was 33%."

**GERBIL Download:** <https://github.com/dice-group/gerbil/releases/download/v1.2.6/gerbil_data.zip>

**Notes:**
- Some ground truth labels are overlapping, e.g. `[[Turku]'s harbour]`