# Benchmark Annotation Guidelines

The following are the guidelines we derived to annotate our Wiki-Fair and News-Fair benchmarks.

**Notation:**
Entity annotations are written as "[Q1234|**original mention text**]". Alternative annotations are written as nested
 annotations. Prefixes to the QID can be used to describe the annotation type. E.g. "[optional:Q1234|**some text**]" or
 "[desc:Q123|**some entity description**]".


## Entity whitelist types
**Guideline:**
Annotate only entities that have a P31/P279* (instance of, subclass of) path to at least one type that occurs in our
 [type whitelist](../small-data-files/whitelist_types.tsv).
If an entity should clearly have a type from that list, but the corresponding path is missing in the KB, annotate that
 entity anyway. If an entity has a whitelist type according to the Knowledge Base but clearly should not have, don't
 annotate that entity.

**Explanation:**
While it is relatively easy to decide what counts as an entity when only considering named entities, the decision
 boundary becomes very fuzzy when non-named entities are considered as well. It is not an option to simply annotate
 everything that has an entry in the Knowledge Base, because then almost everything is an entity (even the word "the"
 has a Wikidata entry) and this arguably is not helpful for any application of entity linking that comes to mind.
 But then where to draw a line? We try to render the decision boundary more precise by creating a type whitelist and
 only annotating entities that have at least one of these whitelist types in Wikidata (via an P31/P279* path). If
 the Wikidata type system is clearly wrong for an entity, we allow manual corrections, e.g. adding or removing a
 whitelist type to/from an entity.

**Examples:**
- “[Q22656|**oil**] **or** [Q40858|**gas**] **reserves**” *(Only oil has a whitelist type, gas on the 
 other hand is only subclass of fossil fuel, fuel gas and mixture. But if one of those has a whitelist type, clearly
 the other one should also have one.)*
- "**mediation, arbitration and conflict resolution**" *(Conflict resolution has the whitelist type academic discipline
 while mediation and arbitration don't. However, it is quite clear that all three phrases should be handled the same.
 Conflict resolution is not an academic discipline in the same sense that Psychology or Maths is, so we decide not to
 annotate any of the phrases.)*
 
#### Occupation vs. profession
**Guideline:**
Only annotate occupations if they are actual professions or describe how a person can spend a significant part of
 their day.

**Explanation:**
Many Wikidata occupations are not professions or occupations in the typical sense, e.g. "supporter", "lover"
 or "gentleman". Such Wikidata occupations should not be annotated

**Examples:**
- "[Q485178|**analyst**]"
- "[Q48282|**student**]"
- "[Q30093123|**investigator**]"
- "[Q937857|**football player**]"
- "[Q38126150|**housewife**]"

*But:*
- "gentleman"
- "supporter"
- "lover"

#### Datetimes and Quantities
**Guideline:**
Annotate datetimes and quantities with the special labels "datetime" and "quantity". No QID is annotated.
Don't include the unit of a quantity in the mention.

**Explanation:**
Datetimes and quantities are rarely linked by any linker, yet many definitions of named entities include them. Thus,
 a linker should not be punished when linking them. A datetime or quantity counts as correctly linked when the span
 matches the annotated span and the type of the linked entity is "point in time" (Q186408) or "real number" (Q12916)
 for datetimes and quantities respectively.
Datetimes and quantities are evaluated as optional mentions, i.e. they don't count as true positives when they are
 correctly linked, but they also don't count as false negatives if they are not linked.

**Examples:**
- "[Q26720335|**Sameli Ventelä**] **(born** [datetime|**July 19, 1994**]) **is a ...**"
- "**... which occurred** [quantity|**398**]**-**[quantity|**391 million**] **years ago.**"
- "[quantity|**235**] **kg**"
- "[Q234491|**Junko Tabei**] **was the** [quantity|**first**] **woman to climb** [Q513|**Mount Everest**]."


## Notability of an entity

**Guideline:**
Annotate entities that are notable enough to occur in the Knowledge Base (Wikidata).
If the entity exists in the KB, annotate it unless it is clearly an outlier that does not belong in the KB.
If the entity does not exist in the KB, think about whether it is missing from the KB, i.e. it should actually be
 contained in the KB, given the other entities in the KB. If it is missing from the KB, annotate it as "Unknown".
 Otherwise don't annotate it.

**Explanation:**
When annotating, the question is sometimes not whether something is an entity, but whether something is notable
 enough to be annotated. E.g. in "As children, they competed against each other in a yearly sports competition held
 by their school". Just like "Olympic Games" is an entity, so is the competition described here. However, the entity
 is most likely not notable enough to be annotated, let alone to be contained in any Knowledge Base. Similarly "Anna's
 Golf" is certainly a descriptive mention of an entity, but that entity is most likely not notable enough to be
 annotated. 

**Examples:**
- "**As children, they competed against each other in a yearly sports competition held by** 
 [desc:Unknown1|**their school**]".
- "[Unknown1|**Anna**] **sold her old car and bought a new one.**"

 
## Descriptive mentions

**Guideline:**
Annotate mentions as descriptive ([desc:...|...]) only if they are 100% descriptive.
In a descriptive mention, also annotate the entities that occur within the description as alternative mentions.

**Explanation:**
A mention can be clearly an entity name, e.g. "Angela Merkel" or it can be a description of an entity, e.g. "second
 war between Pakistan and India in 1965". There are also cases where the differentiation is not quite as sharp, e.g.
 in " 2012 Summer Olympics". In general, most entity names are to some extent descriptive, e.g. "South Australia":
 This Australian state is indeed in the south of Australia, but it arguably does not contain the entire south
 of Australia nor is it clear that every point in the state could objectively be referred to as "in the south
 Australia". Thus the entity name "South Australia" is partly but not purely descriptive.
A further requirement for descriptive mentions is that they must be 0% redundant. E.g., for a river called "Mollarino"
 the mention "Mollarino river" might be 100% descriptive, but it is redundant. The word "river" is not required to
 describe the entity. Thus, it should not be annotated as descriptive mention (although the mention "Mollarino river"
 should be annotated as alternative mention).
 
Currently, most systems don't recognize purely descriptive mentions. However, it would be wrong to punish a system
 that can, therefore they should be annotated. And it is not a hypothetical scenario, as GPT-4 for example detects
 such descriptive mentions.

**Examples:**
- "[desc:Q233583|**second war between** [Q843|**Pakistan**] **and** [Q668|**India**] **in** [datetime|**1965**]]"
- "[desc:Q3996446|[datetime|**1992**] [Q599903|**Ireland rugby union**] **tour of** [Q664|**New Zealand**]]"
- "[desc:Q6408627|[Q6138516|**Her**] **character**] **had been** [Q6100764|**Ray**]**’s partner for several months.**"
- "[Q3521569|**He**] **talked to** [desc:Unknown1|**an** [Q30093123|**investigator**]]."
- "[desc:Unknown1|**performance** [Q485178|**analyst**]"
- "**In the** [desc:datetime|**previous year**], **the** [Q5389|**Olympic Games**] **had been held in**
 [Q84|**London**]." *But:* "**In hindsight, the previous year typically appears less dramatic than the current one.**"
- "[Q317521|**He**] **is now the richest person on** [desc:Q2|**the planet**]." *(If "Earth" had occurred before in the
 text, then this would be a coreference instead.)*

*But:*
- "[Q8577|**2012 Summer Olympics**]"
- "[Q35715|**South Australia**]"
- "[Q60|**New York**]"
- "[Q271894|**French Equatorial Africa**]"
- "[Q213610|**Louis IX of Hesse-Darmstadt**]"
- "[Q362|**Second World War**]"
- "[Q30|**United States of America**]"
- "[Q109981393|[Q109981393|**Mollarino**] **river**]"


#### Narrowing of entities
**Guideline:**
A phrase that is narrowing down an entity should be annotated as descriptive entity if the described part of the entity
 is notable enough to deserve its own KB entry. The entity itself should be annotated as alternative mention.
If the narrowing modifier is capitalized and can be seen as part of the entity name then only the entire phrase
 should be annotated (as non-descriptive).

**Explanation:**
The mention "south-central Arizona" is narrowing down the entity "Arizona" to describe only a certain part of Arizona.
 The entire phrase is a descriptive mention for the south-central part of Arizona which is notable enough to have an
 entry in Wikidata. Therefore, the entire mention should be annotated as a descriptive mention and "Arizona"
 should be annotated as alternative mention with the corresponding state.
If the narrowing modifier is capitalized as in "South Asia" then the author of the text used it as part of an entity
 name, thus the mention is not 100% descriptive and should not be annotated as such.

**Examples:**
- "[desc:Q14234469|**south-central** [Q816|**Arizona**]]"
- "[desc:Q27449|**southern-**[Q46|**Europe**]]"

*But:*
- "[Q771405|**South Asia**]"
- "[Q35715|**South Australia**]"


### Entity name + type
**Guideline:**
Annotate the entity name, and annotate the entity name together with the type as descriptive mention if the type is
 written in lowercase. Otherwise annotate only the entity name together with the type as non-descriptive.

**Explanation:**
A common case of descriptive mentions is to append the type of an entity to the entity name, e.g. "Mollarino river" or
"Jalap tribe". These mentions can be considered as purely descriptive *if the type is not capitalized*. If the type
 is capitalized as in "New York City" or "Punjab Province", then the author of the text clearly used the type as part
 of the entity name, thus the mention is not 100% descriptive and should not be annotated as descriptive.
If the type is not capitalized, but it is essential to the entity's name as in "Allegheny plateau" or "Tadlow Bridge"
 then allow only the entire phrase.

**Examples:**
- "[Q109981393|[Q109981393|**Mollarino**] **river**]"
- "[Unknown1|[Unknown1|**Jalap**] **tribe**]"

*But:*
- "[Q60|**New York City**]"
- "[Q4478|**Punjab Province**]"
- "[Q32429|**Jhelum District**]"
- "[Q654947|**Allegheny plateau**]"


### Descriptive prefix to an entity
**Guideline:**
A descriptive prefix to an entity should not be included in the annotation for the entity, unless it is part of the
 entity name. If it can in some circumstances be considered part of the entity name, annotate both versions.

**Explanation:**
In the phrase "[...|guitarist] [...|Jimmy Ponder]", "guitarist" is a descriptive prefix to the entity "Jimmy
 Ponder". "guitarist" describes the entity "Jimmy Ponder" further, but the entity is already sufficiently described
 by its name, "Jimmy Ponder". Therefore, the entire phrase should not be annotated as descriptive mention.
If however the descriptive prefix is part of the entity name as in "Pope Francis", then the entire mention should be
 annotated as non-descriptive.
If the descriptive prefix can be part of the entity name, but not rigidly, as in "Dr. Justin Maciejewski" or
 "Brigadier Justin Maciejewski", allow both options (see also guideline for honorific prefixes).

**Examples:**
- "[Q855091|**guitarist**] [Q1689423|**Jimmy Ponder**]"
- "[Q12859263|**orator**] [Q263892|**Libanius**]"
- "[Q14558450|**Januzaj**]**'s** [Q1344174|**agent**] [Q2316058|**Dirk de Vriese**]"
- "[Q443528|**his**] **wife** [Q1570201|**Jacquetta Hawkes**]"
- "[Q142|**French**] **TV show** [Q3546609|**Telefoot**]"

*But:*
- "[Q450675|**Pope Francis**]"
- "[Q8058|**King Louis XI**]"


### Honorific prefixes
**Guideline:**
A honorific prefix should be annotated once as part of the entity name and once separately as the honorific prefix
 (not as the occupation). If the honorific prefix is part of the entity name, then only the entire phrase should be
 annotated.

**Explanation:**
Honorific prefixes such as "Mr.", "Dr." or "Prof." can be considered as part of the entity name, but don't have to.
 "Prof." or "Rev." does not refer to the occupation professor or reverend, otherwise the word would not be
 capitalized and not abbreviated. Therefore, annotate the honorific prefix and not the occupation. Annotate both
 options: the entire phrase including the honorific prefix and the honorific prefix and the name separately. 

**Examples:**
- "[Q75420596|[Q177053|**Mr.**] [Q75420596|**George Wilson**]]"
- "[Q75420596|[Q841594|**Rev.**] [Q75420596|**George Wilson**]]"
- "[Q104708740|[Q4967182|**Brigadier**] [Q104708740|**Justin Maciejewski**]]"

*But:*
- [...|Pope Francis]


### Alternative Mention Spans
**Guideline:**

**Explanation:**

**Examples:**
- "[Q213677|[Q213677|**Louis VIII**]**,** [Q841633|**Landgrave**] **of** [Q693551|**Hesse-Darmstadt**]]"
- "[Q406|[Q406|**Istanbul**]**,** [Q43|**Turkey**]]"
- "[Q7268035|[Q7268035|**Qohestan Rural District**]**,** [Q1286121|**Darmian County**]**,** [Q794|**Iran**]]" *(Don't
 annotate a descriptive entity for each possible combination of adjacent region names. If a linker counts such
 occurrences as a single entity, it should do that consistently and link the entire phrase.)*

### Distributed entity mentions
**Guideline:**
Annotate the parts of a distributed entity mention separately and with the respective entity they refer to.

**Explanation:**
In phrases like "Tucker has also written book and film reviews.", the entity mention for "book reviews" is
 distributed over the course of the sentence and does not occur adjunctively. Ideally, an annotation should reflect
 that, however, our evaluation does not support non-adjunctive mentions, thus we opt to annotate "books" with the
 entity for book review (and "film reviews" with the entity for film reviews).


**Examples:**
- "[Q6271700|**Tucker**] **has also written** [Q637866|**book**] **and** [Q69699844|**film reviews**]**.**"
- "[Q16195965|**He**] **was not a member of the squads for the** [Q1322713|**1991**] **or** [Q1130017|**1995 Rugby World
 Cups**]**.**"


### Demonyms
**Guideline:**
In general, annotate demonym mentions with the country. Additionally, annotate the mention with the ethnicity or
 country-citizens if the culture is being referred to. Only annotate the mention with the language if it is obvious
 that the language is being referred to.

**Explanation:**
The mention should not be annotated with the ethnicity in cases like "The [Q15180|Soviets] agreed to the [Q30|American]
 demands", since both "Soviet" and "American" here refers to (a part of) the government which is better represented by
 the country than the ethnicity or citizenship. The mention should also not be annotated in cases like "[...|American] 
 movie", since it will still be an American movie if the director decides to migrate to another country, so the
 modifier "American" does not change with the citizenship.

**Examples:**
- "[Q30|[Q846570|**American**]] **dish**" *(country and citizens)*
- "**'sectores' means 'sectors' in** [Q1321|**Spanish**]" *(language)*

*But:*
- "[Q30|**American**] **movie**" *(country)*
- "**The** [Q15180|**Soviets**] **agreed to the** [Q30|**American**] **demands**" *(country)*
- "[Q30|**American**] **music group** [Q72349|**Krewella**]" *(country)*
- "[Q23736538|**Store Egholm**] **is a small** [Q35|**Danish**] **island**" *(country)*


### Names
**Guideline:**
Use optional annotations for cases where an entity's name and not the entity itself is being referred to.

**Explanation:**
In cases like "[...|Chersotis juncta], known generally as the [optional:...|stirrup dart moth] ..." it is the name of
 the entity that is being referred to, not the entity itself. In this case, a system should not be punished for not
 linking it. However, the mention still has a connection to the actual entity mentioned in the text, so linking it
 should not be punished either. In cases, where an entity name is mentioned and not clearly connected to an actual
 entity in the text, that name should not be annotated, e.g. in "Rosaline is used as a name for only one other 
 character".

**Examples:**
- "[Q13462698|**Chersotis juncta**]**, known generally as the** [optional:Q13462698|**stirrup dart moth**]"

*But:*
- "**Rosaline is used as a name for only one other character**"



### Figurative language
**Guideline:**
Don't annotate entities that would have a whitelist types but are used figuratively only.

**Explanation:**

**Examples:**
- *"air" in* "[Q6100764|**Ray**] **needs to come up for a breath of air, as there's only so much of** 
 [Q6408627|**Kim**]**'s heightened personality** [Q6100764|**he**] **can bear.**"
- "**That's a storyline with legs.**" *(Not a good example, because "leg" does currently not have a whitelist type
 anymore anyway.)*
- "**A soft heart, calm head and gentleman to everyone.**" *(Not a good example, see above.)*

