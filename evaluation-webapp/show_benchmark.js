// Colors for the tooltips.
GREEN = ["rgb(125,206,160)", "rgba(125,206,160, 0.3)"]; // "#7dcea0";
RED = ["rgb(241,148,138)", "rgba(241,148,138, 0.3)"];  // "#f1948a";
BLUE = ["rgb(187,143,206)", "rgba(187,143,206, 0.3)"]; // "#bb8fce";
GREY = ["rgb(211,211,211)", "rgba(211,211,211, 0.3)"]; // "lightgrey";
YELLOW = ["rgb(241,200,138)", "rgba(241,200,138, 0.3)"];

RESULTS_EXTENSION = ".results";

JOKER_LABELS = ["QUANTITY", "DATETIME"];

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
    selected_error_categories = [];
    selected_types = [];

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

    // Show tooltips on both sides when the corresponding span on the other side is hovered
    $("#prediction_overview td").on("mouseenter", ".tooltip", function() {
        var hovered_tooltiptext = $(this).find(".tooltiptext");
        var hovered_tooltiptext_id = $(hovered_tooltiptext).attr("id");
        $(hovered_tooltiptext).css("visibility", "visible");
        // Get corresponding span(s) on the prediction side and show them too
        if (hovered_tooltiptext_id in span_pairs) {
            var tooltip_num = 0;
            for (corresponding_span_id of span_pairs[hovered_tooltiptext_id]) {
                $("#" + corresponding_span_id).css("visibility", "visible");
                if (tooltip_num % 2 == 1) {
                    // Try to avoid overlapping tooltips if a mention on one side corresponds
                    // to multiple mentions on the other side.
                    $("#" + corresponding_span_id).css("top", "100%");
                    $("#" + corresponding_span_id).css("bottom", "auto");
                }
                tooltip_num++;
            }
        }
    });

    $("#prediction_overview td").on("mouseleave", ".tooltip", function() {
        var hovered_tooltiptext = $(this).find(".tooltiptext");
        var hovered_tooltiptext_id = $(hovered_tooltiptext).attr("id");
        $(hovered_tooltiptext).css("visibility", "hidden");
        if (hovered_tooltiptext_id in span_pairs) {
            for (corresponding_span_id of span_pairs[hovered_tooltiptext_id]) {
                $("#" + corresponding_span_id).css("visibility", "hidden");
            }
        }
    });
});

function get_selected_category(element) {
    data_attribute = $(element).data("category");
    if (data_attribute) {
        var match = data_attribute.match(/Q[0-9]+:.*/);
        if (data_attribute in error_category_mapping) {
            return error_category_mapping[data_attribute];
        } else if (match || data_attribute == "OTHER") {
            return data_attribute.replace(/(Q[0-9]+):.*/g, "$1");
        }
    }
    return null;
}

function set_benchmark_select_options() {
    /* Set the options for the benchmark selector element to the names of the benchmarks in the given directory. */
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
    /* Set the options for the article selector element to the names of the articles from the list 'articles'. */
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
    /* Link the currently selected article in the element #article_link. */
    $("#article_link").html("<a href=\"" + article.url + "\" target=\"_blank\">Wikipedia article</a>");
    $("#article_link").show();
}

function show_ground_truth_entities(approach_name, textfield, selected_error_categories, selected_type) {
    /*
    Generate tooltips for the ground truth entities of the selected article
    and show them in the left textfield.
    */
    if (show_all_articles_flag) {
        var ground_truth_texts = [];
        for (var i=0; i < articles.length; i++) {
            var annotations = get_ground_truth_annotations(i, approach_name);
            ground_truth_texts.push(annotate_text(articles[i].text, annotations, articles[i].links, articles[i].evaluation_span, true, i, selected_error_categories, selected_type, approach_name));
        }
        ground_truth_text = "";
        for (var i=0; i < ground_truth_texts.length; i++) {
            ground_truth_text += "<br><br>" + "********** " + articles[i].title + " **********<br>";
            ground_truth_text += ground_truth_texts[i];
        }
    } else {
        var annotations = get_ground_truth_annotations(selected_article_index, approach_name);
        var ground_truth_text = annotate_text(article.text, annotations, article.links, [0, article.text.length], true, 0, selected_error_categories, selected_type, approach_name);
    }
    textfield.html(ground_truth_text);
}

function is_correct_optional_case(eval_case) {
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

function get_ground_truth_annotations(article_index, approach_name) {
    /*
    Generate annotations for the ground truth entities of the selected article.
    */
    var annotations = [];

    var child_label_to_parent = {};
    var label_id_to_label = {};
    for (eval_case of evaluation_cases[approach_name][article_index]) {
        // Build the parent mapping
        if ("true_entity" in eval_case && eval_case.true_entity.children) {
            label_id_to_label[eval_case.true_entity.id] = eval_case.true_entity;
            for (child_id of eval_case.true_entity.children) {
                child_label_to_parent[child_id] = eval_case.true_entity.id;
            }
        }
    }

    for (eval_case of evaluation_cases[approach_name][article_index]) {
        if (eval_case.mention_type && eval_case.mention_type.toLowerCase() in show_mentions) {
            if (!show_mentions[eval_case.mention_type.toLowerCase()]) {
                continue;
            }
        }
        // Ensure backwards compatibility by allowing eval_case.factor to be null.
        // If a factor is given it needs to be > 0 in order for the gt case to be displayed.
        if ("true_entity" in eval_case && (eval_case.factor == null || eval_case.factor > 0)) {
            if (eval_case.true_entity.entity_id.startsWith("Unknown")) {
                // GT entity is NIL
                color = YELLOW;
            } else if (is_correct_optional_case(eval_case)) {
                color = GREY;
            } else if ("predicted_entity" in eval_case) {
                if (eval_case.predicted_entity.entity_id == eval_case.true_entity.entity_id) {
                    // predicted the true entity
                    color = GREEN;
                } else {
                    // predicted the wrong entity
                    color = RED;
                }
            } else {
                // wrong span
                color = BLUE;
            }
            // Use the type of the parent entity because this is the type that counts in the evaluation.
            var curr_label_id = eval_case.true_entity.id;
            while (curr_label_id in child_label_to_parent) {
                curr_label_id = child_label_to_parent[curr_label_id];
            }
            var entity_type = label_id_to_label[curr_label_id].type;
            // Get text of parent span
            var parent_text = null;
            if (curr_label_id != eval_case.true_entity.id) {
                parent_span = label_id_to_label[curr_label_id].span;
                parent_text = articles[article_index].text.substring(parent_span[0], parent_span[1]);
            }
            var annotation = {
                "span": eval_case.span,
                "color": color,
                "entity_name": eval_case.true_entity.name,
                "entity_id": eval_case.true_entity.entity_id,
                "entity_type": entity_type,
                "error_labels": eval_case.error_labels,
                "parent_text": parent_text
            };
            annotations.push(annotation);
        }
    }
    return annotations
}

function show_linked_entities(approach_name, textfield, selected_error_categories, selected_type) {
    /*
    Generate tooltips for the predicted entities of the selected approach and article
    and show them in the right textfield.
    */
    if (show_all_articles_flag) {
        var predicted_texts = [];
        for (var i=0; i < articles.length; i++) {
            var annotations = get_predicted_annotations(i, approach_name);
            predicted_texts.push(annotate_text(articles[i].text, annotations, articles[i].links, articles[i].evaluation_span, false, i, selected_error_categories, selected_type, approach_name));
        }
        predicted_text = "";
        for (var i=0; i < predicted_texts.length; i++) {
            predicted_text += "<br><br>" + "********** " + articles[i].title + " **********<br>";
            predicted_text += predicted_texts[i];
        }
    } else {
        var annotations = get_predicted_annotations(selected_article_index, approach_name);
        var predicted_text = annotate_text(article.text, annotations, article.links, [0, article.text.length], false, 0, selected_error_categories, selected_type, approach_name);
    }
    textfield.html(predicted_text);
}

function get_predicted_annotations(article_index, approach_name) {
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
    // get the predicted entities inside the evaluation span from the cases list
    for (eval_case of article_cases) {
        if ("predicted_entity" in eval_case) {  // no false negatives
            mentions.push(eval_case);
        }
    }
    // get the mentions after the evaluation span
    for (prediction of article_data.entity_mentions) {
        if (prediction.span[0] >= evaluation_end) {
            mentions.push(prediction);
        }
    }

    // list with tooltip information for each mention
    var annotations = {};
    var spans = [];
    for (mention of mentions) {
        if (mention.mention_type && mention.mention_type.toLowerCase() in show_mentions) {
            if (!show_mentions[mention.mention_type.toLowerCase()]) {
                continue;
            }
        }
        if (mention.factor == 0) {
            // Do not display overlapping mentions
            continue;
        }
        if ("predicted_entity" in mention) {
            // Avoid overlapping spans: Keep the larger one.
            // Assume that predictions are sorted by span start (but not by span end)
            var last_index = spans.length - 1;
            if (spans.length > 0 && spans[last_index][1] > mention.span[0]) {
                // Overlap detected.
                var previous_span_length = spans[last_index][1] - spans[last_index][0];
                var current_span_length = mention.span[1] - mention.span[0];
                if (previous_span_length >= current_span_length) {
                    // Previous span is longer than current span so discard current prediction
                    continue
                } else {
                    delete annotations[spans[last_index]];
                    spans.splice(-1);
                }
            }

            spans.push(mention.span)

            // mention is inside the evaluation span and therefore an evaluated case
            if (is_correct_optional_case(mention)) {
                color = GREY;
            } else if ("true_entity" in mention && !mention.true_entity.entity_id.startsWith("Unknown")) {
                 if (mention.true_entity.entity_id == mention.predicted_entity.entity_id) {
                    // predicted the true entity
                    color = GREEN;
                } else {
                    // predicted the wrong entity
                    color = RED;
                }
            }
            else {
                // wrong span
                color = BLUE;
            }
            entity_id = mention.predicted_entity.entity_id;
            entity_name = mention.predicted_entity.name;
            entity_type = mention.predicted_entity.type;
            predicted_by = mention.predicted_by;
            if (color == GREEN) {
                // Use the type of the parent entity because this is the type that counts in the evaluation.
                var curr_label_id = mention.true_entity.id;
                while (curr_label_id in child_label_to_parent) {
                    curr_label_id = child_label_to_parent[curr_label_id];
                }
                entity_type = label_id_to_label[curr_label_id].type;
            }
        } else {  // mention is outside the evaluation span
            color = GREY;
            entity_id = mention.id;
            entity_name = null;
            entity_type = null;
            predicted_by = mention.linked_by;
        }
        var annotation = {
            "span": mention.span,
            "color": color,
            "entity_id": entity_id,
            "entity_name": entity_name,
            "entity_type": entity_type,
            "predicted_by": predicted_by,
            "error_labels": mention.error_labels
        };
        annotations[mention.span] = annotation;
    }
    annotations = Object.values(annotations);
    return annotations
}

function copy(object) {
    /* get a copy of the given object */
    return JSON.parse(JSON.stringify(object));
}

function deep_copy_array(array) {
    /* get a copy of an array and its elements */
    copied_array = [];
    for (element of array) {
        copied_array.push(copy(element));
    }
    return copied_array;
}

function annotate_text(text, annotations, links, evaluation_span, evaluation, article_num, selected_error_categories, selected_type, approach_name) {
    /*
    Generate tooltips for the given annotations and hyperlinks for the given links.
    Tooltips and hyperlinks can overlap.

    Arguments:
    - text: The original text without tooltips or hyperlinks.
    - annotations: A sorted (by span) list of objects containing the following tooltip information:
        annotation.span: start and end character offset of the entity mention
        annotation.color:
        annotation.entity_id: wikidata ID of the mentioned entity
        annotation.entity_name: name of the mentioned entity (or null)
        annotation.predicted_by: identifier of the entity linker (optional)
    - links: A sorted (by span) list of tuples (span, target_article).

    First the overlapping annotations and links get combined to annotations_with_links.
    Second, the annotations with links are added to the text.
    */
    // STEP 1: Combine overlapping annotations and links.
    // Consumes the first element from the link list or annotation list,
    // or a part from both if they overlap.
    links = deep_copy_array(links);
    annotations = deep_copy_array(annotations);
    annotations_with_links = [];
    while (annotations.length > 0 || links.length > 0) {
        if (annotations.length == 0) {
            link = links.shift();
            link_span = link[0];
            link_annotation = {
                "link": link[1]
            };
            annotations_with_links.push([link_span, link_annotation]);
        } else if (links.length == 0) {
            annotation = annotations.shift();
            annotations_with_links.push([annotation.span, annotation]);
        } else {
            annotation = annotations[0];
            link = links[0];
            link_span = link[0];
            if (link_span[0] < annotation.span[0]) {
                // add link
                link_annotation = {
                    "link": link[1]
                };
                link_end = Math.min(link_span[1], annotation.span[0]);
                annotations_with_links.push([[link_span[0], link_end], link_annotation]);
                if (link_end == link_span[1]) {
                    links.shift();
                } else {
                    links[0][0][0] = link_end;
                }
            } else if (annotation.span[0] < link_span[0]) {
                // add annotation
                annotation_end = Math.min(annotation.span[1], link_span[0]);
                annotations_with_links.push([[annotation.span[0], annotation_end], annotation]);
                if (annotation_end == annotation.span[1]) {
                    annotations.shift();
                } else {
                    annotation.span[0] = annotation_end;
                }
            } else {
                // add both
                annotation = copy(annotation);
                annotation["link"] = link[1];
                annotation_end = Math.min(annotation.span[1], link_span[1]);
                annotations_with_links.push([[annotation.span[0], annotation_end], annotation]);
                if (annotation_end == link_span[1]) {
                    links.shift();
                } else {
                    links[0][0][0] = annotation_end;
                }
                if (annotation_end == annotation.span[1]) {
                    annotations.shift();
                } else {
                    annotations[0].span[0] = annotation_end;
                }
            }
        }
    }
    // Text should only be the text within the given evaluation span (Careful: This is the entire article if a
    // single article is supposed to be shown and the article evaluation span if all articles are supposed to be
    // shown)
    text = text.substring(0, evaluation_span[1]);

    // STEP 2: Add the combined annotations and links to the text.
    // This is done in reverse order so that the text before is always unchanged. This allows to use the spans as given.
    id_counter = 0;
    if (evaluation && annotation_spans[approach_name][0].length - 1 < article_num) annotation_spans[approach_name][0].push([]);
    else if (prediction && annotation_spans[approach_name][1].length - 1 < article_num) annotation_spans[approach_name][1].push([]);
    for (annotation of annotations_with_links.reverse()) {
        // annotation is a tuple with (span, annotation_info)
        span = annotation[0];
        if (span[1] > evaluation_span[1]) {
            continue;
        } else if (span[0] < evaluation_span[0]) {
            break;
        }
        annotation = annotation[1];
        before = text.substring(0, span[0]);
        snippet = text.substring(span[0], span[1]);
        after = text.substring(span[1]);
        if (annotation.hasOwnProperty("link")) {
            // add link
            snippet = "<a href=\"https://en.wikipedia.org/wiki/" + annotation.link + "\" target=\"_blank\">" + snippet + "</a>";
        }
        if (annotation.hasOwnProperty("entity_id")) {
            // add tooltip
            wikidata_url = "https://www.wikidata.org/wiki/" + annotation.entity_id;
            entity_link = "<a href=\"" + wikidata_url + "\" target=\"_blank\">" + annotation.entity_id + "</a>";
            if (annotation.entity_name != null) {
                tooltip_text = annotation.entity_name + " (" + entity_link + ")";
            } else {
                tooltip_text = entity_link;
            }
            if (annotation.hasOwnProperty("predicted_by")) {
                tooltip_text += "<br>predicted_by=" + annotation.predicted_by;
            }
            if (annotation.hasOwnProperty("parent_text") && annotation.parent_text != null) {
                tooltip_text += "<br>parent=\"" + annotation.parent_text + "\"";
            }
            if (annotation.hasOwnProperty("error_labels") && annotation.error_labels.length > 0) {
                tooltip_text += "<br>category=";
                for (var e_i = 0; e_i < annotation.error_labels.length; e_i += 1) {
                    if (e_i > 0) {
                        tooltip_text += ",";
                    }
                    tooltip_text += annotation.error_labels[e_i];
                }
            }
            // Only show selected error category
            var color = annotation.color[0];
            if (selected_error_categories && annotation.error_labels) {
                // Use transparent version of the color, if an error category is selected
                // And the current annotation does not have a corresponding category label
                var has_category = false;
                for (selected_category of selected_error_categories) {
                    if (annotation.error_labels.includes(selected_category)) {
                        has_category = true;
                        break;
                    }
                }
                if (!has_category) color = annotation.color[1];
            } else if (selected_type && annotation.entity_type &&
                       !annotation.entity_type.split("|").includes(selected_type)) {
                color = annotation.color[1];
            }
            replacement = "<div class=\"tooltip\" style=\"background-color:" + color + "\">";
            replacement += snippet;
            tooltiptext_id = "tooltiptext_";
            tooltiptext_id += evaluation ? "evaluation" : "prediction";
            tooltiptext_id += "_" + approach_name.replaceAll(".", "_") + "_" + article_num + "_" + id_counter;
            replacement += "<span id=\"" + tooltiptext_id + "\" class=\"tooltiptext\">" + tooltip_text + "</span>";
            replacement += "</div>";
            if (evaluation) annotation_spans[approach_name][0][article_num].push([annotation.span, tooltiptext_id]);
            else annotation_spans[approach_name][1][article_num].push([annotation.span, tooltiptext_id]);
            id_counter++;
        } else {
            // no tooltip (just a link)
            replacement = snippet;
        }
        text = before + replacement + after;
    }
    if (evaluation) annotation_spans[approach_name][0][article_num].reverse();  // Annotations are added in reverse order
    else annotation_spans[approach_name][1][article_num].reverse();
    text = text.substring(evaluation_span[0], text.length);
    text = text.replaceAll("\n", "<br>");
    return text;
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

    // Reset / initialize span pair variables
    annotation_spans = {};
    annotation_spans[selected_approaches[0]] = [[], []];
    span_pairs = {};

    // Show columns
    if (is_show_groundtruth_checked()) {
        // Show first groundtruth column
        show_ground_truth_entities(selected_approaches[0], $(columns[column_idx]), selected_error_categories[0], selected_types[0]);
        $(column_headers[column_idx]).text(selected_approaches[0] + " (groundtruth)")
        show_table_column("prediction_overview", column_idx);
        column_idx++;
    }
    // Show first prediction column
    show_linked_entities(selected_approaches[0], $(columns[column_idx]), selected_error_categories[0], selected_types[0]);
    $(column_headers[column_idx]).text(selected_approaches[0] + " (prediction)")
    show_table_column("prediction_overview", column_idx);
    column_idx++;
    if(is_compare_checked() && selected_approaches.length > 1) {
        // Show second prediction column
        annotation_spans[selected_approaches[1]] = [[], []];
        show_linked_entities(selected_approaches[1], $(columns[column_idx]), selected_error_categories[1], selected_types[1]);
        $(column_headers[column_idx]).text(selected_approaches[1] + " (prediction)")
        show_table_column("prediction_overview", column_idx);
        column_idx++;
        if (is_show_groundtruth_checked()) {
            // Show second groundtruth column
            show_ground_truth_entities(selected_approaches[1], $(columns[column_idx]), selected_error_categories[1], selected_types[1]);
            $(column_headers[column_idx]).text(selected_approaches[1] + " (groundtruth)")
            show_table_column("prediction_overview", column_idx);
            column_idx++;
        }
    }

    // Hide unused columns
    for (var i=column_idx; i<columns.length; i++) {
        hide_table_column("prediction_overview", i);
    }

    // Set column width
    var width_percentage = 100 / column_idx;
    $("#prediction_overview th, #prediction_overview td").css("width", width_percentage + "%");

    // Create annotation span pairs to be able to show the tooltips on both sides when hovering over one
    for (var j=0; j<selected_approaches.length; j++) {
        var approach_name = selected_approaches[j]
        for (var i = 0; i < annotation_spans[approach_name][0].length; i++) {
            prediction_span_index = 0;
            evaluation_span_index = 0;
            overlap_set = [new Set(), new Set()];
            while (evaluation_span_index < annotation_spans[approach_name][0][i].length && prediction_span_index < annotation_spans[approach_name][1][i].length) {
                var [evaluation_span, evaluation_span_id] = annotation_spans[approach_name][0][i][evaluation_span_index];
                var [prediction_span, prediction_span_id] = annotation_spans[approach_name][1][i][prediction_span_index];
                if (evaluation_span[1] <= prediction_span[0]) {
                    // evaluation span comes before prediction span, no overlap
                    evaluation_span_index++;
                    add_overlap_spans_to_mapping(overlap_set);
                    overlap_set = [new Set(), new Set()];
                } else if (evaluation_span[0] >= prediction_span[1]) {
                    // evaluation span comes after prediction span, no overlap
                    prediction_span_index++;
                    add_overlap_spans_to_mapping(overlap_set);
                    overlap_set = [new Set(), new Set()];
                } else {
                    // Overlap
                    overlap_set[0].add(evaluation_span_id);
                    overlap_set[1].add(prediction_span_id);
                    // A single span on one side can overlap with multiple on the other side
                    // Therefore only increase index of span that ends first
                    if (evaluation_span[1] > prediction_span[1]) prediction_span_index++;
                    else evaluation_span_index++;
                }
            }
            add_overlap_spans_to_mapping(overlap_set);
        }
    }
}

function add_overlap_spans_to_mapping(overlap_set) {
    // Add previous overlapping spans to mappings
    for (evaluation_overlap_span_id of overlap_set[0]) {
        if (overlap_set[1].size > 0) span_pairs[evaluation_overlap_span_id] = overlap_set[1];
    }
    for (prediction_overlap_span_id of overlap_set[1]) {
        if (overlap_set[0].size > 0) span_pairs[prediction_overlap_span_id] = overlap_set[0];
    }
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
                    var data_string = "data-category='" + subclass_name + "'";
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
    console.log("on_row_click()");
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
    }

    // Select clicked row
    $(el).addClass("selected");
    selected_rows.push(el);

    if (!is_compare_checked() || selected_approach_names.length == MAX_SELECTED_APPROACHES) {
        selected_approach_names = [];
    }
    if (!selected_approach_names.includes(approach_name)) {
        selected_approach_names.push(approach_name);
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
    console.log("on_cell_click() for selected cells: ", selected_cells);
    var div_id = $(el).closest('table').parent().attr('id');
    if (div_id == "evaluation") { selected_types = []; } else { selected_error_categories = []; }

    if (selected_cells.length > 0) {
        var same_table = $(selected_cells[0]).closest('table').parent().attr('id') == div_id;
        if (!is_compare_checked() || selected_cells.length >= MAX_SELECTED_APPROACHES || !same_table) {
            // Remove selected classes for all currently selected cells
            console.log("Removing all previously selected cells:", selected_cells);
            for (var i=0; i<selected_cells.length; i++) {
                remove_selected_classes(selected_cells[i]);
            }
            selected_cells = [];
            if (div_id == "evaluation") { selected_error_categories = []; } else { selected_types = []; }
        } else {
            // Remove selected class for cells in the same row
            var curr_row = $(el).closest("tr").index();
            var last_rows = $.map(selected_cells, function(sel_cell) { return $(sel_cell).closest('tr').index(); });
            var index = $.inArray(curr_row, last_rows);
            if (index >= 0) {
                remove_selected_classes(selected_cells[index]);
                selected_cells.splice(index, 1);
                if (div_id == "evaluation") { selected_error_categories.splice(index, 1); } else { selected_types.splice(index, 1); }
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
    if (div_id == "evaluation") { selected_error_categories.push(get_selected_category(el)); } else { selected_types.push(get_selected_category(el)); }

    console.log("on_cell_click(): Finished with selected types", selected_types, "and selected errors", selected_error_categories);
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

        if (is_show_groundtruth_checked()) {
            hide_table_column("prediction_overview", 2);
            hide_table_column("prediction_overview", 3);
        } else {
            hide_table_column("prediction_overview", 1);
        }
        show_article(selected_approach_names);
    }
}

function toggle_show_groundtruth() {
    show_article(selected_approach_names);
}

function is_show_groundtruth_checked() {
    return $("#checkbox_groundtruth").is(":checked");
}

function is_compare_checked() {
    return $("#checkbox_compare").is(":checked");
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

