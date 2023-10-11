# Benchmark Annotation Guidelines

The following are the guidelines we derived to annotate our Wiki-Fair and News-Fair benchmarks.

**Notation:**
Entity annotations are written as "[Q1234|**original mention text**]". Alternative annotations are written as nested
 annotations. Prefixes to the QID can be used to describe the annotation type. E.g. "[optional:Q1234|**some text**]" or
 "[desc:Q123|**some entity description**]".


## What kind of entities should be annotated?

### Entities with whitelist types
**Example:**
"[Q44578|**Titanic**] **is a film by** [Q2526255|**director**] [Q42574|**James Cameron**]**.**" *(The entities for
 "Titanic", "director" and "James Cameron" all have an instance of / subclass of path in Wikidata to a type from our
 type whitelist ("creative work", "occupation" and "person", respectively). "film" on the other hand is not an
 instance of any type in Wikidata, but only subclass of some types.)*

**Guideline:**
Annotate only entities that have an instance of / subclass of (P31/P279*) path to at least one type that occurs in our
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
 only annotating entities that have at least one of these whitelist types in Wikidata (via an P31/P279* path, i.e.,
 the entity has to be an instance of a type that is a subclass - direct or indirect - of a type from our whitelist). If
 the Wikidata type system is clearly wrong for an entity, we allow manual corrections, e.g. adding or removing a
 whitelist type to/from an entity.

**More examples:**
- “[Q22656|**oil**] **or** [Q40858|**gas**] **reserves**” *(Only oil has a whitelist type, gas on the 
 other hand is only subclass of fossil fuel, fuel gas and mixture. But if one of those has a whitelist type, clearly
 the other one should also have one.)*
- "**mediation, arbitration and conflict resolution**" *(Conflict resolution has the whitelist type academic discipline
 while mediation and arbitration don't. However, it is quite clear that all three phrases should be handled the same.
 Conflict resolution is not an academic discipline in the same sense that Psychology or Maths is, so we decide not to
 annotate any of the phrases.)*
 
#### Occupation vs. profession
**Example:** "[Q38111|**Leonardo DiCaprio**] **is an** [Q33999|**actor**] **and supporter of environmental
 conservation.**" *(Even though both "actor" and "supporter" have the whitelist type "occupation", only "actor" is an
 actual profession.)*

**Guideline:**
Only annotate occupations if they are actual professions or describe how a person can spend a significant part of
 their day.

**Explanation:**
Many Wikidata occupations are not professions or occupations in the typical sense, e.g. "supporter", "lover"
 or "gentleman". Such Wikidata occupations should not be annotated

**More examples:**
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
**Example:** "[Q16855376|**Wayde**] **was born prematurely on** [datetime|**July 15, 1992**] **and weighed only a
 little over** [quantity|**1**] **kg.**" *(Datetimes and quantities are annotated with special labels.)*

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

**More examples:**
- "[Q26720335|**Sameli Ventelä**] **(born** [datetime|**July 19, 1994**]) **is a ...**"
- "**... which occurred** [quantity|**398**]**-**[quantity|**391 million**] **years ago.**"
- "[quantity|**235**] **kg**"
- "[Q234491|**Junko Tabei**] **was the** [quantity|**first**] **woman to climb** [Q513|**Mount Everest**]."


### Notability of an entity

**Example:**
"**As children, they competed against each other in a yearly local sports competition. They later both went on to
 compete in the** [Q5389|**Olympics**] **.**" *(While both the local sports competition and the Olympics are entities,
 only the latter is notable enough to be annotated and to appear in a Knowledge Base.)*

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

**More examples:**
- "[Q317521|**Elon Musk**] **launched** [coref:Q317521|**his**] **car** [Q46845259|**TSLA10**] **into space.**"

*But:*

- "[Unknown1|**Anna**] **sold her old car and bought a new one.**"

## How to annotate implicit references to entities?

### Descriptive mentions
**Example:**
"[desc:Q233583|**second war between** [Q843|**Pakistan**] **and** [Q668|**India**] **in** [datetime|**1965**]]"

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

**More examples:**
- "[desc:Q3996446|[datetime|**1992**] [Q599903|**Ireland rugby union**] **tour of** [Q664|**New Zealand**]]"
- "[desc:Q6408627|[Q6138516|**Her**] **character**] **had been** [Q6100764|**Ray**]**’s partner for several months.**"
- "[Q3521569|**He**] **talked to** [desc:Unknown1|**an** [Q30093123|**investigator**]]."
- "[desc:Unknown1|**performance** [Q485178|**analyst**]"
- "**In the** [desc:datetime|**previous year**], **the** [Q5389|**Olympic Games**] **had been held in**
 [Q84|**London**]." *But:* "**In hindsight, the previous year typically appears less dramatic than the current one.**"
 *(Because "previous year" in this example does not refer to a concrete year.)*
- "[Q317521|**He**] **is now the richest person on** [desc:Q2|**the planet**]." *(If "Earth" had occurred before in the
 text, then this would be a coreference instead.)*
- "[Unknown1|**VRA**] **is one of the premier** [Q729267|**radiation oncology**] **groups in**
 [desc:Q30|**the nation**] **.**" *(If "USA" had occurred before in the text, then this would be a coreference instead)*
- "**In the** [desc:Q1466815|**2008 election**]**, ...**"

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
**Example:**
"[Q221|**North Macedonia**] **is in** [desc:Q27449|**southern-**[Q46|**Europe**]] **.**"

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

**More examples:**
- "[desc:Q14234469|**south-central** [Q816|**Arizona**]]"

*But:*
- "[Q771405|**South Asia**]"
- "[Q35715|**South Australia**]"


### Names
**Example:**
"[Q13462698|**Chersotis juncta**]**, known generally as the** [optional:Q13462698|**stirrup dart moth**]"

**Guideline:**
Use optional annotations for cases where an entity's name and not the entity itself is being referred to.

**Explanation:**
In cases like "Chersotis juncta, known generally as the stirrup dart moth ..." the mention text "stirrup dart moth"
 refers to the name of the entity, not the entity itself. In this case, a system should not be punished for not
 linking it. However, the mention still has a connection to the actual entity mentioned in the text, so linking it
 should not be punished either. In cases, where an entity name is mentioned and not clearly connected to an actual
 entity in the text, that name should not be annotated, e.g. in "Rosaline is used as a name for only one other
 character".

**Examples:**
- "[Q5720272|**Tizkharab**]**, also Romanized as** [optional:Q5720272|**Tīzkharāb**]**, ...**"

*But:*
- "**Rosaline is used as a name for only one other character.**"
- "[quantity|**Two**] **ships have been named New Jersey.**"


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

### Coreferences
**Example:**
"[Q567|**Angela Merkel**] **received** [coref:Q567|**her**] [Q752297|**PhD**] **in** [datetime|**1986**] **.**
 [coref:Q567|**The politician**] **speaks at least** [quantity|**three**] **languages fluently.**"

**Guideline:**
Annotate pronominal (e.g., her, he, itself) and nominal (e.g., the politician, the film, the < type >) references to
 an entity that has been mentioned in the text before as coreferences.

**More examples:**
- "[Q2|**Earth**] **orbits the** [Q525|**Sun**] **at an average distance of** [quantity|**149.60 million**] **km.**
 [coref:Q2|**The planet**] **is the** [quantity|**fourth**] **biggest in the** [Q544|**solar system**]."

*But*
- "[Q317521|**Elon Musk**] **is now the richest person on** [desc:Q2|**the planet**]." *(If "Earth" had occurred
 before in the text, then this would be a coreference instead.)*


## What should be part of an entity mention?

### Alternative Mention Spans
**Example:**
"[Q6065437|[Q192964|**Istanbul University**] [Q6065437|**Faculty of Medicine**]]"

**Guideline:**
If it is not clear whether something is part of the mention or not, e.g. because a longer span could be seen either
 as an alias of an entity or just as a clarifying addition, annotate both versions.

**More examples:**
- "[Q213677|[Q213677|**Louis VIII**]**,** [Q841633|**Landgrave**] **of** [Q693551|**Hesse-Darmstadt**]]"
- "[Q406|[Q406|**Istanbul**]**,** [Q43|**Turkey**]]"
- "[Q7268035|[Q7268035|**Qohestan Rural District**]**,** [Q1286121|**Darmian County**]**,** [Q794|**Iran**]]" *(Don't
 annotate a descriptive entity for each possible combination of adjacent region names. If a linker counts such
 occurrences as a single entity, it should do that consistently and link the entire phrase.)*
- "[Q2309784|**professional** [Q2309784|**racing cyclist**]]" *(Note that this is not descriptive, as "professional"
 is at least to some degree redundant)*

### Entity name + type
**Example:**
"**The** [Unknown1|[Unknown1|**Jalap**] **tribe**] **resides in** [Q32429|**Jhelum District**] **.**"

**Guideline:**
Annotate both the entity name, and the entity name together with the type as alternative mentions if the type is
 written in lowercase. Otherwise annotate only the long version (i.e. the entity name together with the type).

**Explanation:**
Sometimes the type of an entity is being appended to the entity name, e.g. "Mollarino river" or "Jalap tribe".
 The appended type can potentially be considered as part of the entity name and a linker should not be punished if it
 annotates only the entity name or the entity name together with the type. Therefore, both options should be annotated
 as alternative mentions *if the type is not capitalized*.
If the type is capitalized as in "New York City" or "Punjab Province", then the author of the text clearly used the
 type as part of the entity name, thus only the entire mention of entity name + type should be annotated.
If the type is not capitalized, but it is essential to the entity's name as in "Allegheny plateau" or "Tadlow bridge"
 then also allow only the entire phrase.

**More examples:**
- "[Q109981393|[Q109981393|**Mollarino**] **river**]"

*But:*
- "[Q60|**New York City**]"
- "[Q4478|**Punjab Province**]"
- "[Q654947|**Allegheny plateau**]"
- "[Unknown1|**Tadlow bridge**]"

### Descriptive prefix to an entity
**Example:**
"[Q855091|**Guitarist**] [Q1689423|**Jimmy Ponder**] **never had an audition with** [Q450675|**Pope Francis**] **.**"
 *("guitarist" is merely a descriptive prefix to the entity "Jimmy Ponder". It is not part of the entity name as is
 the case for "Pope" in "Pope Francis".)*

**Guideline:**
A descriptive prefix to an entity should not be included in the annotation for the entity, unless it is part of the
 entity name. If it can in some circumstances be considered part of the entity name, annotate both versions.

**Explanation:**
In the phrase "guitarist Jimmy Ponder", "guitarist" is a descriptive prefix to the entity "Jimmy
 Ponder". "guitarist" describes the entity "Jimmy Ponder" further, but the entity is already sufficiently described
 by its name, "Jimmy Ponder". The entire phrase should therefore not be annotated as descriptive mention, as it is
 not 0% redundant.
If however the descriptive prefix is part of the entity name as in "Pope Francis", then the entire mention should be
 annotated (as non-descriptive).
If the descriptive prefix can be part of the entity name, but not rigidly, as in "Dr. Justin Maciejewski" or
 "Brigadier Justin Maciejewski", allow both options (see guideline for honorific prefixes).

**More examples:**
- "[Q855091|**guitarist**] [Q1689423|**Jimmy Ponder**]"
- "[Q12859263|**orator**] [Q263892|**Libanius**]"
- "[Q14558450|**Januzaj**]**'s** [Q1344174|**agent**] [Q2316058|**Dirk de Vriese**]"
- "[Q443528|**his**] **wife** [Q1570201|**Jacquetta Hawkes**]"
- "[Q142|**French**] **TV show** [Q3546609|**Telefoot**]"

*But:*
- "[Q8058|**King Louis XI**]"


### Honorific prefixes
**Example:**
"[Q75420596|[Q177053|**Mr.**] [Q75420596|**George Wilson**]] **never met** [Q450675|**Pope Francis**] **.**"
 *("Mr." can be considered as part of the entity name, but does not have to. "Pope" on the other hand is part of
 the entity name.)*

**Guideline:**
A honorific prefix should be annotated once as part of the entity name and once separately as the honorific prefix
 (not as the occupation). If the honorific prefix is part of the entity name, then only the entire phrase should be
 annotated.

**Explanation:**
Honorific prefixes such as "Mr.", "Dr." or "Prof." can be considered as part of the entity name, but don't have to.
 "Prof." or "Rev." does not refer to the occupation professor or reverend, otherwise the word would not be
 capitalized and not abbreviated. Therefore, annotate the honorific prefix and not the occupation. Annotate both
 options: the entire phrase including the honorific prefix and the honorific prefix and the name separately. 

**More examples:**
- "[Q75420596|[Q841594|**Rev.**] [Q75420596|**George Wilson**]]"
- "[Q104708740|[Q4967182|**Brigadier**] [Q104708740|**Justin Maciejewski**]]"

*But:*
- "[Q8058|**King Louis XI**]"


### Distributed entity mentions
**Example:**
"[Q6271700|**Tucker**] **has written** [Q637866|**book**] **and** [Q69699844|**film reviews**]**.**"

**Guideline:**
Annotate the parts of a distributed entity mention separately and with the entity they refer to, respectively.

**Explanation:**
In phrases like "Tucker has also written book and film reviews.", the entity mention for "book reviews" is
 distributed over the course of the sentence and does not occur adjunctively. Ideally, an annotation should reflect
 that, however, our evaluation does not support non-adjunctive mentions, thus we opt to annotate just the text "books"
 with the entity for book review (and "film reviews" with the entity for film reviews).

**More examples:**
- "[Q16195965|**He**] **was not a member of the squads for the** [Q1322713|**1991**] **or** [Q1130017|**1995 Rugby World
 Cups**]**.**"


## Which entity should a mention be annotated with?

Most of the times, this is straight forward. "Merkel" in "Merkel congratulates Olaf Scholz on election success."
 should of course be annotated with the entity for the former chancellor of Germany Angela Merkel. Some specific
 cases are however not quite as clear. E.g., should "German" in "The German politician Olaf Scholz ..." be annotated
 with the entity for the country Germany or the entity for the residents and citizens of Germany? (See
 [Demonyms](#demonyms) section.)

### Demonyms
**Example:**
"[Q44578|**Titanic**] **is an** [Q30|**American**] **movie by the** [Q16|[Q1196645|**Canadian**]]
 [Q2526255|**director**] [Q42574|**James Cameron**]**.**"

**Guideline:**
In general, annotate demonym mentions with the country. Additionally, annotate the mention with the ethnicity or
 country-citizens if the cultur/ethnicity or citizenship is being referred to. Only annotate the mention with the
 language if it is 100% clear that the language is being referred to.

**Explanation:**
The mention should not be annotated with the ethnicity in cases like "The [Q15180|Soviets] agreed to the [Q30|American]
 demands", since both "Soviet" and "American" here refers to (a part of) the government which is better represented by
 the country than the ethnicity or citizenship. The mention should also not be annotated in cases like "[...|American] 
 movie", since it will still be an American movie if the director decides to migrate to another country, so the
 modifier "American" does not change with the citizenship. However, "American" in "American dish" refers to the
 culture, therefore it should be annotated with both the country and the ethnicity/citizens.

**More examples:**
- "[Q30|[Q846570|**American**]] **dish**" *(country and citizens)*
- "**'sectores' means 'sectors' in** [Q1321|**Spanish**]" *(language)*

*But:*
- "[Q30|**American**] **movie**" *(country)*
- "**The** [Q15180|**Soviets**] **agreed to the** [Q30|**American**] **demands**" *(country)*
- "[Q30|**American**] **music group** [Q72349|**Krewella**]" *(country)*
- "[Q23736538|**Store Egholm**] **is a small** [Q35|**Danish**] **island**" *(country)*


### Metonyms
**Example:**
"[Q43310|**Germany**] **beat** [Q83459|**Brazil**] **7 to 1 in** [Q42800|**Belo Horizonte**]**.**"

**Guideline:**
If it is 100% clear which entity is being referred to, annotate that entity. Otherwise link the entity that is being
 referred to more literally.

**Explanation:**
In the sentence "Germany beat Brazil 7 to 1 in Belo Horizonte", "Germany" and "Brazil" clearly refer to the national
 football teams of the corresponding countries, therefore these entities should be annotated. With Belo Horizonte
 however, the author could be referring to the stadion in Belo Horizonte or the city. Since it is not 100% clear, which
 of these entities is being referred to, the city should be annotated, as the mention text is the literal city name.
