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
