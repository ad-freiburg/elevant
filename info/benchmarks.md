# Benchmarks

## MSNBC
*Cucerzan, 2007*

**Paper:** [Large-Scale Named Entity Disambiguation Based on Wikipedia Data](https://www.aclweb.org/anthology/D07-1074.pdf)

**Volume:** \
*Original Dataset:* 20 articles with 756 mentions (of which 127 were linked to NIL since there was no appropriate Wikipedia article corresponding to the mention).
This is the same as the dataset from the GERBIL download below. This dataset contains 747 non-NIL mentions.
For 87 of these non-NIL mentions, the corresponding Wikipedia article can not be found (anymore).
Some of the labels are overlapping in the original dataset, e.g. [Frank [Blake]], [The [Home Depot]].\
*Updated Dataset:* A cleaned version of the MSNBC dataset with no-longer existing Wikipedia entities removed was released by [Guo & Barbosa](http://webdocs.cs.ualberta.ca/~denilson/files/publications/swj1511.pdf).
This version contains 739 mentions in total and 656 non-NIL mentions. At least 6 articles are different articles than the one in the original dataset, but revolve around the same topics.
These articles are 16417540, 16443053, 16447720, 16452612, 16455207, 3683270.

**Method:** They took the top 2 stories of the 10 MSNBC News categories (January 2, 2007), used them as input to their system and then perform a post-hoc evaluation of the disambiguations.
From the paper: "We defined a disambiguation to be correct if it represented the best possible Wikipedia article that would satisfy a user’s need for information and incorrect otherwise.
For example, the article *Viking program* is judged as correct for “Viking Landers”, for which there is no separate article in the Wikipedia collection".

**Download:**\
**Updated Version:** Cleaned version of the original dataset. The number of mentions and partly the text differs from the original version. <www.cs.ualberta.ca/~denilson/data/deos14_ualberta_experiments.tgz>

**Gerbil Version:** UTF-8 and XML problems from the [Wikification dataset](http://cogcomp.org/Data/ACL2011WikificationData.zip) (assumed to be close to the original) fixed without additional adjustments. <https://github.com/dice-group/gerbil/releases/download/v1.2.6/gerbil_data.zip>

**Original Dataset:** Broken link. <http://research.microsoft.com/users/silviu/WebAssistant/TestData>

**Problems/Notes:**
- No coreference
- For 87 non-NIL mentions, the corresponding Wikipedia article cannot be determined with our mapping.
This is partly because no corresponding Wikipedia article exists (anymore?), e.g. "*Daniel Venegas*".
Partly it's because of obvious spelling mistakes in the annotated entity names and urls, e.g. "*Los Angeles. California*"
Most (all?) of these entities are linked to NIL in the updated dataset or not included in the list of mentions.
- Some of the mentions in the original dataset overlap for no obvious reason.
E.g. for "*Frank Blake*" the entire mention is annotated, as well as "*Blake*". Both link to the same entity.
These overlapping mentions don't seem to be included in the updated version.

## ACE-2004
*Ratinov et al., 2011*

**Paper:** [Local and Global Algorithms for Disambiguation to Wikipedia](https://www.aclweb.org/anthology/P11-1138.pdf)

**Volume:**
57 articles with 306 mentions and 257 non-NIL mentions . Only 36 articles contain any (non-NIL-)mentions at all.

**Method:** Ratinov et al. took a subset of the ACE coreference dataset (Coreference is resolved and mentions and their types are given) and asked Amazon Mechanical Turk annotators to link the first nominal mention of each co-reference chain to Wikipedia if possible.
They then manually corrected the annotations.

**Download**\
**Updated Version (recommended):** Cleaned version of the original dataset. <https://dataverse.library.ualberta.ca/file.xhtml?fileId=6884&version=1.0>

**Gerbil Version:** UTF-8 and XML problems fixed without additional adjustments: <https://github.com/dice-group/gerbil/releases/download/v1.2.6/gerbil_data.zip>

**Original Dataset** (with invalid XML files): <http://cogcomp.org/Data/ACL2011WikificationData.zip>

**Problems/Notes:**
- Only very few entities are annotated. Probably those, that form the first occurrence of an entity in a co-reference chain (and therefore only entities that are being referred to more than once).
- Mention boundaries are sometimes chosen in a very unintuitive way: e.g. *"D.C."* instead of *"Washington, D.C."*, *"Ministry of Defense"* instead of *"Iranian Ministry of Defense"*, *"Green Party"* instead of *"Florida Green Party"*, and then *"Ocean Spray Cranberries"* instead of *"Ocean Spray"* (with link to Company *"Ocean Spray"*)
- No coreference
- The original dataset contains a couple of annotation problems/errors where the annotated Wikipedia title does not exist.
These cases are: *Seattke* instead of *Seattle*, *USS COLE (DDG-67)* instead of *USS Cole (DDG-67)* and *Lujaizui* to which no Wikipedia article exists (anymore?).
The first two problems have been fixed in the updated version of the dataset.
Additionally, two other errors have been fixed in the updated version: The mention *Bloomberg News* was in the original dataset linked to *Bloomberg Television*.
In the updated dataset this is linked to *Bloomberg News*.
The Wiki-link for *Portland* is (now?) a disambiguation page. In the updated dataset this mention links to *Portland, Oregon*.
These 4 adjustments are the only observed differences between the original dataset and the updated dataset.

## AIDA-CoNLL

*Hoffart et al., 2011*

**Paper:** [Robust Disambiguation of Named Entities in Text](https://www.aclweb.org/anthology/D11-1072.pdf)

**Volume:** 1393 articles with 34,956 mentions all in all, 7,136 of which link to NIL -> 27,820 non-NIL mentions.
The dataset is split in train, dev and test set where the training dataset contains the first 946 articles, the dev set the next 216 articles and the test set the last 231 articles.

**Method:** The dataset is based on the CoNLL-2003 dataset for NER tagging with proper noun annotations for 1393 Reuters newswire articles.
Hoffart et al. hand-annotated these proper noun mentions with corresponding entities in YAGO2.
Each mention was disambiguated by two students and resolved by Hoffart et al. in case of conflict.

**Official Download** (Annotations only): <http://resources.mpi-inf.mpg.de/yago-naga/aida/download/aida-yago2-dataset.zip>

**Inofficial CoNLL Download:** <https://data.deepai.org/conll2003.zip>
With this and the annotations, the complete dataset can be constructed using the java program that comes with the annotations.

**Problems/Notes**
- No coreference
- Strong tendency towards sports articles.
The dev set for example with 216 articles overall contains ca. 100 articles about sports.
Certain kinds of entity linking problems occur more frequently in such articles, e.g. metonymy (*"Germany won against Brasil"* -> link the country or the team?).


## KORE50
*Hoffart et al., 2012*

**Paper:** [KORE: Keyphrase Overlap Relatedness for Entity Disambiguation](https://dl.acm.org/doi/pdf/10.1145/2396761.2396832)

**Volume:** 50 difficult, hand-crafted test sentences from five domains: celebrities, music, business, sports, and politics.

**Official Download:** <https://www.mpi-inf.mpg.de/departments/databases-and-information-systems/research/ambiverse-nlu/aida/downloads>


## CWEB and WW
*Guo and Barbosa, 2016*

**Paper:** [Robust Named Entity Dsambiguation with Random Walks](http://webdocs.cs.ualberta.ca/~denilson/files/publications/swj1511.pdf)

**Motivation:** Previous benchmarks are too easy and biased towards popular entities.
Even baseline methods like using solely prior probabilities achieve a perfect result for 20% of all documents of AQUAINT and AIDA-CoNLL and even 31% for ACE2004.

**Method:** They took 2 publicly annotated corpora - Wikipedia and [ClueWeb12 FACC1](http://lemurproject.org/clueweb12/FACC1/).
The annotations of FACC1 were done automatically and are thus imperfect.
Precision is believed to be around 80-85%, Recall around 70-85%.
They don't mention where the annotations in Wikipedia come from, but a look at the dataset suggests they simply use hyperlinks, which means precision can't be evaluated on the dataset.
They only included documents in their benchmark, where their prior-probability baseline achieved an accuracy > 0.3. That is because they observed that the FACC1 annotations of documents where this accuracy was not achieved was very low.
They group documents by their average prior-probability accuracy and picked 40 random documents for each group. Their WNED WW dataset therefore consists of 320 Wikipedia articles.

**Download:** <https://dataverse.library.ualberta.ca/dataset.xhtml?persistentId=doi:10.7939/DVN/10968>

**Github:** <https://github.com/U-Alberta/wned>

**Problems:**
- Only few entities are annotated on the WW dataset (only Wikipedia hyperlinks) and on the CWEB dataset, annotations are imperfect.
- Other than having articles grouped by difficulty, their WW dataset does not seem to have any advantage over using Wikipedia with hyperlinks.
