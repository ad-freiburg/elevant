# Analysis

### Fine-Grained Evaluation for Entity Linking
*Rosales-Mendez et al., 2019*

**Paper:** <https://www.aclweb.org/anthology/D19-1066.pdf>

(**More detailed paper:** <http://aidanhogan.com/docs/fine-grained-el.pdf>)

**Objective:**
Fair comparison of different Entity Linking systems considering the lack of a common definition of the Entity Linking task.

Rosales-Mendez et al. first sent a questionaire to authors of Entity Linking papers to find out where there is consensus and where disagreement about Entity Linking decisions (which kind of mentions should be linked to which entities).
The questionaire aims to investigate 6 different aspects of linking decisions:
1) Entity types: Should types not included in the MUC-6 definition be linked, such as for example the documentary "Living with Michael Jackson"? The consensus is yes.
2) Overlapping mentions: Should mentions inside other mentions be annotated, e.g. "Michael Jackson" in "Living with Michael Jackson"? 3/4 of respondents allow overlapping mentions.
3) Common entities: Should common nouns be annotated, e.g. "documentary"? Most respondents do not link common entities (> 2/3).
4) Parts of Speech: Should only nouns be annotated or also other parts of speech? The consensus is, that EL should focus on nouns, however pronouns were also considered for linking by 40% of respondents.
5) Mention types: Should complex types of mentions such as pronouns or descriptive noun phrases like "he and his four siblings" be annotated? No agreement between respondents.
6) Link types: Should mentions link to the explicitly named entity, e.g. in metonomy cases such as "Moscow" for the "government of Russia"? Most agree to link demonyms to the country and "Moscow" to the "government of Russia".

Rosales-Mendez et al. introduce a fine-grained categorization scheme for annotations.
The scheme has 4 dimensions:
1) Base Form:Proper noun with subcategories full name, short name, extended name and alias, numeric/temporal, common form (common words such as "documentary", noun phrases like "he and his four siblings") and pro-form (pronouns)
2) Part of Speech: Noun phrase (singular, plural), adjective, verb, adverb
3) Overlap: None, Maximal ("New York City Police Museum"), Intermediate ("New York City Police" in "New York City Police Museum"), Minimal ("New York" in "New York City Police Museum")
4) Reference: Direct ("M. Jackson", "King of Pop"), Anaphoric (reference to an antecedent or postcedent for pronouns), Metaphoric, Metonymic, Related (only a near-synonym, hypernym or hyponym is available in the KB), Descriptive ("Fiji's capital", "his father")

The authors then re-annotate three existing benchmarks (ACE2004, KORE50 and VoxEL) using their proposed annotation scheme - each annotation is assigned exactly one leaf-node of each category.
They also label some mentions with multiple alternatives (e.g. metonymy or demonym cases).

They then perform a fine-grained evaluation of 6 different systems (Babelfy, TagMe, DBpedia Spotlight, AIDA and FREME), computing precision, recall and f1 score for each leaf-node for each system.
They conclude that this might be a too fine-grained evaluation to compare different systems and introduce a fuzzy recall and F1 metric.
For this they define a membership function µ which assigns each ground truth annotation a membership degree between 0 and 1 where a higher value places more importance on achieving the annotations.
Annotations with consensus > 0.9 in their questionaire are assigned a membership degree of 1 (Proper Forms, Noun Phrases, No Overlap and Direct Reference).
All other annotations get a constant membership degree of alpha.
For a set of ground truth annotations G and a set of predicted links S, fuzzy recall is then defined as R* = sum_{a in S} µ(a) / sum_{a in G} µ(a). 
They find that the results distinguish the systems that link common entities (Babelfy (relaxed) and TagME) from those that do not.
The systems that link common entities outperform other systems when the definition of EL annotations is relaxed and perform worse for stricter definitions of EL annotations.

### Evaluating Entity Linking with Wikipedia
*Hachey et al., 2013*

**Paper:** <https://www.sciencedirect.com/science/article/pii/S0004370212000446>

**Objective:**
Evaluate different aspects of entity linking such as candidate generation, akronym handling or co-reference resolution to find out which components have the biggest impact on entity linking performance.

Hachey et al. reimplement three state of the art entity linking systems.
A primary goal is to independently analyze the candidate generation and the candidate ranking step.
Their conclusion is that candidate generation accounts for more variation in performance between systems than candidate ranking.
Additionally they find that co-reference resolution and akronym detection have a larger impact than candidate ranking

Hachey et al. discuss various datasets, among them the MSNBC and TAC datasets.
They differentiate between cross-document coreference, wikification and named entity linking and use named entity disambiguation as a term to describe all three of these tasks.
According to them, the difference between wikification and named entity linking is that wikification includes concept linking and does not include links to NIL whereas named entity linking only deals with named entities and requires a system to link to NIL if no matching entity was found in the knowledge base.
Hachey et al. suggest to separate the task of named entity linking into three components: an extractor (extracting mention spans), a searcher (searching for entity candidates) and a disambiguator (settle on a single suitable candidate)
... 