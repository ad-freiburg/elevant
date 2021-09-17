# Systems

### WEXEA: Wikipedia EXhaustive Entity Annotation
*Strobl et al., 2020*

**Paper:** <https://www.aclweb.org/anthology/2020.lrec-1.240.pdf>

**Code:** <https://github.com/mjstrobl/WEXEA>

**Objective:**
Strobl et al. introduce a system to exhaustively annotate a Wikipedia corpus with entity annotations.

**Approach:**
The first step in their approach is to create the following dictionaries:
- Redirects dictionary
- Alias dictionary: aliases are extracted from anchor texts of hyperlinks referring to an article. This dictionary might overlap with the redirects dictionary. Only aliases that start with a capital letter are kept. alias-entity links that occur only once are ignored.
- Disambiguation page dictionary: this often adds information about the type of an entity (e.g. *human* or *geo*)
- Stub articles, which are ignored: These are very short articles with presumably lower quality.
- Frequent sentence starter words: These words should not be considered for starting a mention at the beginning of a sentence
- List of persons from the Yago KB to figure out whether an article refers to a person
- Most popular entities: Very popular entities such as "World War II" are often not linked in an article. The dictionary is used such that these entities can be linked to mentions with high confidence without having a corresponding hyperlink in the article.
- Given Name dictionary extracted from Wikipedia pages for categories "Given names" etc.

An article is then linked in the following manner:
1) Keep hyperlinks in the article if the corresponding article entity is mostly starting with a capital letter (considering most frequent anchor text of incoming links of an article)
2) Link the bold title spans in the first paragraph of an article to the article entity
3) After a link is seen, search through the remaining article for the name or aliases (link anchor texts starting with a capital letter that appear more than once, redirects, first and last word of the entity if it's a person) of the linked entity and annotate them with the corresponding entity.
4) Search for acronyms in the article: For a string "Aaaaa Bbbbb Cccc (ABC)" if the matching string before the brackets was linked to an entity, the acronym is linked to that same entity.
5) Search for mentions by looking for words starting with a capital letter (except for frequent sentence starter words). Combine pairs of mentions occuring next to each other or, if combined, are part of the alias dictionary or have one of the following words between the pair of mentions: ("de", "of", "von", "van").
6) Such mentions are resolved as follows:
	- If a mention matches an alias of the article entity and does not exactly match any other entity, link to the article entity.
	- If the mention matches the 10,000 most popular entities in Wikipedia, link to that entity
	- If the mention matches a disambiguation page and one of the previously linked entities appears in this list, link to this entity
	- If the mention matches an alias from the general alias dictionary, it is linked to the most frequently linked entity given the mention
7) Resolve conflicts (more than one potential candidate for a mention using the previous rules) in the following manner:
	- If all candidates correspond to persons, the person that was linked with the mention more often (within the article?) is linked
	- previously linked entity exact name > article entity alias > previously linked entity alias
	- Apply Gupta et al.'s Neural EL on the mention given the computed candidate set
8) If no entity can be found for a mention, annotate it with unknown entity or with a disambiguation page if one matches.

They additionally apply a rule based coreference resolution system (for both pronouns and "the" + entity type coreferences).
They use the most recent entity that matches the coreference pronoun or type as referenced entity.
Pronominal and nominal mentions are only linked if the mention does not start with a capital letter.
"it", "this" or "that" are never linked.


**Evaluation:**
Corpora statistics compared to an unprocessed Wikipedia corpus with hyperlinks.

**Notes:**
- *"it"* is not linked by their coreference system
- Mentions are sometimes linked to Wikipedia Disambiguation Pages, especially demonym mentions like `American`, `German`, ...: `A cover by American [Q463180] country music group` (Sad Eyes)
- Mention of the article entity is not linked correctly: `Sad Eyes [Q4048940]" is one of just a few non-disco` --> Why?
- Obvious mention not linked: `Ballbank is an area in the` --> smaller entity db? But entities are extracted from Wikipedia...
- Seems like their common-sentence-starter filter to improve their NER component often causes problems: `The Samples` --> only Samples is linked; `A.R. "Archie" Shaw` --> *R.* is linked and *Shaw*.
- Replacing their coreference linker with our entity coreference linker improves the F1 score on our benchmark by 3% with a very small decrease in precision (-1%) and a huge increase (+7%) in Recall.

**Noteworthy error categories:**
- **Undetected:** 118 (vs. 96 neural_el.ltl.entity). This is the highest value for the approaches that use both a normal linker and a link-linker.
- **Specificity:** 36 (vs. 22 neural_el.ltl.entity). This is the highest value for the approaches that use a link-linker.
The order is xyz.none.xyz > wexea.wexea.xyz > xyz.ltl.xyz
- **Rare:** 43 (vs. 19 neural_el.ltl.entity). This is the highest value for the approaches that use a link-linker and also worse than Tagme.
- **Hyperlinks:** 51 (vs. 27 for all LTL approaches). Apparently WEXEA is much worse at using existing hyperlinks than LTL.
- **Partial Name:** 17 (vs. 19 neural_el.ltl.entity). Best result over all, but very small difference to LTL approaches.


### Entity Linking via Joint Encoding of Types, Descriptions, and Context
*Gupta et al., 2017*

**Paper:** <https://www.aclweb.org/anthology/D17-1284.pdf>

**Code:** <https://github.com/nitishgupta/neural-el>

**Objective:** A system that incorporates various information aspects of an entity in order to make an accurate linking decision.
The system should work on texts from different domains without domain specific training data.

**Result:** Their system learns a unified dense representation for each entity using multiple sources of information (description, contexts, fine-grained types).
The resulting system (EL only) performs competitively over various benchmarks, sometimes outperforming SotA systems without requiring domain-specific training.

**Approach:**
They introduce encoders for the different sources of information and encourage the entity embedding to be similar to all the encoded representations.
1) Encoding the **mention context (C)**: *"In 1932, India played their first match in England"*.
India should be linked to *India_cricket_team*.
In order to recognize that India is not a country but a sports team, local context needs to be taken into account (*"played"*, *"match"*).
In order to identify the sport (cricket), document context needs to be taken into account.
At the same time, semantics need to be considered in the context representation to realize that *"England"* should not be linked to a sports team but to the country.
For the **local-context representation** they use two different LSTMs to encode the context to the left and to the right of the mention separately.
Both encodings are concatenated and fed into a single-layer FF network to produce the local-context vector.
For the **document-context representation** they use a bag-of-mention-surfaces representation of the document.
The vocabulary consists of all mention surface forms seen in the training data.
This document-context representation is supposed to capture entity coherence information in the document.
The sparse vector of bag-of-mention-surfaces is fed into a single-layer FF network which yields the document-context vector.
The local- and document-context vectors are concatenated and passed through a single-layer FF network to obtain the mention context vector v_m.
2) Encoding the **entity description (D)**: Given the Wikipedia entity description (in their evaluation they use the first 100 tokens of the corresponding Wikipedia article) as sequence of words where each word is embedded as a d_w dimensional vector, a CNN is used to obtain the entity description vector.
They use 300-dimensional GloVe vectors as word embeddings in their evaluation.
3) **Encoding fine-grained types (E)**: Each entity is assigned multiple types. Freebase types are extracted for each entity and mapped to 112 types from a type set introduced by Ling and Weld (2012).
They compute the probability of type t being relevant to entity e as sigmoid(v_t * v_e). Entity and type representations are jointly learned.
4) **Type-aware context representation (T)**: They introduce an objective between every mention-context vector and type vector if the type belongs to the type set of the entity that the mention refers to.

They jointly learn the entity representations and encoder parameters. In their evaluation they use a Wikipedia dump from 2016 as training data with existing hyperlinks as labels.

Given a document with marked mentions, they first retrieve a set of the top 30 candidates and their prior scores using Cross-Wikis.
They then use their mention-context encoder to estimate the semantic similarity of each mention with the embedding of the candidate and combine both results.

**Evaluation:**
They compare their system to 5 different existing systems: Plato (Lazic et al., 2015), Wikifier (Ratinov et al., 2011), Vinculum (Ling et al., 2015), AIDA (Hoffart et al., 2011) and BerkCNN (Francis-Landau et al., 2016).
They evaluate these approaches over 4 different datasets: CoNLL-YAGO, ACE2004, ACE2005 and Wikipedia (Ratinov et al., 2011).
Their system outperforms AIDA, Wikifier and Vinculum on ACE2004 (BerkCNN not evaluated).
The full BerkCNN model outperforms their system on CoNLL and ACE2005 but is significantly outperformed on Wikipedia.

**Notes:**
- Slightly worse F1 score than Explosion on our benchmark: 37.52% (vs. 38.47%).
But interestingly with LTL + Entity better results than Explosion + LTL + Entity: F1 score of 74.66% (vs. 72.21%).

**Noteworthy error categories:**
- **Undetected:** 255 (vs. 218 for Explosion). This is the highest value for Undetected over all our systems.
- **Partial Name:** 92 (vs. 85 for Explosion). This is the highest value for Partial Name over all our systems.
- **Rare:** 75 (vs. 77 for Explosion). The other only-linker-systems perform better in this category.
- Best results for **Demonym** (by a large margin), **Abstraction** (by a pretty big margin) and **Specificity**. 


### TAGME: On-the-fly Annotation of Short Text Fragments(by Wikipedia Entities)
*Ferragina & Scaiella, 2010*

**Paper:** https://dl.acm.org/doi/pdf/10.1145/1871437.1871689

**Code:** https://github.com/marcocor/tagme-python

**Objective:**
Entity disambiguation for very short texts like tweets, snippets of search engine results, items from a newsfeed, ...

**Approach:**
They use Wikipedia link anchor texts as mentions.
In order to disambiguate a mention m, they compute a vote of each other mention m' in the text as the average relatedness between the candidate entity c that m might refer to and all candidate entities c' that m' might refer to.
The relatedness is weighted with the prior probability of p(c'|m') (computed using Wikipedia link anchor frequencies, i.e. how often does this anchor link to the specific entity).
The sum of the votes yields the total score rel_m(c) for a given mention and its candidate entity.
They test two different ranking algorithms and settle on Disambiguation by Threshold (DT).
DT computes the top-n best candidates for a mention according to their total score and then settles on the candidate that has the highest prior probability (commonness).
To achieve a high disambiguation speed, candidate entities are pruned by discarding candidates with a prior probability smaller than a threshold t.
Mentions are pruned using a scoring function that uses the link probability of an anchor (how often is the anchor text a link in Wikipedia) and the coherence of its disambiguation with respect to the other disambiguations in the text.
The idea is to keep all mentions where the link probability is high or the linked entity is coherent with the other linked entities.
They implement two different methods for this pruning, AVG (average of link probability and coherence) and LR (linear combination of the two scores trained via linear regression), each of which produce a score for the disambiguation.
If the score is lower than a certain threshold, then the mention is linked to NIL.
This threshold allows to balance recall and precision.

**Noteworthy error categories:**
- **Abstract:** with 206 abstraction errors, TAGME makes ten times more abstraction errors than almost all other base linker (xyz.none.none) approaches (except for the prior probability baseline with 29 abstraction errors).
At the same time, TAGME does not make (significantly) less UNDETECTED errors than Ambiverse, Explosion or the baseline.
Setting the rho-threshold to 0.3 reduces the abstraction errors to 78, but increases the UNDETECTED errors to 284 which is significantly more than all other base linker approaches.
- **Demonym:** TAGME makes more demonym errors than Neural-EL, Ambiverse, Explosion and the baseline by a large margin.
- ...


### Ambiverse

Ambiverse provides a system for NER, KnowNER, and a system for NEL, AIDA.
KnowNER uses a linear chain CRF that is fed with features extracted from a knowledge base or corpus with annotated entities.
They use four distinct features: 1) A binary indicator for each token that indicates whether the token is part of a sequence that occurs in a type-specific (?) gazetteer. 2) The probability of a token being linked to a Wikipedia article. 3) the probability of a token belonging to a given type. 4) The token type position (i.e. the position of a token within a mention, given its type?)
(The referenced paper for the NER component introduces 4 different systems, but it seems most likely that the described "Knowledge-Base-Based Knowledge" system is meant with "KnowNER")
AIDA performs entity disambiguation by combining information from three different sources:
the prior probability of an entity being mentioned in a text, the similarity between the context of a mention and a candidate entity and the coherence among candidate entities of all mentions.
AIDA is therefore a global entity linking system.

**Notes:**

**Noteworthy error categories:**
-


### Relational Inference for Wikification
*Cheng and Roth, 2013*

**Paper:** <https://aclanthology.org/D13-1184.pdf>

**Code:** <https://cogcomp.seas.upenn.edu/page/download_view/Wikifier>

**Objective:**

**Approach:**
Cheng and Roth argue that it is necessary to incorporate background knowledge to successfully disambiguate mentions in certain contexts and to understand the relation between mentions in a context.
In their paper, they focus on eliminating entity linking errors due to natural language constructs that are obvious to a human reader (e.g. in "As Mubarak, the wife of deposed Egyptian President Hosni Mubarak got older, her influence..." linking both Mubarak mentions to the most linked page Hosni Mubarak).
They approach this task by extracting textual relations between mentions (e.g. possessive, coreference, apposition, ...) and combining them with relations retrieved from a knowledge base (more precisely, they combine the confidence scores of both extracted relations).
They extract syntactico-semantic relations using (existing?) high precision classifiers.
They extract coreference relations by clustering named entities that share tokens or are acronyms of each other when there is no ambiguity (E.g. "Al Goldman, chief market strategist at A.G. Edwards said ... Goldman told us that ..." if there is no other longer mention containing Goldman in the document, like Goldman Sachs). They then use a voting algorithm to generate candidates for the cluster.
They also make use of nominal mentions as in "Dorothy Byrne, a state coordinator for the Florida Green Party". They use TF-IDF cosine similarity between the nominal mention and the lexical context of the candidate page, head word attributes and entity relation (i.e. between Dorothy Byrne and Florida Green Party) to find an entity candidates that are coherent with the nominal description.
