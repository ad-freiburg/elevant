ANNOTATION_CLASS_TP = "tp"
ANNOTATION_CLASS_FP = "fp"
ANNOTATION_CLASS_FN = "fn"
ANNOTATION_CLASS_UNKNOWN = "unknown"
ANNOTATION_CLASS_OPTIONAL = "optional"
ANNOTATION_CLASS_CORRECT_OPTIONAL = "correct_optional"
ANNOTATION_CLASS_UNEVALUATED = "unevaluated"

RESULTS_EXTENSION = ".results";

MAX_SELECTED_APPROACHES = 2;
MAX_CACHED_FILES = 15;

ignore_headers = ["true_positives", "false_positives", "false_negatives", "ground_truth"];
percentage_headers = ["precision", "recall", "f1"];
copy_latex_text = "Copy LaTeX code for table";

header_descriptions = {"undetected": "The span of a GT mention was not linked (= NER FN) / Named GT mentions",
                       "undetected_lowercase": "The span of a lowercase GT mention was not linked / Named lowercase GT mentions",
                       "undetected_specificity": "FN and a part of the GT mention was linked to an arbitrary entity / Named GT mentions containing whitespace(s)",
                       "undetected_overlap": "FN and the GT span overlaps with a predicted span / Named uppercase GT mentions",
                       "undetected_other": "Other detection error / Named uppercase GT mentions",
                       "disambiguation": "Detected, but wrong entity linked / Detected",
                       "disambiguation_demonym": "FN from a list of demonyms (German, Germans, ...) / All demonym GT mentions",
                       "disambiguation_partial_name": "FN and the GT mention is part of the entity name / Named GT mentions where the mention is a part of the entity name",
                       "disambiguation_metonymy": "Predicted and most popular candidate are locations, but ground truth is not / Most popular candidate is a location, but ground truth is not",
                       "disambiguation_rare": "Most popular candidate is wrongly predicted / Detected mentions where the most popular candidate is not the correct entity",
                       "disambiguation_other": "Other disambiguation error",
                       "false_detection": "Prediction of a span which has no ground truth entity",
                       "abstraction": "Lowercase named FP that does not overlap with a GT mention",
                       "unknown_named_entity": "Uppercase mention wrongly linked, where the ground truth is either Unknown or has no label at all",
                       "false_detection_other": "Other false detection",
                       "hyperlink": "FN where the mention is a hyperlink / GT mentions that are hyperlinks",
                       "span_wrong": "FP where the predicted span overlaps with a GT mention with the same entity id / Predicted mentions",
                       "wrong_candidates": "A GT mention was recognized but the GT entity is not among the candidates / Named detected",
                       "multi_candidates": "A GT mention was recognized and the GT entity is one of the candidates, but the wrong candidate was selected / Named detected where the GT entity is one of multiple candidates",
                       "non_entity_coreference": "FP mentions in {It, it, This, this, That, that, Its, its}",
                       "referenced_wrong": "FN, the last named GT mention of the GT entity was linked to the same, wrong entity / Correct references",
                       "wrong_reference": "FN, the last named GT mention of the GT entity was not linked or linked to a wrong entity / Linked GT coreference mentions",
                       "no_reference": "FN, mention was not linked / GT coreference mentions",
                       "all": "All errors. TP: correct span, correct link; FP: incorrect span or correct span but wrong link; FN: GT span was not recognized or wrong link",
                       "NER": "Named mention span errors. TP: correct span; FP: predicted span does not match any GT span; FN: GT span does not match any predicted span",
                       "coreference": "All coreference errors (the &lt;type&gt; and pronouns)",
                       "named": "All errors excluding coreference",
                       "nominal": "'the &lt;type&gt;' errors",
                       "pronominal": "Pronoun errors",
                       "errors": "Error categories",
                       "coreference_errors": "Coreference error categories"};

mention_type_headers = {"entity": ["entity_named", "entity_other"],
                        "coref": ["nominal", "pronominal"],
                        "entity_named": ["entity_named"],
                        "entity_other": ["entity_other"],
                        "nominal": ["nominal"],
                        "pronominal": ["pronominal"]};

show_mentions = {"entity_named": true, "entity_other": true, "nominal": true, "pronominal": true};

benchmark_names = ["wiki-ex", "conll", "conll-dev", "conll-test", "ace", "msnbc", "newscrawl", "msnbc-original", "ace-original"];

error_category_mapping = {"undetected": ["UNDETECTED"],
    "undetected_lowercase": ["UNDETECTED_LOWERCASE"],
    "wrong_candidates": ["WRONG_CANDIDATES"],
    "":  ["MULTI_CANDIDATES_CORRECT"],
    "multi_candidates": ["MULTI_CANDIDATES_WRONG"],
    "undetected_specificity": ["SPECIFICITY"],
    "undetected_overlap": ["UNDETECTED_OVERLAP"],
    "undetected_other": ["UNDETECTED_OTHER"],
    "disambiguation": ["DISAMBIGUATION"],
    "": ["DEMONYM_CORRECT"],
    "disambiguation_demonym": ["DEMONYM_CORRECT", "DEMONYM_WRONG"],
    "": ["PARTIAL_NAME_CORRECT"],
    "disambiguation_metonymy": ["METONYMY_CORRECT", "METONYMY_WRONG"],
    "disambiguation_partial_name": ["PARTIAL_NAME_CORRECT", "PARTIAL_NAME_WRONG"],
    "disambiguation_rare": ["RARE_CORRECT", "RARE_WRONG"],
    "disambiguation_other": ["DISAMBIGUATION_OTHER"],
    "false_detection": ["FALSE_DETECTION"],
    "abstraction": ["ABSTRACTION"],
    "unknown_named_entity": ["UNKNOWN_NAMED_ENTITY"],
    "false_detection_other": ["FALSE_DETECTION_OTHER"],
    "": ["HYPERLINK_CORRECT"],
    "hyperlink": ["HYPERLINK_WRONG"],
    "span_wrong": ["SPAN_WRONG"],
    "non_entity_coreference": ["NON_ENTITY_COREFERENCE"],
    "referenced_wrong": ["COREFERENCE_REFERENCED_WRONG"],
    "wrong_reference": ["COREFERENCE_WRONG_REFERENCE"],
    "no_reference": ["COREFERENCE_NO_REFERENCE"]}

$("document").ready(function() {
    // Elements from the HTML document for later usage.
    benchmark_select = document.getElementById("benchmark");
    article_select = document.getElementById("article");

    show_all_articles_flag = false;

    evaluation_cases = {};
    articles_data = {};

    selected_approach_names = [];
    selected_rows = [];
    selected_cells = [];
    reset_selected_error_categories();
    reset_selected_types();

    sorting_variables = {"evaluation": {}, "type_evaluation": {}}
    for (div in sorting_variables) {
        sorting_variables[div]["column_index"] = null;
        sorting_variables[div]["descending"] = true;
    }

    set_benchmark_select_options();

    // Filter results by regex in input field #result-regex (from SPARQL AC evaluation)
    // Filter on key up
    $("input#result-filter").focus();
    $("input#result-filter").keyup(function() {
        filter_table_rows();
    });
    // Filter on radio button change
    $("input.match_type").change(function() {
        filter_table_rows();
    })

    // Show/Hide certain mentions in linked articles
    // Set flags according to current checkbox status
    $.each(show_mentions, function(key) {
        show_mentions[key] = $("#show_" + key).is(":checked");
    });

    // On article results checkbox change
    $("#article_checkboxes input").change(function() {
        var id = $(this).attr("id");
        var suffix = id.substring(id.indexOf("_") + 1, id.length);
        var checked = $(this).is(":checked");
        $.each(show_mentions, function(key) {
            if (key == suffix) {
                show_mentions[key] = checked;
            }
        });
        show_article(selected_approach_names);
    });

    // Highlight error category cells on hover
    $("#evaluation").on("mouseenter", "td", function() {
        if ($(this).attr('class')) {  // System column has no class attribute
            var classes = $(this).attr('class').split(/\s+/);
            if (classes.length > 1 && classes[1] in error_category_mapping) {
                $(this).addClass("hovered");
            }
        }
    });
    $("#evaluation").on("mouseleave", "td", function() {
        $(this).removeClass("hovered");
    });

    // Highlight all cells in a row belonging to the same mention_type on hover
    $("#evaluation").on("mouseenter", "td", function() {
        if ($(this).attr('class')) {  // System column has no class attribute
            var cls = $(this).attr('class').split(/\s+/)[0];
            if (cls in mention_type_headers) {
                // Mark all cells in the corresponding row with the corresponding class
                $(this).closest('tr').find('.' + cls).each(function(index) {
                    $(this).addClass("hovered");
                });
            }
        }
    });
    $("#evaluation").on("mouseleave", "td", function() {
        if ($(this).attr('class')) {  // System column has no class attribute
            var cls = $(this).attr('class').split(/\s+/)[0];
            if (cls in mention_type_headers) {
                $(this).closest('tr').find('.' + cls).each(function(index) {
                    $(this).removeClass("hovered");
                });
            }
        }
    });

    // Highlight all cells in a row belonging to the same type on hover
    $("#type_evaluation").on("mouseenter", "td", function() {
        if ($(this).attr('class')) {  // System column has no class attribute
            var cls = $(this).attr('class').split(/\s+/)[0];
            // Mark all cells in the corresponding row with the corresponding class
            $(this).closest('tr').find('.' + cls).each(function(index) {
                $(this).addClass("hovered");
            });
        }
    });
    $("#type_evaluation").on("mouseleave", "td", function() {
        if ($(this).attr('class')) {  // System column has no class attribute
            var cls = $(this).attr('class').split(/\s+/)[0];
            $(this).closest('tr').find('.' + cls).each(function(index) {
                $(this).removeClass("hovered");
            });
        }
    });
});

function set_benchmark_select_options() {
    /*
    Set the options for the benchmark selector element to the names of the benchmarks in the given directory.
    */
    // Retrieve file path of .results files in each folder
    benchmarks = [];
    $.get("benchmarks", function(folder_data) {
        $(folder_data).find("a").each(function() {
            file_name = $(this).attr("href");
            if (file_name.startsWith("benchmark_labels")) {
                benchmarks.push(file_name);
            }
        });
    }).then(function() {
        benchmarks.sort();
        for (bi in benchmarks) {
            benchmark = benchmarks[bi];
            var option = document.createElement("option");
            option.text = benchmark.split("_")[2].split(".")[0];
            option.value = benchmark;
            benchmark_select.add(option);
        }
        // Set default value to "wiki-ex".
        $('#benchmark option:contains("wiki-ex")').prop('selected',true);
        show_benchmark_results();
    });
}

function reset_selected_error_categories() {
    /*
    Initialize or reset the selected error categories.
    The array contains one entry for each approach that can be compared.
    */
    selected_error_categories = new Array(MAX_SELECTED_APPROACHES).fill(null);
}

function reset_selected_types() {
    /*
    Initialize or reset the selected types.
    The array contains one entry for each approach that can be compared.
    */
    selected_types = new Array(MAX_SELECTED_APPROACHES).fill(null);
}

function show_benchmark_results() {
    /*
    Show overview table and set up the article selector for a selected benchmark.
    */
    benchmark_file = benchmark_select.value;
    benchmark_name = $("#benchmark option:selected").text();

    if (benchmark_file == "") {
        return;
    }

    // Remove previous evaluation table content
    $("#evaluation_tables table thead").empty();
    $("#evaluation_tables table tbody").empty();

    // Remove previous article evaluation content
    $("#prediction_overview").hide();
    evaluation_cases = [];

    // Build an overview table over all .results-files from the evaluation-results folder.
    build_overview_table("evaluation-results", benchmark_name);

    // Read the article and ground truth information from the benchmark.
    parse_benchmark(benchmark_file);
}

function filter_table_rows() {
    var filter_keywords = $.trim($("input#result-filter").val()).split(/\s+/);
    var match_type_and = $("#radio_and").is(":checked");
    $("#evaluation_tables tbody tr").each(function() {
        var name = $(this).children(":first-child").text();
        var show_row;
        if (match_type_and) {
            show_row = filter_keywords.every(keyword => name.search(keyword) != -1);
        } else {
            show_row = filter_keywords.some(keyword => name.search(keyword) != -1);
        }
        if (show_row) $(this).show(); else $(this).hide();
    });
}

function parse_benchmark(benchmark_file) {
    /*
    Read the articles and ground truth labels from the benchmark.

    Reads the file benchmarks/<benchmark_file> and adds each article to the list 'articles'.
    Each article is an object indentical to the parsed JSON-object.

    Calls set_article_select_options(), which sets the options for the article selector element.
    */
    // List of articles with ground truth information from the benchmark.
    articles = [];
    $.get("benchmarks/" + benchmark_file,
        function(data, status) {
            lines = data.split("\n");
            for (line of lines) {
                if (line.length > 0) {
                    json = JSON.parse(line);
                    articles.push(json);
                }
            }
            // Set options for the article selector element.
            set_article_select_options();
        }
    );
}

function set_article_select_options() {
    /*
    Set the options for the article selector element to the names of the articles from the list 'articles'.
    */
    // Empty previous options
    $("#article").empty();

    // Add default "All articles" option
    var option = document.createElement("option");
    option.text = "All articles (evaluated span only)";
    option.value = -1;
    article_select.add(option);

    // Create new options
    for (ai in articles) {
        article = articles[ai];
        option = document.createElement("option");
        // Shorten the article title if it's longer than 40 characters
        var title;
        if (article.title) {
            title = (article.title.length <= 40) ? article.title : article.title.substring(0, 40) + "..."
        } else {
            title = article.text.substring(0, Math.min(40, article.text.length)) + "...";
        }
        // Conll articles don't have a title. In that case use the first 40 characters of the article
        option.text = title;
        option.value = ai;
        article_select.add(option);
    }
}

function show_article_link() {
    /*
    Link the currently selected article in the element #article_link.
    */
    $("#article_link").html("<a href=\"" + article.url + "\" target=\"_blank\">Wikipedia article</a>");
    $("#article_link").show();
}

function is_correct_optional_case(eval_case) {
    /*
    Return true iff the given evaluation case is a correctly linked optional case.
    */
    if ("true_entity" in eval_case) {
        if ("optional" in eval_case.true_entity && eval_case.true_entity.optional) {
            if ("predicted_entity" in eval_case && eval_case.predicted_entity.entity_id == eval_case.true_entity.entity_id) {
                // Optional TP are correct
                return true;
            } else if (!("predicted_entity" in eval_case)) {
                // Optional FN are correct
                return true;
            }
        } else if ("type" in eval_case.true_entity && ["QUANTITY", "DATETIME"].includes(eval_case.true_entity.type)) {
            if ("predicted_entity" in eval_case && "type" in eval_case.predicted_entity && eval_case.true_entity.type == eval_case.predicted_entity.type) {
                // True entity is of type QUANTITY or DATETIME and predicted entity is of the same type -> correct TP
                return true;
            } else if (!("predicted_entity" in eval_case)) {
                // True entity is of type QUANTITY or DATETIME and no entity was predicted -> correct FN
                return true;
            }
        }
    }
    return false;
}

function is_optional_case(eval_case) {
    /*
    Returns true iff the given evaluation case is optional, a datetime or a quantity.
    */
     return "true_entity" in eval_case && (eval_case.true_entity.optional ||
                                           ["QUANTITY", "DATETIME"].includes(eval_case.true_entity.type));
}

function show_annotated_text(approach_name, textfield, selected_error_category, selected_type) {
    /*
    Generate annotations and tooltips for predicted and groundtruth mentions of the selected approach and article
    and show them in the textfield.
    */
    if (show_all_articles_flag) {
        var annotated_texts = [];
        for (var i=0; i < articles.length; i++) {
            var annotations = get_annotations(i, approach_name);
            annotated_texts.push(annotate_text(articles[i].text, annotations, articles[i].links, articles[i].evaluation_span, selected_error_category, selected_type));
        }
        annotated_text = "";
        for (var i=0; i < annotated_texts.length; i++) {
            annotated_text += "<br><br>" + "********** " + articles[i].title + " **********<br>";
            annotated_text += annotated_texts[i];
        }
    } else {
        var annotations = get_annotations(selected_article_index, approach_name);
        var annotated_text = annotate_text(article.text, annotations, article.links, [0, article.text.length], selected_error_category, selected_type);
    }
    textfield.html(annotated_text);
}

function get_annotations(article_index, approach_name) {
    /*
    Generate annotations for the predicted entities of the selected approach and article.

    This method first combines the predictions outside the evaluation span (from the file <approach>.jsonl)
    with the evaluated predictions inside the evaluation span (from the file <approach>.cases),
    and then generates annotations for all of them.
    */
    var article_cases = evaluation_cases[approach_name][article_index];  // information from the .cases file
    var article_data = articles_data[approach_name][article_index];  // information from the .jsonl file

    var child_label_to_parent = {};
    var label_id_to_label = {};
    for (eval_case of article_cases) {
        // Build the parent mapping
        if ("true_entity" in eval_case && eval_case.true_entity.children) {
            label_id_to_label[eval_case.true_entity.id] = eval_case.true_entity;
            for (child_id of eval_case.true_entity.children) {
                child_label_to_parent[child_id] = eval_case.true_entity.id;
            }
        }
    }

    // evaluation span
    var evaluation_begin = article_data.evaluation_span[0];
    var evaluation_end = article_data.evaluation_span[1];

    // list of all predicted mentions (inside and outside the evaluation span)
    var mentions = [];

    // get the mentions before the evaluation span
    for (prediction of article_data.entity_mentions) {
        if (prediction.span[1] < evaluation_begin) {
            mentions.push(prediction);
        }
    }
    // get the cases inside the evaluation span from the cases list
    for (eval_case of article_cases) {
        mentions.push(eval_case);
    }
    // get the mentions after the evaluation span
    for (prediction of article_data.entity_mentions) {
        if (prediction.span[0] >= evaluation_end) {
            mentions.push(prediction);
        }
    }

    // list with tooltip information for each mention
    var annotations = {};
    var prediction_spans = [];
    for (mention of mentions) {
        // TODO: Remove this once this can be controlled via selecting the columns
        if (mention.mention_type && mention.mention_type.toLowerCase() in show_mentions) {
            if (!show_mentions[mention.mention_type.toLowerCase()]) {
                continue;
            }
        }
        if (mention.factor == 0) {
            // Do not display overlapping mentions
            continue;
        }

        var gt_entity_id = null;
        var gt_entity_name = null;
        var gt_entity_type = null;
        var parent_text = null;

        var pred_entity_id = null;
        var pred_entity_name = null;
        var pred_entity_type = null;
        var pred_by = null;

        var classes = [];

        // mention is an evaluated case
        if ("predicted_entity" in mention || "true_entity" in mention) {
            // Avoid overlapping prediction_spans: Keep the larger one.
            // Assume that predictions are sorted by span start (but not by span end)
            if ("predicted_entity" in mention) {
                var last_index = prediction_spans.length - 1;
                if (prediction_spans.length > 0 && prediction_spans[last_index][1] > mention.span[0]) {
                    // Overlap detected.
                    var previous_span_length = prediction_spans[last_index][1] - prediction_spans[last_index][0];
                    var current_span_length = mention.span[1] - mention.span[0];
                    if (previous_span_length >= current_span_length) {
                        // Previous span is longer than current span so discard current prediction
                        continue
                    } else {
                        delete annotations[prediction_spans[last_index]];
                        prediction_spans.splice(-1);
                    }
                }
                prediction_spans.push(mention.span);
            }

            if ("true_entity" in mention && mention.true_entity.entity_id.startsWith("Unknown")) {
                // GT entity is NIL
                classes.push(ANNOTATION_CLASS_UNKNOWN);
                if ("predicted_entity" in mention) {
                    classes.push(ANNOTATION_CLASS_FP);
                }
            } else if (is_correct_optional_case(mention)) {
                classes.push(ANNOTATION_CLASS_OPTIONAL);
                if ("predicted_entity" in mention) {
                    classes.push(ANNOTATION_CLASS_CORRECT_OPTIONAL);
                }
            } else if ("predicted_entity" in mention) {
                 if ("true_entity" in mention && !mention.true_entity.entity_id.startsWith("Unknown")) {
                     if (mention.true_entity.entity_id == mention.predicted_entity.entity_id) {
                        // predicted the true entity
                        classes.push(ANNOTATION_CLASS_TP);
                    } else {
                        // predicted the wrong entity
                        classes.push(ANNOTATION_CLASS_FP);
                        if (is_optional_case(mention)) {
                            classes.push(ANNOTATION_CLASS_OPTIONAL);
                        } else {
                            classes.push(ANNOTATION_CLASS_FN);
                        }
                    }
                } else {
                    // wrong span
                    classes.push(ANNOTATION_CLASS_FP);
                }
            } else {
                classes.push(ANNOTATION_CLASS_FN);
            }

            if ("true_entity" in mention) {
                // Use the type of the parent entity because this is the type that counts in the evaluation.
                var curr_label_id = mention.true_entity.id;
                while (curr_label_id in child_label_to_parent) {
                    curr_label_id = child_label_to_parent[curr_label_id];
                }
                gt_entity_type = label_id_to_label[curr_label_id].type;
                // Get text of parent span
                if (curr_label_id != mention.true_entity.id) {
                    parent_span = label_id_to_label[curr_label_id].span;
                    parent_text = articles[article_index].text.substring(parent_span[0], parent_span[1]);
                }
                gt_entity_id = mention.true_entity.entity_id;
                gt_entity_name = mention.true_entity.name;
            }
            if ("predicted_entity" in mention) {
                pred_entity_id = mention.predicted_entity.entity_id;
                pred_entity_name = mention.predicted_entity.name;
                pred_entity_type = mention.predicted_entity.type;
                pred_by = mention.predicted_by;
                if (classes.includes(ANNOTATION_CLASS_TP)) {
                    // Use the type of the parent entity because this is the type that counts in the evaluation.
                    pred_entity_type = gt_entity_type;
                }
            }
        } else {
            // mention is outside the evaluation span
            classes.push(ANNOTATION_CLASS_UNEVALUATED);
            pred_entity_id = mention.id;
            pred_entity_name = null;
            pred_entity_type = null;
            pred_by = mention.linked_by;
        }
        var mention_type = (mention.mention_type) ? mention.mention_type.toLowerCase() : null;
        var annotation = {
            "span": mention.span,
            "classes": classes,
            "error_labels": mention.error_labels,
            "gt_entity_id": gt_entity_id,
            "gt_entity_name": gt_entity_name,
            "gt_entity_type": gt_entity_type,
            "parent_text": parent_text,
            "pred_entity_id": pred_entity_id,
            "pred_entity_name": pred_entity_name,
            "pred_entity_type": pred_entity_type,
            "predicted_by": pred_by,
            "mention_type": mention_type
        };
        annotations[mention.span] = annotation;
    }
    annotations = Object.values(annotations);
    return annotations
}

function copy(object) {
    /*
    Get a copy of the given object
    */
    return JSON.parse(JSON.stringify(object));
}

function annotate_text(text, annotations, links, evaluation_span, selected_error_category, selected_type) {
    /*
    Generate tooltips for the given annotations and hyperlinks for the given links.
    Tooltips and hyperlinks can overlap.

    Arguments:
    - text: The original text without tooltips or hyperlinks.
    - annotations: A sorted (by span) list of objects containing tooltip information
    - links: A sorted (by span) list of tuples (span, target_article)
    - evaluation_span: The span of the article that can be evaluated
    - selected_error_categores: selected error categories for the corresponding approach
    - selected_type: selected type for the corresponding approach

    First the overlapping annotations and links get combined to combined_annotations.
    Second, the annotations with links are added to the text and a tooltip is generated for each annotation.
    */
    // Separate mention annotations into two distinct lists such that any one list does not contain annotations that
    // overlap.
    var only_groundtruth_annotations = [];
    var non_groundtruth_annotations = [];
    for (var i=0; i<annotations.length; i++) {
        var ann = annotations[i];
        if (ann.gt_entity_id) {
            only_groundtruth_annotations.push([copy(ann.span), ann]);
        } else {
            non_groundtruth_annotations.push([copy(ann.span), ann]);
        }
    }

    // Transform hyperlinks into a similar format as the mention annotations
    var new_links = [];
    for (link of links) { new_links.push([copy(link[0]), {"span": link[0], "link": link[1]}]); }

    // STEP 1: Combine overlapping annotations and links.
    // Consumes the first element from the link list or annotation list, or a part from both if they overlap.
    var combined_annotations = combine_overlapping_annotations(only_groundtruth_annotations, non_groundtruth_annotations, selected_error_category, selected_type);
    // Links must be the last list that is added such that they can only be the inner most annotations, because <div>
    // tags are not allowed within <a> tags, but the other way round is valid.
    combined_annotations = combine_overlapping_annotations(combined_annotations, new_links, selected_error_category, selected_type);

    // Text should only be the text within the given evaluation span (Careful: This is the entire article if a
    // single article is supposed to be shown and the article evaluation span if all articles are supposed to be
    // shown)
    text = text.substring(0, evaluation_span[1]);

    // STEP 2: Add the combined annotations and links to the text.
    // This is done in reverse order so that the text before is always unchanged. This allows to use the spans as given.
    for (annotation of combined_annotations.reverse()) {
        span = annotation[0];
        if (span[1] > evaluation_span[1]) {
            continue;
        } else if (span[0] < evaluation_span[0]) {
            break;
        }
        // annotation is a tuple with (span, annotation_info)
        annotation = annotation[1];
        before = text.substring(0, span[0]);
        snippet = text.substring(span[0], span[1]);
        after = text.substring(span[1]);
        replacement = generate_annotation_html(snippet, annotation, selected_error_category, selected_type);
        text = before + replacement + after;
    }
    text = text.substring(evaluation_span[0], text.length);
    text = text.replaceAll("\n", "<br>");
    return text;
}

function generate_annotation_html(snippet, annotation, selected_error_category, selected_type) {
    /*
    Generate html snippet for a given annotation. A hyperlink is also regarded as an annotation
    and can be identified by the property "link". Inner annotations, e.g. hyperlinks contained in
    a mention annotation, nested mention annotations are contained given by the property "inner_annotation".
    */
    var inner_annotation = snippet;

    if ("inner_annotation" in annotation) {
        inner_annotation = generate_annotation_html(snippet, annotation.inner_annotation, selected_error_category, selected_type);
    }

    if ("link" in annotation) {
        return "<a href=\"https://en.wikipedia.org/wiki/" + annotation.link + "\" target=\"_blank\">" + inner_annotation + "</a>";
    }

    // Add tooltip
    var tooltip_classes = "tooltiptext";
    var tooltip_header_text = "";
    var tooltip_case_type_html = "";
    var tooltip_body_text = "";
    var tooltip_footer_html = "";
    if (annotation.classes.includes(ANNOTATION_CLASS_TP)) {
        wikidata_url = "https://www.wikidata.org/wiki/" + annotation.gt_entity_id;
        entity_link = "<a href=\"" + wikidata_url + "\" target=\"_blank\">" + annotation.gt_entity_id + "</a>";
        if (annotation.gt_entity_name != null) {
            tooltip_header_text += annotation.gt_entity_name + " (" + entity_link + ")";
        } else {
            tooltip_header_text += entity_link;
        }
    } else {
        if (annotation.pred_entity_id) {
            var wikidata_url = "https://www.wikidata.org/wiki/" + annotation.pred_entity_id;
            var entity_link = "<a href=\"" + wikidata_url + "\" target=\"_blank\">" + annotation.pred_entity_id + "</a>";
            tooltip_header_text += "Prediction: " + annotation.pred_entity_name + " (" + entity_link + ")";
        }
        if (annotation.gt_entity_id) {
            var wikidata_url = "https://www.wikidata.org/wiki/" + annotation.gt_entity_id;
            var entity_link = "<a href=\"" + wikidata_url + "\" target=\"_blank\">" + annotation.gt_entity_id + "</a>";
            if (tooltip_header_text) { tooltip_header_text += "<br>"; }
            tooltip_header_text += "Groundtruth: " + annotation.gt_entity_name + " (" + entity_link + ")";
            if (!annotation.pred_entity_id) { tooltip_classes += " below"; }
        }
    }
    // Add case type boxes and annotation case type class to tooltip
    for (ann_class of annotation.classes) {
        if ([ANNOTATION_CLASS_TP, ANNOTATION_CLASS_FN, ANNOTATION_CLASS_FP].includes(ann_class)) {
            tooltip_case_type_html += "<div class=\"case_type_box " + ann_class + "\">" + ann_class.toUpperCase() + "</div>";
            tooltip_classes += " " + ann_class;
        }
    }
    if (annotation.predicted_by) {
        tooltip_body_text += "predicted by " + annotation.predicted_by + "<br>";
    }
    if (annotation.parent_text) {
        tooltip_body_text += "parent text: \"" + annotation.parent_text + "\"<br>";
    }
    // Add error category tags
    if (annotation.error_labels && annotation.error_labels.length > 0) {
        for (var e_i = 0; e_i < annotation.error_labels.length; e_i += 1) {
            var error_label = annotation.error_labels[e_i];
            error_label = error_label.replace(/_/g, " ").toLowerCase();
            if (e_i > 0) {
                tooltip_footer_html += " ";
            }
            tooltip_footer_html += "<span class=\"error_category_tag\">" + error_label + "</span>";
        }
    }
    // Use transparent version of the color, if an error category or type is selected
    // and the current annotation does not have a corresponding error category or type label
    var lowlight_classes = "";
    if (selected_error_category && annotation.error_labels) {
        lowlight_classes = "gt_lowlight pred_lowlight";
        for (selected_category of selected_error_category) {
            if (annotation.error_labels.includes(selected_category) || annotation.mention_type == selected_category) {
                lowlight_classes = "";
                break;
            }
        }
    } else if (selected_type) {
        var pred_type_selected = annotation.pred_entity_type && annotation.pred_entity_type.split("|").includes(selected_type);
        var gt_type_selected = annotation.gt_entity_type && annotation.gt_entity_type.split("|").includes(selected_type);
        if (!pred_type_selected) {
            lowlight_classes += "pred_lowlight ";
        }
        if (!gt_type_selected) {
            lowlight_classes += "gt_lowlight ";
        }
    }

    var replacement = "<span class=\"annotation " + annotation.classes.join(" ") + " " + lowlight_classes + "\">";
    replacement += inner_annotation;
    replacement += "<div class=\"" + tooltip_classes + "\">";
    replacement += "<div class=\"header\">";
    replacement += "<div class=\"left\">" + tooltip_header_text + "</div>";
    replacement += "<div class=\"right\">" + tooltip_case_type_html + "</div>";
    replacement += "</div>";
    replacement += "<div class=\"body\">" + tooltip_body_text + "</div>";
    replacement += "<div class=\"footer\">" + tooltip_footer_html + "</div>";
    replacement += "</div>";
    replacement += "</span>";

    return replacement;
}

function combine_overlapping_annotations(list1, list2) {
    /*
    Combine two lists of potentially overlapping and nested annotations into a single list.
    Overlaps are resolved by splitting annotations at the overlap into two.
    Nestings are resolved by adding the inner annotation to the outer annotation via the
    property "inner_annotation".

    NOTE: Links must be the last list that is added such that they can only be the inner-most
    annotations, because <div> tags are not allowed within <a> tags.
    */
    var combined_annotations = [];
    while (list1.length > 0 || list2.length > 0) {
        if (list1.length == 0) {
            var list2_item = list2.shift();
            combined_annotations.push([list2_item[0], list2_item[1]]);
        } else if (list2.length == 0) {
            var list1_item = list1.shift();
            combined_annotations.push([list1_item[0], list1_item[1]]);
        } else {
            var list1_item = list1[0];
            var list2_item = list2[0];
            var list1_item_span = list1_item[0];
            var list2_item_span = list2_item[0];
            if (list2_item_span[0] < list1_item_span[0]) {
                // Add element from second list
                var list2_item_end = Math.min(list2_item_span[1], list1_item_span[0]);
                combined_annotations.push([[list2_item_span[0], list2_item_end], list2_item[1]]);
                if (list2_item_end == list2_item_span[1]) {
                    list2.shift();
                } else {
                    list2[0][0][0] = list2_item_end;
                }
            } else if (list1_item_span[0] < list2_item_span[0]) {
                // Add element from first list
                var list1_item_end = Math.min(list1_item_span[1], list2_item_span[0]);
                combined_annotations.push([[list1_item_span[0], list1_item_end], list1_item[1]]);
                if (list1_item_end == list1_item_span[1]) {
                    list1.shift();
                } else {
                    list1_item_span[0] = list1_item_end;
                }
            } else {
                // Add both
                var list1_item_ann = copy(list1_item[1]);
                var most_inner_ann = list1_item_ann;
                // Add element from second list as inner-most annotation of element from first list
                while ("inner_annotation" in most_inner_ann) {
                    most_inner_ann = most_inner_ann["inner_annotation"];
                }
                most_inner_ann["inner_annotation"] = list2_item[1];
                var list1_item_end = Math.min(list1_item_span[1], list2_item_span[1]);
                combined_annotations.push([[list1_item_span[0], list1_item_end], list1_item_ann]);
                if (list1_item_end == list2_item_span[1]) {
                    list2.shift();
                } else {
                    list2[0][0][0] = list1_item_end;
                }
                if (list1_item_end == list1_item_span[1]) {
                    list1.shift();
                } else {
                    list1[0][0][0] = list1_item_end;
                }
            }
        }
    }
    return combined_annotations;
}

async function show_article(selected_approaches) {
    /*
    Generate the ground truth textfield and predicted text field for the selected article
    (or all articles if this option is selected) and approach.
    */
    console.log("show_article() called for selected approaches", selected_approaches, "and evaluation cases for", Object.keys(evaluation_cases));

    selected_article_index = article_select.value;

    if (selected_article_index == -1) {
        show_all_articles_flag = true;
        $("#article_link").hide();
    } else {
        show_all_articles_flag = false;
        article = articles[selected_article_index];

        if (article.url) {
            show_article_link();
        } else {
            $("#article_link").hide();
        }
    }

    $("#prediction_overview").show();
    var columns = $("#prediction_overview tbody tr td");
    var column_headers = $("#prediction_overview thead tr th");
    var column_idx = 0;

    var iteration = 0;
    while (!(selected_approaches[0] in evaluation_cases) || evaluation_cases[selected_approaches[0]].length == 0) {
        if (iteration >= 10) {
            console.log("ERROR: Stop waiting for result.");
            $(columns[column_idx]).html("<b class='warning'>No approach selected or no file with cases found.</b>");
            return;
        }
        console.log("WARNING: selected approach[0]", selected_approaches[0], "not in evaluation cases. Waiting for result.");
        $(column_headers[column_idx]).text("");
        $(columns[column_idx]).html("<b>Waiting for results...</b>");
        column_idx++;
        for (var i=column_idx; i<columns.length; i++) {
            hide_table_column("prediction_overview", i);
        }
        column_idx = 0;
        await new Promise(r => setTimeout(r, 1000));
        iteration++;
    }

    // Show columns
    // Show first prediction column
    show_annotated_text(selected_approaches[0], $(columns[column_idx]), selected_error_categories[0], selected_types[0]);
    $(column_headers[column_idx]).text(selected_approaches[0]);
    show_table_column("prediction_overview", column_idx);
    column_idx++;
    if(is_compare_checked() && selected_approaches.length > 1) {
        // Show second prediction column
        show_annotated_text(selected_approaches[1], $(columns[column_idx]), selected_error_categories[1], selected_types[1]);
        $(column_headers[column_idx]).text(selected_approaches[1]);
        show_table_column("prediction_overview", column_idx);
        column_idx++;
    }

    // Hide unused columns
    for (var i=column_idx; i<columns.length; i++) {
        hide_table_column("prediction_overview", i);
    }

    // Set column width
    var width_percentage = 100 / column_idx;
    $("#prediction_overview th, #prediction_overview td").css("width", width_percentage + "%");
}

function build_overview_table(path, benchmark_name) {
    /*
    Build the overview table from the .results files found in the subdirectories of the given path.
    */
    folders = [];
    result_files = {};
    result_array = [];
    var urls = [];
    $.get(path, function(data) {
        // Get all folders from the evaluation results directory
        $(data).find("a").each(function() {
            name = $(this).attr("href");
            name = name.substring(0, name.length - 1);
            folders.push(name);
        });
    }).done(function() {
        // Retrieve file path of .results files for the selected benchmark in each folder
        $.when.apply($, folders.map(function(folder) {
            return $.get(path + "/" + folder, function(folder_data) {
                $(folder_data).find("a").each(function() {
                    file_name = $(this).attr("href");
                    // This assumes the benchmark is specified in the last dot separated column before the
                    // file extension if it is not our wiki-ex benchmark.
                    benchmark = file_name.split(".").slice(-2)[0];
                    benchmark_match = ((benchmark_name == "wiki-ex" && !benchmark_names.includes(benchmark)) || benchmark == benchmark_name);
                    if (file_name.endsWith(RESULTS_EXTENSION) && benchmark_match) {
                        var url = path + "/" + folder + "/" + file_name;
                        urls.push(url);
                    }
                });
            });
        })).then(function() {
            // Retrieve contents of each .results file for the selected benchmark and store it in an array
            $.when.apply($, urls.map(function(url) {
                return $.getJSON(url, function(results) {
                    var approach_name = url.substring(url.lastIndexOf("/") + 1, url.length - RESULTS_EXTENSION.length);
                    result_files[approach_name] = url.substring(0, url.length - RESULTS_EXTENSION.length);
                    result_array.push([approach_name, results]);
                });
            })).then(function() {
                // Sort the result array
                result_array.sort(compare_approach_names);
                // Add table header and checkboxes
                result_array.forEach(function(result_tuple) {
                    var approach_name = result_tuple[0];
                    var results = result_tuple[1];
                    if (!$('#evaluation table thead').html()) {
                        // Add table header if it has not yet been added
                        var table_header = get_table_header(results, "evaluation");
                        $('#evaluation table thead').html(table_header);
                    }
                    if (!$('#type_evaluation table thead').html() && results["by_type"]) {
                        // Add table header for type evaluation table if it has not yet been added
                        var table_header = get_table_header(results["by_type"], "type_evaluation");
                        $('#type_evaluation table thead').html(table_header);
                    }

                    if (!$('#evaluation .checkboxes').html()) {
                        // Add checkboxes if they have not yet been added
                        add_checkboxes(results, "evaluation");
                    }
                    if (!$('#type_evaluation .checkboxes').html() && results["by_type"]) {
                        // Add checkboxes if they have not yet been added
                        add_checkboxes(results["by_type"], "type_evaluation");
                    }
                });
                // Add table body
                build_evaluation_table_body(result_array, "evaluation");
                build_evaluation_table_body(result_array, "type_evaluation");

                // Sort the table according to previously chosen sorting
                for (div in sorting_variables) {
                    var sort_column_index = sorting_variables[div]["column_index"];
                    var sort_descending = sorting_variables[div]["sort_descending"];
                    if (sort_column_index != null) {
                        var sort_column_header = $('#' + div + ' table thead tr:nth-child(2) th:nth-child(' + sort_column_index + ')');
                        // Hack to get the right sort order which is determined by
                        // whether the column header already has the class "descending"
                        if (!sort_descending) sort_column_header.addClass("desc");
                        sort_table(sort_column_header, div);
                    }
                }
            });
        });
    });
}

function build_evaluation_table_body(result_list, div_id) {
    /*
    Build the table body.
    Show / Hide rows and columns according to checkbox state and filter-result input field.
    */
    // Add table rows in new sorting order
    result_list.forEach(function(result_tuple) {
        var approach_name = result_tuple[0];
        var results = result_tuple[1];
        if (div_id == "type_evaluation") results = results["by_type"];
        if (results) {
            var row = get_table_row(approach_name, results, div_id);
            $('#' + div_id + ' table tbody').append(row);
        }
    });

    // Show / Hide columns according to checkbox state
    $("input[class^='checkbox_']").each(function() {
        show_hide_columns(this, div_id);
    })

    // Show / Hide rows according to filter-result input field
    filter_table_rows();
}

function add_checkboxes(json_obj, div_id) {
    /*
    Add checkboxes for showing / hiding columns.
    */
    $.each(json_obj, function(key) {
        var class_name = get_class_name(key);
        if (key != "by_type") {
            var title = get_title_from_key(key);
            var checked = (class_name == "all") ? "checked" : ""
            var checkbox_html = "<input type=\"checkbox\" class=\"checkbox_" + class_name + "\" onchange=\"show_hide_columns(this, '" + div_id + "')\" " + checked + ">";
            checkbox_html += "<label>" + title + "</label>";
            $("#" + div_id + " .checkboxes").append(checkbox_html);
        }
    });
}

function show_hide_columns(element, div_id) {
    /*
    This function should be called when the state of a checkbox is changed.
    This can't be simply added in on document ready, because checkboxes are added dynamically.
    */
    var col_class = $(element).attr("class");
    col_class = col_class.substring(col_class.indexOf("_") + 1, col_class.length);
    var column = $("#" + div_id + " ." + col_class);
    if($(element).is(":checked")) {
        column.show();
    } else {
        column.hide();
    }
}

function get_table_header(json_obj, div_id) {
    /*
    Get html for the table header.
    */
    var num_first_cols = json_obj.length;
    var first_row = "<tr><th onclick='produce_latex(\"" + div_id + "\")' class='produce_latex'>" + copy_latex_text + "</th>";
    var second_row = "<tr><th onclick='sort_table(this, \"" + div_id + "\")'>System<span class='sort_symbol'>&#9660</span></th>";
    $.each(json_obj, function(key) {
        if (key == "by_type") return;
        var colspan = 0;
        var class_name = get_class_name(key);
        $.each(json_obj[key], function(subkey) {
            if (!(ignore_headers.includes(subkey))) {
                second_row += "<th class='" + class_name + "' onclick='sort_table(this, \"" + div_id + "\")' data-array-key='" + key + "' data-array-subkey='" + subkey + "'><div class='tooltip'>" + get_title_from_key(subkey) + "<span class='sort_symbol'>&#9660</span>";
                var tooltip_text = get_header_tooltip_text(subkey);
                if (tooltip_text) {
                    second_row += "<span class='tooltiptext'>" + tooltip_text + "</span>";
                }
                second_row += "</div></th>";
                colspan += 1;
            }
        });
        first_row += "<th colspan=\"" + colspan + "\" class='" + class_name + "'><div class='tooltip'>" + get_title_from_key(key);
        var tooltip_text = get_header_tooltip_text(key);
        if (tooltip_text) {
            first_row += "<span class='tooltiptext'>" + tooltip_text + "</span>";
        }
        first_row += "</div></th>";
    });
    first_row += "</tr>";
    second_row += "</tr>";
    return first_row + second_row;
}

function get_table_row(approach_name, json_obj, div_id) {
    /*
    Get html for the table row with the given approach name and result values.
    */
    var row = "<tr onclick='on_row_click(this)'>";
    var onclick_str = " onclick='on_cell_click(this)'";
    row += "<td " + onclick_str + ">" + approach_name + "</td>";
    $.each(json_obj, function(key) {
        if (key == "by_type") return;
        var class_name = get_class_name(key);
        var tooltip_text = "";
        $.each(json_obj[key], function(subkey) {
            // Include only keys in the table, that are not on the ignore list
            if (!(ignore_headers.includes(subkey))) {
                var value = json_obj[key][subkey];
                if (value == null) {
                    // This means, the category does not apply to the given approach
                    value = "-";
                } else if (Object.keys(value).length > 0) {
                    // Values that consist not of a single number but of multiple
                    // key-value pairs are displayed in a single column.
                    var processed_value = "<div class='" + class_name + " tooltip'>";
                    var percentage = (value["errors"] / value["total"] * 100).toFixed(2);
                    processed_value += percentage + "%";
                    processed_value += "<span class='tooltiptext'>";
                    processed_value += value["errors"] + " / " + value["total"];
                    processed_value += "</span></div>";
                    value = processed_value;
                } else if (percentage_headers.includes(subkey)) {
                    // Get rounded percentage but only if number is a decimal < 1
                    processed_value = "<div class='" + class_name + " tooltip'>";
                    processed_value += (value * 100).toFixed(2) + "%";
                    // Create tooltip text
                    processed_value += "<span class='tooltiptext'>" + get_tooltip_text(json_obj[key]) + "</span></div>";
                    value = processed_value;
                } else {
                    Math.round(json_obj[key][subkey] * 100) / 100
                }
                var subclass_name = get_class_name(subkey);
                if (div_id == "type_evaluation") {
                    var data_string = "data-category='" + key + "'";
                } else {
                    if (key in mention_type_headers) {
                        var data_string = "data-category='" + class_name + "'";
                    } else {
                        var data_string = "data-category='" + subclass_name + "'";
                    }
                }
                row += "<td class='" + class_name + " " + subclass_name + "' " + data_string + onclick_str + ">" + value + "</td>";
            }
        });
    })
    row += "</tr>";
    return row;
}

function get_tooltip_text(json_obj) {
    tooltip_text = "TP: " + Math.round(json_obj["true_positives"] * 100) / 100 + "<br>";
    tooltip_text += "FP: " + Math.round(json_obj["false_positives"] * 100) / 100 + "<br>";
    tooltip_text += "FN: " + Math.round(json_obj["false_negatives"] * 100) / 100 + "<br>";
    tooltip_text += "GT: " + Math.round(json_obj["ground_truth"] * 100) / 100;
    return tooltip_text;
}

function get_header_tooltip_text(header_title) {
    if (header_title in header_descriptions) {
        return header_descriptions[header_title];
    }
    return "";
}

function get_class_name(text) {
    return text.toLowerCase().replace(/[ ,.#:]/g, "_");
}

function get_title_from_key(key) {
    key = key.replace(/Q[0-9]+:/g, "");
    return to_title_case(key.replace(/_/g, " "));
}

function to_title_case(str) {
    return str.replace(/\w\S*/g, function(txt) {
        return txt.charAt(0).toUpperCase() + txt.substr(1);
    });
}

function sort_table(column_header, div_id) {
    /*
    Sort table rows with respect to the selected column.
    This sorts the result_array, removes old table rows and adds them in the new ordering.
    */
    // Get list of values in the selected column
    // + 1 because nth-child indices are 1-based
    var col_index = $(column_header).parent().children().index($(column_header)) + 1;

    // Store the column index to apply the same sorting when selecting a different benchmark
    // Can't just store and use the column header itself since it's the header of the old table
    sorting_variables[div_id]["column_index"] = col_index;

    var key = $(column_header).data("array-key");
    var subkey = $(column_header).data("array-subkey");
    var col_values = [];
    var index = 0;
    var selected_approach_indices = [null, null];
    result_array.forEach(function(result_tuple) {
        var approach_name = result_tuple[0];
        if (selected_approach_names.includes(approach_name) && selected_rows.length > 0 && $(selected_rows[0]).closest("table").parent().attr("id") == div_id) {
            // Store the index in the result_array of the currently selected row
            // Keep the order in which the rows were selected
            selected_approach_indices[$.inArray(approach_name, selected_approach_names)] = index;
        }
        index += 1;
        var results = result_tuple[1];
        if (!key) {
            // System column has no attribute data-array-key. Sort by approach name.
            col_values.push(approach_name);
            return;
        }
        if (div_id == "type_evaluation") {
            results = results["by_type"];
        }
        var value = results[key][subkey]
        if (Object.keys(results[key][subkey]).length > 0) {
            // An error category contains two keys and the percentage is displayed, so sort by percentage
            value = (value["errors"] / value["total"] * 100).toFixed(2);
        }
        col_values.push(value);
     });

    // Store class name of currently selected cell
    var selected_cells_classes = [];
    for (var i=0;i<selected_rows.length; i++) {
        var cell_classes = $(selected_rows[i]).find("td.selected").attr("class");
        if (cell_classes) {
            cell_classes = cell_classes.split(/\s+/);
            cell_classes.pop();  // We don't want the "selected" class
            cell_classes = "." + cell_classes.join(".");
            selected_cells_classes.push(cell_classes)
        }
    }

    // Check if sorting should be ascending or descending
    var descending = !$(column_header).hasClass("desc");
    sorting_variables[div_id]["sort_descending"] = descending;

    // Get new sorting order of the row indices and create a new result array according to the new sorting
    if (col_index == 1) {
        sort_function = compare_approach_names;
    } else {
        sort_function = function(a, b) {a = parseFloat(a[0]); b = parseFloat(b[0]); return (isNaN(a)) ? 1 - isNaN(b) : b - a;};
    }
    const decor = (v, i) => [v, i];          // set index to value
    const undecor = a => a[1];               // leave only index
    const argsort = arr => arr.map(decor).sort(sort_function).map(undecor);
    var order = argsort(col_values);
    result_array = order.map(i => result_array[i]);

    // Remove asc/desc classes from all columns
    $("#" + div_id + " table th").each(function() {
        $(this).removeClass("desc");
        $(this).removeClass("asc");
    })

    if (descending) {
        // Show down-pointing triangle
        $(column_header).find(".sort_symbol").html("&#9660");
        // Add new class to indicate descending sorting order
        $(column_header).addClass("desc");
    } else {
        // Reverse sorting order
        order = order.reverse();
        result_array = result_array.reverse();
        // Show up-pointing triangle
        $(column_header).find(".sort_symbol").html("&#9650");
        // Add new class to indicate ascending sorting order
        $(column_header).addClass("asc");
    }

    // Remove old table rows
    $("#" + div_id + " table tbody").empty();

    // Add table rows in new order to the table body
    build_evaluation_table_body(result_array, div_id);

    // Re-add selected class if row or cell was previously selected
    if (selected_approach_indices.length > 0) {
        selected_cells = [];
        // Re-add selected class to previously selected row
        for (var i=0;i<selected_approach_indices.length; i++) {
            if (selected_approach_indices[i] === null) break;
            var new_selected_approach_index = order.indexOf(selected_approach_indices[i]) + 1;  // +1 because nth-child is 1-based
            $("#" + div_id + " table tbody tr:nth-child(" + new_selected_approach_index + ")").addClass("selected");

            if (selected_cells_classes.length > i) {
                // Re-add selected class to previously selected cell
                selected_cells.push($("#" + div_id + " table tbody tr:nth-child(" + new_selected_approach_index + ") td" + selected_cells_classes[i]));
                $(selected_cells[i]).addClass("selected");
                if (div_id == "type_evaluation") {
                    var cls = $(selected_cells[i]).attr('class').split(/\s+/)[0];
                    $(selected_cells[i]).closest('tr').find('.' + cls).each(function(index) {
                        $(this).addClass("selected");
                    });
                }
            }
        }
    }
}

function compare_approach_names(approach_1, approach_2) {
    approach_name_1 = approach_1[0];
    approach_name_2 = approach_2[0];
    return link_linker_key(approach_name_1) - link_linker_key(approach_name_2) ||
        coref_linker_key(approach_name_1) - coref_linker_key(approach_name_2) ||
        linker_key(approach_name_1) - linker_key(approach_name_2) ||
        approach_name_1 > approach_name_2;
}

function link_linker_key(approach_name) {
    if (approach_name.includes("ltl.entity")) return 1;
    else if (approach_name.includes("ltl")) return 2;
    else if (approach_name.startsWith("wexea")) return 3;
    else return 10;
}

function linker_key(approach_name) {
    if (approach_name.startsWith("neural_el")) return 1;
    else if (approach_name.startsWith("explosion")) return 2;
    else if (approach_name.startsWith("baseline")) return 90;
    else if (approach_name.startsWith("none")) return 100;
    else return 10;
}

function coref_linker_key(approach_name) {
    var start_idx = approach_name.split(".", 2).join(".").length + 1;
    var end_idx = approach_name.split(".", 3).join(".").length;
    var coref_linker = approach_name.substring(start_idx, end_idx);
    if (coref_linker == "entity") return 1;
    else if (coref_linker == "none") return 100;
    else return 10;
}

function read_evaluation_cases(path, approach_name, selected_approaches) {
    /*
    Retrieve evaluation cases from the given file and show the linked currently selected article.
    */
    console.log("read_evaluation_cases() called for", path, approach_name, selected_approaches);

    // Clear evaluation case cache
    if (Object.keys(evaluation_cases).length >= MAX_CACHED_FILES) {
        var position = 0;
        var key = null;
        while (position < Object.keys(evaluation_cases).length) {
            key = Object.keys(evaluation_cases)[position];
            if (key != approach_name && !selected_approach_names.includes(key)) {
                break;
            }
            position++;
        }
        delete evaluation_cases[key];
        console.log("Deleting " + key + " from evaluation_cases cache.");
    }

    // Read new evaluation cases
    if (approach_name in evaluation_cases && evaluation_cases[approach_name].length > 0) {
        show_article(selected_approaches)
    } else {
        $.get(path, function(data) {
            evaluation_cases[approach_name] = [];
            lines = data.split("\n");
            for (line of lines) {
                if (line.length > 0) {
                    cases = JSON.parse(line);
                    evaluation_cases[approach_name].push(cases);
                }
            }
            show_article(selected_approaches);
        }).fail(function() {
            $("#evaluation").html("ERROR: no file with cases found.");
            console.log("FAIL NOW CALL SHOW ARTICLE");
            show_article(selected_approaches);
        });
    }
}

function read_articles_data(path, approach_name) {
    /*
    Read the predictions of the selected approach for all articles.
    They are needed later to visualise the predictions outside the evaluation span of an article.
    
    Arguments:
    - path: the .jsonl file of the selected approach
    */
    // Clear articles data cache
    if (Object.keys(articles_data).length >= MAX_CACHED_FILES) {
        var position = 0;
        var key = null;
        while (position < Object.keys(articles_data).length) {
            key = Object.keys(articles_data)[position];
            if (key != approach_name && !selected_approach_names.includes(key)) {
                break;
            }
            position++;
        }
        delete articles_data[key];
        console.log("Deleting " + key + " from articles_data cache.");
    }

    if (!(approach_name in articles_data) || articles_data[approach_name].length == 0) {
        articles_data[approach_name] = [];
        promise = $.get(path, function(data) {
            lines = data.split("\n");
            for (line of lines) {
                if (line.length > 0) {
                    articles_data[approach_name].push(JSON.parse(line));
                }
            }
        });
        return promise;
    } else {
        return Promise.resolve(1);
    }
}

function read_evaluation(approach_name, selected_approaches) {
    /*
    Read the predictions and evaluation cases for the selected approach for all articles.
    */
    console.log("read_evaluation() called for ", approach_name, "and ", selected_approaches);
    var cases_path = result_files[approach_name] + ".cases";
    var articles_path = result_files[approach_name] + ".jsonl";

    reading_promise = read_articles_data(articles_path, approach_name);
    reading_promise.then(function() {  // wait until the predictions from the .jsonl file are read, because run_evaluation updates the prediction textfield
        read_evaluation_cases(cases_path, approach_name, selected_approaches);
    });
}

function on_row_click(el) {
    /*
    This method is called when a table body row was clicked.
    This marks the row as selected and reads the evaluation cases.
    */
    var approach_name = $(el).find('td:first').text();

    // De-select all current rows if a row in a different table was selected before
    var former_parent_table = $("#evaluation_tables table tbody tr.selected").closest("table").parent().attr("id");
    var new_parent_table = $(el).closest("table").parent().attr("id");
    if (former_parent_table && former_parent_table != new_parent_table) {
        deselect_all_table_rows(former_parent_table);
        selected_approach_names = [];
    }

    // De-select previously selected rows
    if (!is_compare_checked() || selected_approach_names.length >= MAX_SELECTED_APPROACHES) {
        deselect_all_table_rows(new_parent_table);
        selected_approach_names = [];
    }

    if (!selected_approach_names.includes(approach_name)) {
        selected_approach_names.push(approach_name);
        // Select clicked row
        $(el).addClass("selected");
        selected_rows.push(el);
    }
    var selected_approaches = [...selected_approach_names];

    read_evaluation(approach_name, selected_approaches);
}

function on_cell_click(el) {
    /*
    Highlight error category / type cells on click and un-highlight previously clicked cell.
    Add or remove error categories and types to/from current selection.
    */
    // De-select current selection if necessary
    var div_id = $(el).closest('table').parent().attr('id');
    if (div_id == "evaluation") { reset_selected_types(); } else { reset_selected_error_categories(); }

    // Determine whether an already selected cell has been clicked
    var curr_row = $(el).closest("tr").index();
    var prev_selected_rows = $.map(selected_rows, function(sel_row) { return $(sel_row).index(); });
    var already_selected_row_clicked = $.inArray(curr_row, prev_selected_rows);

    if (selected_cells.length > 0) {
        var same_table = $(selected_cells[0]).closest('table').parent().attr('id') == div_id;
        if (!is_compare_checked() || selected_rows.length >= MAX_SELECTED_APPROACHES || !same_table) {
            // Remove selected classes for all currently selected cells
            for (var i=0; i<selected_cells.length; i++) {
                remove_selected_classes(selected_cells[i]);
            }
            selected_cells = [];
            if (div_id == "evaluation") { reset_selected_error_categories(); } else { reset_selected_types(); }
        } else {
            // Remove selected class for cells in the same row
            var last_rows = $.map(selected_cells, function(sel_cell) { return $(sel_cell).closest('tr').index(); });
            var index = $.inArray(curr_row, last_rows);
            if (index >= 0) {
                remove_selected_classes(selected_cells[index]);
                selected_cells.splice(index, 1);
                if (div_id == "evaluation") { selected_error_categories[index] = null; } else { selected_types[index] = null; }
            }
        }
    }

    // Make new selection
    if ($(el).attr('class')) {  // System column has no class attribute
        if (div_id == "evaluation") {
            var classes = $(el).attr('class').split(/\s+/);
            if (classes.length > 1 && classes[1] in error_category_mapping) {
                $(el).addClass("selected");
                selected_cells.push(el);
            } else if (classes.length > 0 && classes[0] in mention_type_headers) {
                $(el).closest('tr').find('.' + classes[0]).each(function() {
                    $(this).addClass("selected");
                });
                selected_cells.push(el);
            }
        } else {
            // Mark all cells in the corresponding row with the corresponding class
            var cls = $(el).attr('class').split(/\s+/)[0];
            $(el).closest('tr').find('.' + cls).each(function() {
                $(this).addClass("selected");
            });
            selected_cells.push(el);
        }
    }

    // Note that selected_rows is updated in on_row_click(), i.e. after on_cell_click() is called so no -1 necessary.
    var approach_index = (already_selected_row_clicked >= 0) ? 0 : selected_rows.length % MAX_SELECTED_APPROACHES;
    if (div_id == "evaluation") {
        selected_error_categories[approach_index] = get_error_category_or_type(el);
    } else {
        selected_types[approach_index] = get_error_category_or_type(el);
    }
}

function deselect_all_table_rows(div_id) {
    /*
    Deselect all rows in all evaluation tables
    */
    $("#" + div_id + " tbody tr").each(function() {
        $(this).removeClass("selected");
    });
    selected_rows = [];
}

function remove_selected_classes(el) {
    var cls = $(el).attr('class').split(/\s+/)[0];
    $(el).closest('tr').find('.' + cls).each(function(index) {
        $(this).removeClass("selected");
    });
}

function get_error_category_or_type(element) {
    /*
    For a given cell return the error category or type it belongs to, or null otherwise.
    */
    data_attribute = $(element).data("category");
    if (data_attribute) {
        var match = data_attribute.match(/Q[0-9]+:.*/);
        if (data_attribute in error_category_mapping) {
            return error_category_mapping[data_attribute];
        } else if (data_attribute in mention_type_headers) {
            return mention_type_headers[data_attribute];
        } else if (match || data_attribute == "OTHER") {
            return data_attribute.replace(/(Q[0-9]+):.*/g, "$1");
        }
    }
    return null;
}

function show_table_column(table_id, index) {
    /*
    Show the column with the given index in the table with the given id.
    */
    $("#" + table_id + " th:nth-child(" + (index + 1) + ")").show();
    $("#" + table_id + " td:nth-child(" + (index + 1) + ")").show();
}

function hide_table_column(table_id, index) {
    /*
    Show the column with the given index in the table with the given id.
    */
    $("#" + table_id + " th:nth-child(" + (index + 1) + ")").hide();
    $("#" + table_id + " td:nth-child(" + (index + 1) + ")").hide();
}

function toggle_compare() {
    /*
    Toggle compare checkbox.
    */
    if (!is_compare_checked()) {
        if (selected_approach_names.length > 1) {
            selected_approach_names = [selected_approach_names[1]];
        }

        // De-select evaluation table row
        if (selected_rows.length > 1) {
            deselected_row = selected_rows.shift();  // Remove first element in array
            $(deselected_row).removeClass("selected");
            deselected_cell = selected_cells.shift();
            remove_selected_classes(deselected_cell);
        }

        hide_table_column("prediction_overview", 1);

        show_article(selected_approach_names);
    }
}

function is_compare_checked() {
    return $("#checkbox_compare").is(":checked");
}

function on_article_select() {
    show_article(selected_approach_names);
}

function produce_latex(div_id) {
    /*
    Produce LaTeX source code for the overview table and copy it to the clipboard.
    */
    var latex = [];

    // Comment that clarifies the origin of this code.
    latex.push("% Copied from " + window.location.href + " on " + new Date().toLocaleString());
    latex.push("");

    // Generate the header row of the table and count columns
    var num_cols = 0;
    var row_count = 0;
    var header_string = "";
    $('#' + div_id + ' table thead tr').each(function(){
        $(this).find('th').each(function() {
            if (!$(this).is(":hidden")) {
                // Do not add hidden table columns
                if (row_count > 0) num_cols += 1;
                var title = $(this).html();
                title = title.replace(/_/g, " ");  // Underscore not within $ yields error
                // Filter out sorting order and tooltip html
                var match = title.match(/(<div [^<>]*>)?([^<>]*)<(span|div)/);
                if (match) title = match[2];
                // Get column span of the current header
                var colspan = parseInt($(this).attr("colspan"), 10);
                if (colspan) {
                    // First column header is skipped here, so starting with "&" works
                    header_string += "& \\multicolumn{" + colspan + "}{c}{\\textbf{" + title + "}} ";
                } else if (title && title != "System" && title != copy_latex_text) {
                    header_string += "& \\textbf{" + title + "} ";
                }
            }
        })
        header_string += "\\\\\n";
        row_count += 1;
    })

    // Begin table.
    latex.push(
        ["\\begin{table*}",
         "\\centering",
         "\\begin{tabular}{l" + "c".repeat(num_cols) + "}",
         "\\hline"].join("\n"));

    latex.push(header_string);
    latex.push("\\hline");

    // Generate the rows of the table body
    $("#" + div_id + " table tbody tr").each(function() {
        var col_idx = 0;
        var row_string = "";
        $(this).find("td").each(function() {
            if (!$(this).is(":hidden")) {
                // Do not add hidden table columns
                var text = $(this).html();
                // Filter out tooltip texts and html
                var match = text.match(/<div [^<>]*>([^<>]*)<(span|div)/);
                if (match) text = match[1];
                text = text.replace(/%/g, "\\%").replace(/_/g, " ");
                if (col_idx == 0) {
                    row_string += text + " ";
                } else {
                    row_string += "& $" + text + "$ ";
                }
                col_idx += 1;
            }
        });
        if (row_string) {
            row_string += "\\\\";
            latex.push(row_string);
        }
    });

    // End table
    latex.push(
        ["\\hline",
         "\\end{tabular}",
         "\\caption{\\label{results}Fancy caption.}",
         "\\end{table*}",
         ""].join("\n"));

    // Join lines, copy to textarea and from there to the clipboard.
    var latex_text = latex.join("\n");
    console.log(latex_text);
    $('#' + div_id + " .latex").show();
    $('#' + div_id + " .latex textarea").val(latex_text);
    $('#' + div_id + " .latex textarea").show();  // Text is not selected or copied if it is hidden
    $('#' + div_id + " .latex textarea").select();
    document.execCommand("copy");
    $('#' + div_id + " .latex textarea").hide();

    // Show the notification for the specified number of seconds
    var show_duration_seconds = 5;
    setTimeout(function() { $('#' + div_id + " .latex").hide(); }, show_duration_seconds * 1000);
}

