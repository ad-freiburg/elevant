# Our JSONL Format

We use our own JSONL format with one JSON object per line to represent articles and their properties such as
 entity mentions predicted by an entity linker or ground truth labels. Internally, each JSON object in such a JSONL
 file is converted to an object of class `src.models.article.Article` using the function 
 `src.models.article.article_from_json()`. 

Our JSONL format supports the following keys:
- `id`: The article ID
- `title`: The article title
- `text`: The article text
- `url` (*optional*): The article URL
- `hyperlinks` (*optional*): Hyperlinks to Wikipedia articles in the article text as array of
 `[[start_char_index, end_char_index], target_article_title]` 
- `title_synonyms` (*optional*): Bold spans in the abstract of Wikipedia article's, which denote synonyms of the
 article title. An array of `[start_char_index, end_char_index]`.
- `sections` (*optional*): The article's sections as an array of `[[start_char_index, end_char_index], section_title]`
- `entity_mentions` (*optional*): The entity mentions predicted by an entity linker. This should usually be omitted for
 benchmarks. An array of objects with the keys
    - `span`: The span of the entity mention as `[start_char_index, end_char_index]`
    - `recognized_by`: The name of the entity recognition component that recognized the mention
    - `id`: The Wikidata QID of the predicted entity
    - `linked_by`: The name of the entity linker that linked the mention to an entity in a knowledge base
    - `candidates`: An array of QIDs of entity candidates that were considered in the entity disambiguation step
 omitted, this is the entire article text.
- `labels` (*optional*): The ground truth labels for an article. An array of objects with the keys
    - `id`: The ID of a ground truth label. A ground truth ID should be unique within an article.
    - `span`: The span of the ground truth mention as `[start_char_index, end_char_index]`
    - `entity_id`: The Wikidata QID of the ground truth entity
    - `name`: The name of the Wikidata entity
    - `parent`: The ID of the parent ground truth label (in case the ground truth contains nested labels). `null` if the
     ground truth label has no parent
    - `children`: The IDs of the child ground truth labels (in case the ground truth contains nested labels). `[]` if
     the ground truth label has no children.
    - `optional`: Boolean indicating whether the detection of the ground truth label is optional.
    - `type`: The whitelist Wikidata type(s) of the ground truth entity
- `evaluation_span`: The span of the article text for which linking results should be evaluated. Typically, this is
 the span of the entire article text.

The following is an example for a file that contains two articles (both consisting of a single sentence) with predicted
 entity mentions and ground truth labels:

    {"id": 1, "title": "Some title", "text": "Angelina, her father Jon, and her partner Brad never played together in the same movie.", "hyperlinks": [], "title_synonyms": [], "entity_mentions": [{"span": [0, 8], "recognized_by": "SpaCy_NER", "id": "Q29441544", "linked_by": "EXPLOSION", "candidates": ["Q108379", "Q29441544"]}, {"span": [21, 24], "recognized_by": "SpaCy_NER", "id": "Q6270797", "linked_by": "EXPLOSION", "candidates": ["Q6270797"]}, {"span": [42, 46], "recognized_by": "SpaCy_NER", "id": "Q4954359", "linked_by": "EXPLOSION", "candidates": ["Q2370554", "Q4953783", "Q4954359"]}], "evaluation_span": [0, 87], "labels": [{"id": 0, "span": [21, 24], "entity_id": "Q167520", "name": "Jon Voight", "parent": null, "children": [], "optional": false, "type": "Q18336849"}, {"id": 1, "span": [42, 46], "entity_id": "Q35332", "name": "Brad Pitt", "parent": null, "children": [], "optional": false, "type": "Q18336849"}, {"id": 2, "span": [0, 8], "entity_id": "Q13909", "name": "Angelina Jolie", "parent": null, "children": [], "optional": false, "type": "Q18336849"}]}
    {"id": 2, "title": "Some title", "text": "Heidi and her husband Seal live in Vegas.", "hyperlinks": [], "title_synonyms": [], "entity_mentions": [{"span": [0, 5], "recognized_by": "SpaCy_NER", "id": "Q2618588", "linked_by": "EXPLOSION", "candidates": ["Q21646479", "Q2618588", "Q271697"]}, {"span": [35, 40], "recognized_by": "SpaCy_NER", "id": "Q23768", "linked_by": "EXPLOSION", "candidates": ["Q23768", "Q932929", "Q942661"]}], "evaluation_span": [0, 41], "labels": [{"id": 0, "span": [0, 5], "entity_id": "Q60036", "name": "Heidi Klum", "parent": null, "children": [], "optional": false, "type": "Q18336849"}, {"id": 1, "span": [35, 40], "entity_id": "Q23768", "name": "Las Vegas", "parent": null, "children": [], "optional": false, "type": "Q27096213|Q43229"}, {"id": 2, "span": [22, 26], "entity_id": "Q218091", "name": "Seal", "parent": null, "children": [], "optional": false, "type": "Q18336849"}]}
