# Benchmarks

## MSNBC
*Cucerzan, 2007*

**Paper:** [Large-Scale Named Entity Disambiguation Based on Wikipedia Data](https://www.aclweb.org/anthology/D07-1074.pdf)

**Volume:** 20 articles with 756 mentions (of which 127 were non-recallable (there was no appropriate Wikipedia article corresponding to the mention)).
The dataset from the inofficial download has 739 mentions, 83 of which link to NIL -> 656 non-NIL mentions.

**Method:** They took the top 2 stories of the 10 MSNBC News categories (January 2, 2007), used them as input to their system and then perform a post-hoc evaluation of the disambiguations.
From the paper: "We defined a disambiguation to be correct if it represented the best possible Wikipedia article that would satisfy a user’s need for information and incorrect otherwise.
For example, the article *Viking program* is judged as correct for “Viking Landers”, for which there is no separate article in the Wikipedia collection".

**Inofficial Download** (data of [Ganea Paper](https://github.com/dalab/end2end_neural_el)): <https://drive.google.com/file/d/1OSKvIiXHVVaWUhQ1-fpvePTBQfgMT6Ps/view>

**Official Download** (broken link): <http://research.microsoft.com/users/silviu/WebAssistant/TestData>

**Problems:**
- No coreference

## ACE-2004
*Ratinov et al., 2011*

**Paper:** [Local and Global Algorithms for Disambiguation to Wikipedia](https://www.aclweb.org/anthology/P11-1138.pdf)

**Volume:** 36 articles with 257 mentions.

**Method:** Ratinov et al. took a subset of the ACE coreference dataset (Coreference is resolved and mentions and their types are given) and asked Amazon Mechanical Turk annotators to link the first nominal mention of each co-reference chain to Wikipedia if possible.
They then manually corrected the annotations.

**Inofficial Download** (data of [Ganea Paper](https://github.com/dalab/end2end_neural_el)): <https://drive.google.com/file/d/1OSKvIiXHVVaWUhQ1-fpvePTBQfgMT6Ps/view>

**Official Download** (in a weird format): <https://cogcomp.seas.upenn.edu/page/resource_view/4>

**Problems:**
- Only very few entities are annotated. Probably those, that form the first occurrence of an entity in a co-reference chain (and therefore only entities that are being referred to more than once).
- Mention boundaries are sometimes chosen in a very unintuitive way: e.g. *"D.C."* instead of *"Washington, D.C."*, *"Ministry of Defense"* instead of *"Iranian Ministry of Defense"*, *"Green Party"* instead of *"Florida Green Party"*, and then *"Ocean Spray Cranberries"* instead of *"Ocean Spray"* (with link to Company *"Ocean Spray"*)
- No coreference


## AIDA CoNLL

*Hoffart et al., 2011*

**Paper:** [Robust Disambiguation of Named Entities in Text](https://www.aclweb.org/anthology/D11-1072.pdf)

**Volume:** 1393 articles with 34,956 mentions all in all, 7,136 of which link to NIL -> 27,820 non-NIL mentions.
The dataset is split in train, dev and test set where the training dataset contains the first 946 articles, the dev set the next 216 articles and the test set the last 231 articles.

**Method:** The dataset is based on the CoNLL-2003 dataset for NER tagging with proper noun annotations for 1393 Reuters newswire articles.
Hoffart et al. hand-annotated these proper noun mentions with corresponding entities in YAGO2.
Each mention was disambiguated by two students and resolved by Hoffart et al. in case of conflict.

**Official Download**: <http://resources.mpi-inf.mpg.de/yago-naga/aida/download/aida-yago2-dataset.zip>

**Problems/Notes**
- No coreference
- Strong tendency towards sports articles.
The dev set for example with 216 articles overall contains ca. 100 articles about sports.
Certain kinds of entity linking problems occur more frequently in such articles, e.g. metonymy (*"Germany won against Brasil"* -> link the country or the team?).


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

