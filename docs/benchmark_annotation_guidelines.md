# Benchmark Annotation Guidelines

The following are the guidelines we derived to annotate our Wiki-Fair and News-Fair benchmarks.

**Notation:**
Entity annotations are written as "[Q1234|original mention text]". The QID can be replaced by "..." if it is not
 relevant for understanding the example. Alternative annotations are written as nested annotations.


## Entity whitelist types
**Guideline:**
Annotate only entities that have a P31/P279* (instance of, subclass of) path to at least one type that occurs in our
 type whitelist.
If an entity should clearly have a type, but the corresponding path is missing in the KB, annotate that entity anyway.
If an entity has a whitelist type according to the Knowledge Base but clearly should not have, don't annotate that
 entity.

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
- “[Q22656|oil] or [gas] reserves” (Only oil has a whitelist type, gas on the other hand is only subclass of
 fossil fuel, fuel gas and mixture. But if one of those has a whitelist type, clearly the other one should also have
 one.)
- "mediation, arbitration and conflict resolution" (Conflict resolution has the whitelist type academic discipline
 while mediation and arbitration don't. However, it is quite clear that all three phrases should be handled the same.
 Conflict resolution is not an academic discipline in the same sense that Psychology or Maths is, so we decide not to
 annotate any of the phrases.)
 
## Descriptive mentions

**Guideline:**
Annotate mentions as descriptive ([DESC:...|...]) only if they are 100% descriptive.
In a descriptive mention, also annotate the entities that occur within the description as alternative mentions.

**Explanation:**
A mention can be clearly an entity name, e.g. "Angela Merkel" or it can be a description of an entity, e.g. "second
 war between Pakistan and India in 1965". There are also cases where the differentiation is not quite as sharp, e.g.
 in " 2012 Summer Olympics". In general, most entity names are to some extent descriptive, e.g. "South Australia":
 This Australian state is indeed in the south of Australia, but it arguably does not contain the entire south
 of Australia nor is it clear that every point in the state could objectively be referred to as "in the south
 Australia". Thus the entity name "South Australia" is partly but not purely descriptive.
 
Currently, most systems don't recognize purely descriptive mentions. However, it would be wrong to punish a system
 that can, therefore they should be annotated. And it is not a hypothetical scenario, as GPT-4 for example is
 already able to detect such descriptive mentions.

**Examples:**
- "[DESC:Q233583|second war between [...|Pakistan] and [...|India] in [DATETIME|1965]]"
- "[DESC:Q3996446|[DATETIME|1992] [...|Ireland rugby union] tour of [...|New Zealand]]"
- "[DESC:Q6408627|[Q6138516|Her] character] had been [...|Ray]’s partner for several months."
- "[...|He] talked to [DESC:Unknown1|an [...|investigator]]."
- "[DESC:Unknown1|performance [...|analyst]"
- "In the [DESC:DATETIME|previous year], the [...|Olympic Games] had been held in [...|London]." **But:** "In
 hindsight, the previous year typically appears less dramatic than the current one."
- "[...|He] is now the richest person on [DESC:...|the planet]."
- **But:** "[...|2012 Summer Olympics]", "[...|South Australia]", "[...|New York]", "[...|French Equatorial
 Africa]", "[...|Louis IX of Hesse-Darmstadt]", "[...|Second World War]", "[...|United States of America]"


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
- "As children, they competed against each other in a yearly sports competition held by [DESC:Unknown1|their school]".
- "[Unknown1|Anna] sold her old car and bought a new one."


### Derived Guideline: Entity name + type
**Guideline:**
Annotate the entity name, and annotate the entity name together with the type as descriptive mention if the type is
 written in lowercase. Otherwise annotate only the entity name together with the type as non-descriptive.

**Explanation:**
A common case of descriptive mentions is to append the type of an entity to the entity name, e.g. "Mollarino river" or
"Jalap tribe". These mentions can be considered as purely descriptive *if the type is not capitalized*. If the type
 is capitalized as in "New York City" or "Punjab Province", then the author of the text clearly used the type as part
 of the entity name, thus the mention is not 100% descriptive and should not be annotated as descriptive.

**Examples:**
- "[DESC:...|[Mollarino] river]"
- "[DESC:...|[Jalap] tribe]"
- **But:** "[...|New York City]", "[...|Punjab Province]", "[...|Jhelum District]"

### Derived Guideline: Narrowing of entities
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
- "[DESC:...|south-central [...|Arizona]]"
- "[DESC:...|southern-[...|Europe]]"
- **But:** "[...|South Asia]", [...|South Australia]


### Derived Guideline: Descriptive prefix to an entity
**Guideline:**
A descriptive prefix to an entity should not be included in the annotation for the entity, unless it is part of the
 entity name.

**Explanation:**
In the phrase "[...|guitarist] [...|Jimmy Ponder]", "guitarist" is a descriptive prefix to the entity "Jimmy
 Ponder". "guitarist" describes the entity "Jimmy Ponder" further, but the entity is already sufficiently described
 by its name, "Jimmy Ponder". Therefore, the entire phrase should not be annotated as descriptive mention.
If however the descriptive prefix is part of the entity name as in "Pope Francis", then the entire mention should be
 annotated as non-descriptive.

**Examples:**
- "[...|guitarist] [...|Jimmy Ponder]"
- "[...|orator] [...|Libanius]"
- **But:** "[...|Pope Francis]", "[...|King Louis XI]"


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
- "[...|[Q177053|Mr.] [...|Vittorio Zoboli]]"
- "[...|[Q841594|Rev.] [...|Vittorio Zoboli]]"
- **But:** [...|Pope Francis]


### Distributed entity mentions
**Guideline:**
Annotate the parts of a distributed entity mention separately and with the respective entity they refer to.

**Explanation:**
In phrases like "Tucker has also written book and film reviews.", the entity mention for "book reviews" is
 distributed over the course of the sentence and does not occur adjunctively. Ideally, an annotation should reflect
 that, however, our evaluation does not support non-adjunctive mentions, thus we opt to annotate "books" with the
 entity for book review (and "film reviews" with the entity for film reviews).


**Examples:**
- "[Q6271700|Tucker] has also written [Q637866|book] and [Q69699844|film reviews]."
- "[Q16195965|He] was not a member of the squads for the [Q1322713|1991] or [Q1130017|1995 Rugby World Cups]."


### Occupation vs. profession
**Guideline:**
Only annotate occupations if they are actual professions or describe how a person can spend a significant part of
 their day.

**Explanation:**
Many Wikidata occupations are not professions or occupations in the typical sense, e.g. "supporter", "lover"
 or "gentleman". Such Wikidata occupations should not be annotated

**Examples:**
- "[...|analyst]"
- "[...|student]"
- "[...|investigator]"
- "[...|football player]"
- "[...|housewife]"
- **But:** "gentleman", "supporter", "lover"


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
- "[Q30|[Q846570|American]] dish" (country and citizens)
- "'sectores' means 'sectors' in [Q1321|Spanish]" (language)

**But:**
- "[Q30|American] movie" (country)
- "The [Q15180|Soviets] agreed to the [Q30|American] demands" (country)
- "[Q30|American] electronic dance music group Krewella" (country)
- "Store Egholm is a small [Q35|Danish] island" (country)

### Figurative language
**Guideline:**
Don't annotate entities that would have a whitelist types but are used figuratively only.

**Explanation:**

**Examples:**
- "air" in "[...|he] needs to come up for a breath of air, as there's only so much of [...|Kim]'s heightened
 personality [...|he] can bear."
- "That's a storyline with legs." (Not a good example, because "leg" does currently not have a whitelist type anymore
 anyway.)
- "A soft heart, calm head and gentleman to everyone." (Not a good example, see above.)


### Datetimes and Quantities
**Guideline:**
Annotate datetimes and quantities with the special labels "DATETIME" and "QUANTITY". No QID is annotated.
Don't include the unit of a quantity in the mention.

**Explanation:**
Datetimes and quantities are rarely linked by any linker, yet many definitions of named entities include them. Thus,
 a linker should not be punished when linking them. A datetime or quantity counts as correctly linked when the span
 matches the annotated span and the type of the linked entity is "point in time" (Q186408) or "real number" (Q12916)
 for datetimes and quantities respectively.
Datetimes and quantities are evaluated as optional mentions, i.e. they don't count as true positives when they are
 correctly linked, but they also don't count as false negatives if they are not linked.

**Examples:**
- "[...|Sameli Ventelä] (born [DATETIME|July 19, 1994]) is a ..."
- "... which occurred [QUANTITY|398]-[QUANTITY|391 million] years ago."
- "[QUANTITY|235] kg"
- "[...|Junko Tabei] was the [QUANTITY|first] woman to climb Mount Everest."


### Names
**Guideline:**
Use optional annotations for cases where an entity's name and not the entity itself is being referred to.

**Explanation:**
In cases like "[...|Chersotis juncta], known generally as the [OPTIONAL:...|stirrup dart moth] ..." it is the name of
 the entity that is being referred to, not the entity itself. In this case, a system should not be punished for not
 linking it. However, the mention still has a connection to the actual entity mentioned in the text, so linking it
 should not be punished either. In cases, where an entity name is mentioned and not clearly connected to an actual
 entity in the text, that name should not be annotated, e.g. in "Rosaline is used as a name for only one other 
 character".

**Examples:**
- "[...|Chersotis juncta], known generally as the [OPTIONAL:...|stirrup dart moth] ..."
- **But:** "Rosaline is used as a name for only one other character"
