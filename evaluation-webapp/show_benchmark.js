ANNOTATION_CLASS_TP = "tp";
ANNOTATION_CLASS_FP = "fp";
ANNOTATION_CLASS_FN = "fn";
ANNOTATION_CLASS_UNKNOWN = "unknown";
ANNOTATION_CLASS_OPTIONAL = "optional";
ANNOTATION_CLASS_UNEVALUATED = "unevaluated";

RESULTS_EXTENSION = ".results";
EVALUATION_RESULT_PATH = "evaluation-results";

MAX_SELECTED_APPROACHES = 2;
MAX_CACHED_FILES = 15;

MISSING_LABEL_TEXT = "[MISSING LABEL]";
NO_LABEL_ENTITY_IDS = ["QUANTITY", "DATETIME", "Unknown"];

ignore_headers = ["true_positives", "false_positives", "false_negatives", "ground_truth"];
percentage_headers = ["precision", "recall", "f1"];
copy_latex_text = "Copy LaTeX code for table";

header_descriptions = {
    "undetected": {
        "all": "The span of a GT mention was not linked (= NER FN) / Named GT mentions",
        "lowercase": "The span of a lowercase GT mention was not linked / Named lowercase GT mentions",
        "specificity": "FN and a part of the GT mention was linked to an arbitrary entity / Named GT mentions containing whitespace(s)",
        "overlap": "FN and the GT span overlaps with a predicted span / Named uppercase GT mentions",
        "other": "Other detection error / Named uppercase GT mentions"
    },
    "disambiguation_errors": {
        "all": "Detected, but wrong entity linked / Detected",
        "demonym": "FN from a list of demonyms (German, Germans, ...) / All demonym GT mentions",
        "partial_name": "FN and the GT mention is part of the entity name / Named GT mentions where the mention is a part of the entity name",
        "metonymy": "Predicted and most popular candidate are locations, but ground truth is not / Most popular candidate is a location, but ground truth is not",
        "rare": "Most popular candidate is wrongly predicted / Detected mentions where the most popular candidate is not the correct entity",
        "other": "Other disambiguation error",
        "wrong_candidates": "A GT mention was recognized but the GT entity is not among the candidates / Named detected",
        "multi_candidates": "A GT mention was recognized and the GT entity is one of the candidates, but the wrong candidate was selected / Named detected where the GT entity is one of multiple candidates"
    },
    "false_detection": {
        "all": "Predicted mention that does not match a groundtruth mention span",
        "abstraction": "Lowercase named FP that does not overlap with a GT mention",
        "unknown_named_entity": "Uppercase mention wrongly linked, where the ground truth is either Unknown or has no label at all",
        "other": "Other false detection",
        "span_wrong": "Predicted mention whose span does not match, but overlaps with a GT mention with a matching entity / Predicted mentions"
    },
    "other_errors": {
        "hyperlink": "FN where the mention is a hyperlink / GT mentions that are hyperlinks"
    },
    "coreference_errors": {
        "false_detection": "FP mentions in {It, it, This, this, That, that, Its, its}",
        "reference_wrongly_disambiguated": "FN + FP, the reference was wrongly disambiguated / Coreference mentions where correct GT mention was referenced",
        "wrong_mention_referenced": "FN + FP, wrong mention was referenced / Linked GT coreference mentions",
        "undetected": "FN, mention was not linked / GT coreference mentions"
    },
    "all": "All results. TP: correct span, correct link; FP: incorrect span or correct span but wrong link; FN: GT span was not recognized or wrong link",
    "NER": "Named mention span errors. TP: correct span; FP: predicted span does not match any GT span; FN: GT span does not match any predicted span",
    "coref": "All coreference results: nominal (the &lt;type&gt) and pronominal (pronouns)",
    "entity": "All entity results (i.e. results excluding coreference)",
    "entity_named": "All results for named entities",
    "entity_other": "All results for non-named entities",
    "nominal": "All nominal coreference ('the &lt;type&gt;') results",
    "pronominal": "All pronominal coreference (pronoun) results"
};

error_category_mapping = {
    "undetected": {
        "all": ["UNDETECTED"],
        "lowercase": ["UNDETECTED_LOWERCASE"],
        "specificity": ["UNDETECTED_SPECIFICITY"],
        "overlap": ["UNDETECTED_OVERLAP"],
        "other": ["UNDETECTED_OTHER"]
    },
    "disambiguation_errors": {
        "all": ["DISAMBIGUATION_WRONG"],
        "demonym": ["DISAMBIGUATION_DEMONYM_CORRECT", "DISAMBIGUATION_DEMONYM_WRONG"],
        "partial_name": ["DISAMBIGUATION_PARTIAL_NAME_CORRECT", "DISAMBIGUATION_PARTIAL_NAME_WRONG"],
        "metonymy": ["DISAMBIGUATION_METONYMY_CORRECT", "DISAMBIGUATION_METONYMY_WRONG"],
        "rare": ["DISAMBIGUATION_RARE_CORRECT", "DISAMBIGUATION_RARE_WRONG"],
        "other": ["DISAMBIGUATION_WRONG_OTHER"],
        "wrong_candidates": ["DISAMBIGUATION_WRONG_CANDIDATES"],
        "multi_candidates": ["DISAMBIGUATION_MULTI_CANDIDATES_CORRECT", "DISAMBIGUATION_MULTI_CANDIDATES_WRONG"]
    },
    "false_detection": {
        "all": ["FALSE_DETECTION"],
        "abstraction": ["FALSE_DETECTION_ABSTRACTION"],
        "unknown_named_entity": ["FALSE_DETECTION_UNKNOWN_NAMED_ENTITY"],
        "other": ["FALSE_DETECTION_OTHER"],
        "span_wrong": ["FALSE_DETECTION_SPAN_WRONG"]
    },
    "other_errors": {
        "hyperlink": ["OTHER_HYPERLINK_WRONG"]
    },
    "coreference_errors": {
        "false_detection": ["COREFERENCE_FALSE_DETECTION"],
        "reference_wrongly_disambiguated": ["COREFERENCE_REFERENCE_WRONGLY_DISAMBIGUATED"],
        "wrong_mention_referenced": ["COREFERENCE_WRONG_MENTION_REFERENCED"],
        "undetected": ["COREFERENCE_UNDETECTED"]
    }
};

mention_type_headers = {"entity": ["entity_named", "entity_other"],
                        "coref": ["nominal", "pronominal"],
                        "entity_named": ["entity_named"],
                        "entity_other": ["entity_other"],
                        "nominal": ["nominal"],
                        "pronominal": ["pronominal"]};

benchmark_names = ["wiki-ex", "conll", "conll-dev", "conll-test", "ace", "msnbc", "newscrawl", "msnbc-original", "ace-original"];


$("document").ready(function() {
    // Elements from the HTML document for later usage.
    benchmark_select = document.getElementById("benchmark");
    article_select = document.getElementById("article_select");

    show_all_articles_flag = false;

    evaluation_cases = {};
    articles_data = {};

    last_show_article_request_timestamp = 0;

    selected_approach_names = [];
    selected_rows = [];
    selected_cells = [];
    reset_selected_cell_categories();

    sorting_variables = {"column_index": null, "desc": true};

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

    // Highlight error category cells on hover
    $("#evaluation").on("mouseenter", "td", function() {
        if (is_error_cell(this)) {
            $(this).addClass("hovered");
        }
    });
    $("#evaluation").on("mouseleave", "td", function() {
        $(this).removeClass("hovered");
    });

    // Highlight all cells in a row belonging to the same mention_type or type on hover
    $("#evaluation").on("mouseenter", "td", function() {
        if ($(this).attr('class')) {
            var cls = $(this).attr('class').split(/\s+/)[0];
            if (cls in mention_type_headers || is_type_string(cls)) {
                // Mark all cells in the corresponding row with the corresponding class
                $(this).closest('tr').find('.' + cls).each(function(index) {
                    $(this).addClass("hovered");
                });
            }
        }
    });
    $("#evaluation").on("mouseleave", "td", function() {
        if ($(this).attr('class')) {
            var cls = $(this).attr('class').split(/\s+/)[0];
            if (cls in mention_type_headers || is_type_string(cls)) {
                $(this).closest('tr').find('.' + cls).each(function(index) {
                    $(this).removeClass("hovered");
                });
            }
        }
    });

    // Reposition annotation tooltips on the right edge of the window on mouseenter
    $("#prediction_overview").on("mouseenter", ".annotation", function() {
        reposition_annotation_tooltip(this);
    });

    // Position table tooltips
    $("#evaluation").on("mouseenter", "td,th", function() {
        $(this).find(".tooltip").each(function() {
            position_table_tooltip(this);
        });
    });

    // Tooltips need to be repositioned on window resize
    // otherwise some might overlap with the left window edge.
    $(window).on('resize', function(){
        $("#prediction_overview").find(".tooltiptext").each(function() {
            if ($(this).css("right") == "0px") $(this).css({"right": "auto", "left": "0px"});
        });
    });

    // Set the result filter string and show-deprecated checkbox according to the URL parameters
    var filter_string = get_url_parameter("filter");
    if (filter_string) $("input#result-filter").val(filter_string);
    var show_deprecated_param = get_url_parameter("show_deprecated");
    var show_deprecated = (["true", "1"].includes(show_deprecated_param)) ? true : false;
    if (show_deprecated) $("#checkbox_deprecated").prop('checked', show_deprecated);
    if (filter_string || !show_deprecated) {
        filter_table_rows();
    }

    // Synchronize the top and bottom scrollbar of the evaluation table
    $("#evaluation").scroll(function(){
        $("#top_scrollbar_wrapper").scrollLeft($("#evaluation").scrollLeft());
    });
    $("#top_scrollbar_wrapper").scroll(function(){
        $("#evaluation").scrollLeft($("#top_scrollbar_wrapper").scrollLeft());
    });
});

function position_table_tooltip(anchor_el) {
    var anchor_el_rect = anchor_el.getBoundingClientRect();
    $(anchor_el).find(".tooltiptext").each(function() {
        var tooltip_rect = this.getBoundingClientRect();
        var font_size = $(this).css("font-size").replace("px", "");
        var top = anchor_el_rect.top - tooltip_rect.height - (font_size / 2);
        $(this).css({"left": anchor_el_rect.left + "px", "top": top + "px"});
    });
}

function reposition_annotation_tooltip(annotation_el) {
    /*
    Re-position all tooltips of an annotation such that they don't go outside the window.
    */
    var annotation_rect = annotation_el.getBoundingClientRect();
    // Check whether the annotation contains a line break by checking whether its height is bigger than the line height
    var line_height = parseInt($(annotation_el).css('line-height').replace('px',''));
    var line_break = (annotation_rect.height > line_height + 5);
    $(annotation_el).find(".tooltiptext").each(function() {
        var tooltip_rect = this.getBoundingClientRect();
        // Correct the tooltip position if it overlaps with the right edge of the window (approximated by table width)
        // If the annotation contains a line break, check the right
        if ((annotation_rect.left + tooltip_rect.width) > $("#prediction_overview").width() || line_break)  {
            // Align right tooltip edge with right edge of the annotation.
            // Left needs to be set to auto since it is otherwise still 0.
            $(this).css({"right": "0px", "left": "auto"});
        }
    });
}

function get_url_parameter(parameter_name) {
    /*
    Retrieve URL parameter.
    See https://stackoverflow.com/a/21903119/7097579.
    */
    var page_url = window.location.search.substring(1);
    var url_variables = page_url.split('&');

    for (var i = 0; i < url_variables.length; i++) {
        var curr_parameter = url_variables[i].split('=');
        if (curr_parameter[0] === parameter_name) {
            return curr_parameter[1] === undefined ? true : decodeURIComponent(curr_parameter[1]);
        }
    }
    return false;
};

function is_error_cell(el) {
    if ($(el).attr('class')) {  // System column has no class attribute
        var classes = $(el).attr('class').split(/\s+/);
        if (classes.length > 1) {
            // The second class of a cell is its header and subheader (as class name) connected by "-"
            var keys = classes[1].split("-");
            if (keys[0] in error_category_mapping) {
                if (keys[1] in error_category_mapping[keys[0]]) {
                    return true;
                }
            }
        }
    }
    return false;
}

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

        // Set benchmark
        var benchmark_string = get_url_parameter("benchmark");
        var benchmark_by_url = $('#benchmark option').filter(function () { return $(this).html() == benchmark_string; });
        if (benchmark_string && benchmark_by_url.length > 0) {
            // Set the benchmark according to URL parameter if one with a valid benchmark name exists
            $(benchmark_by_url).prop('selected',true);
        } else {
            // Set default value to "wiki-ex".
            $('#benchmark option:contains("wiki-ex")').prop('selected',true);
        }
        // If URL parameter is set, select approach name according to URL parameter
        var approach_name_url_param = get_url_parameter("approach");
        show_benchmark_results(approach_name_url_param);
    });
}

function reset_selected_cell_categories() {
    /*
    Initialize or reset the selected error categories.
    The array contains one entry for each approach that can be compared.
    */
    selected_cell_categories = new Array(MAX_SELECTED_APPROACHES).fill(null);
}

function show_benchmark_results(default_approach_name) {
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
    evaluation_cases = {};
    selected_approach_names = [];
    selected_rows = [];
    selected_cells = [];
    reset_selected_cell_categories();

    // Build an overview table over all .results-files from the evaluation-results folder.
    build_overview_table(benchmark_name, default_approach_name);

    // Read the article and ground truth information from the benchmark.
    parse_benchmark(benchmark_file);
}

function filter_table_rows() {
    var filter_keywords = $.trim($("input#result-filter").val()).split(/\s+/);
    $("#evaluation_tables tbody tr").each(function() {
        var name = $(this).children(":first-child").text();
        // Filter row according to filter keywords
        var show_row = filter_keywords.every(keyword => name.search(keyword) != -1);

        // Filter row according to show-deprecated checkbox
        if (!$("#checkbox_deprecated").is(":checked")) {
            show_row = show_row && !name.includes("deprecated");
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
    $("#article_select").empty();

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

function show_annotated_text(approach_name, textfield, selected_cell_category) {
    /*
    Generate annotations and tooltips for predicted and groundtruth mentions of the selected approach and article
    and show them in the textfield.
    */
    if (show_all_articles_flag) {
        var annotated_texts = [];
        for (var i=0; i < articles.length; i++) {
            var annotations = get_annotations(i, approach_name);
            annotated_texts.push(annotate_text(articles[i].text, annotations, articles[i].links, articles[i].evaluation_span, selected_cell_category));
        }
        annotated_text = "";
        for (var i=0; i < annotated_texts.length; i++) {
            if (i != 0) annotated_text += "<hr/>";
            if (articles[i].title) annotated_text += "<b>" + articles[i].title + "</b><br>";
            annotated_text += annotated_texts[i];
        }
    } else {
        var annotations = get_annotations(selected_article_index, approach_name);
        var annotated_text = annotate_text(article.text, annotations, article.links, [0, article.text.length], selected_cell_category);
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
        if (mention.factor == 0) {
            // Do not display overlapping mentions
            continue;
        }

        var gt_annotation = {};
        var pred_annotation = {};

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
                gt_annotation.class = ANNOTATION_CLASS_UNKNOWN;
                if ("predicted_entity" in mention) {
                    pred_annotation.class = ANNOTATION_CLASS_FP;
                }
            } else if (is_correct_optional_case(mention)) {
                gt_annotation.class = ANNOTATION_CLASS_OPTIONAL;
                if ("predicted_entity" in mention) {
                    // Prediction is a correct optional, i.e. unevaluated.
                    pred_annotation.class = ANNOTATION_CLASS_UNEVALUATED;
                }
            } else if ("predicted_entity" in mention) {
                 if ("true_entity" in mention && !mention.true_entity.entity_id.startsWith("Unknown")) {
                     if (mention.true_entity.entity_id == mention.predicted_entity.entity_id) {
                        // predicted the true entity
                        gt_annotation.class = ANNOTATION_CLASS_TP;
                        pred_annotation.class = ANNOTATION_CLASS_TP;
                    } else {
                        // predicted the wrong entity
                        pred_annotation.class = ANNOTATION_CLASS_FP;
                        if (is_optional_case(mention)) {
                            gt_annotation.class = ANNOTATION_CLASS_OPTIONAL;
                        } else {
                            gt_annotation.class = ANNOTATION_CLASS_FN;
                        }
                    }
                } else {
                    // wrong span
                    pred_annotation.class = ANNOTATION_CLASS_FP;
                }
            } else {
                gt_annotation.class = ANNOTATION_CLASS_FN;
            }

            if ("true_entity" in mention) {
                // Use the type of the parent entity because this is the type that counts in the evaluation.
                var curr_label_id = mention.true_entity.id;
                while (curr_label_id in child_label_to_parent) {
                    curr_label_id = child_label_to_parent[curr_label_id];
                }
                gt_annotation.gt_entity_type = label_id_to_label[curr_label_id].type;
                // Get text of parent span
                if (curr_label_id != mention.true_entity.id) {
                    var parent_span = label_id_to_label[curr_label_id].span;
                    gt_annotation.parent_text = articles[article_index].text.substring(parent_span[0], parent_span[1]);
                }
                gt_annotation.gt_entity_id = mention.true_entity.entity_id;
                gt_annotation.gt_entity_name = mention.true_entity.name;
            }

            if ("predicted_entity" in mention) {
                pred_annotation.pred_entity_id = mention.predicted_entity.entity_id;
                pred_annotation.pred_entity_name = mention.predicted_entity.name;
                pred_annotation.pred_entity_type = mention.predicted_entity.type;
                pred_annotation.predicted_by = mention.predicted_by;
                if (pred_annotation.class == ANNOTATION_CLASS_TP) {
                    // Use the type of the parent entity because this is the type that counts in the evaluation.
                    pred_annotation.pred_entity_type = gt_annotation.gt_entity_type;
                }
            }
        } else {
            // mention is outside the evaluation span
            pred_annotation.class = ANNOTATION_CLASS_UNEVALUATED;
            pred_annotation.pred_entity_id = mention.id;
            pred_annotation.pred_entity_name = null;
            pred_annotation.pred_entity_type = null;
            pred_annotation.predicted_by = mention.linked_by;
        }

        var mention_type = (mention.mention_type) ? mention.mention_type.toLowerCase() : null;
        var annotation = {
            "span": mention.span,
            "mention_type": mention_type,
            "error_labels": []
        };
        // If the case has a GT and a prediction, don't add error cases to GT if it's an unknown or optional case
        if (!$.isEmptyObject(gt_annotation) && !$.isEmptyObject(pred_annotation)) {
            if (gt_annotation.class == ANNOTATION_CLASS_OPTIONAL || gt_annotation.class == ANNOTATION_CLASS_UNKNOWN) {
                pred_annotation.error_labels = mention.error_labels;
            } else {
                gt_annotation.error_labels = mention.error_labels;
                pred_annotation.error_labels = mention.error_labels;

            }
        } else {
            annotation.error_labels = mention.error_labels;
        }
        // Merge basic annotations and case specific annotations into a single annotation object
        // If the annotation contains both a groundtruth and a prediction, make the prediction the inner annotation of
        // the groundtruth annotation in order not to create overlapping annotations.
        if (!$.isEmptyObject(gt_annotation)) {
            var gt_annotation = {...annotation, ...gt_annotation};
            annotations[mention.span] = gt_annotation;
            if (!$.isEmptyObject(pred_annotation)) {
                var pred_annotation = {...annotation, ...pred_annotation};
                gt_annotation.inner_annotation = pred_annotation;
            }
        } else if (!$.isEmptyObject(pred_annotation)) {
            var pred_annotation = {...annotation, ...pred_annotation};
            annotations[mention.span] = pred_annotation;
        }
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

function annotate_text(text, annotations, links, evaluation_span, selected_cell_category) {
    /*
    Generate tooltips for the given annotations and hyperlinks for the given links.
    Tooltips and hyperlinks can overlap.

    Arguments:
    - text: The original text without tooltips or hyperlinks.
    - annotations: A sorted (by span) list of objects containing tooltip information
    - links: A sorted (by span) list of tuples (span, target_article)
    - evaluation_span: The span of the article that can be evaluated
    - selected_cell_categories: categories of the selected cell for the corresponding approach

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
    var combined_annotations = combine_overlapping_annotations(only_groundtruth_annotations, non_groundtruth_annotations);
    // Links must be the last list that is added such that they can only be the inner most annotations, because <div>
    // tags are not allowed within <a> tags, but the other way round is valid.
    combined_annotations = combine_overlapping_annotations(combined_annotations, new_links);

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
        replacement = generate_annotation_html(snippet, annotation, selected_cell_category, null);
        text = before + replacement + after;
    }
    text = text.substring(evaluation_span[0], text.length);
    text = text.replaceAll("\n", "<br>");
    return text;
}

function generate_annotation_html(snippet, annotation, selected_cell_category, parent_text) {
    /*
    Generate html snippet for a given annotation. A hyperlink is also regarded as an annotation
    and can be identified by the property "link". Inner annotations, e.g. hyperlinks contained in
    a mention annotation, nested mention annotations are contained given by the property "inner_annotation".
    */
    var inner_annotation = snippet;

    if ("inner_annotation" in annotation) {
        inner_annotation = generate_annotation_html(snippet, annotation.inner_annotation, selected_cell_category, annotation.parent_text);
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
    if (!(annotation.class == ANNOTATION_CLASS_TP && annotation.gt_entity_id)) {
        // Don't generate tooltips for the groundtruth part of a TP. A single tooltip is enough in this case
        if (annotation.class == ANNOTATION_CLASS_TP) {
            wikidata_url = "https://www.wikidata.org/wiki/" + annotation.pred_entity_id;
            entity_link = "<a href=\"" + wikidata_url + "\" target=\"_blank\">" + annotation.pred_entity_id + "</a>";
            if (annotation.pred_entity_name != null) {
                var entity_name = (["Unknown", "null"].includes(annotation.pred_entity_name)) ? MISSING_LABEL_TEXT : annotation.pred_entity_name;
                tooltip_header_text += entity_name + " (" + entity_link + ")";
            } else {
                tooltip_header_text += entity_link;
            }
            if (parent_text) tooltip_body_text += "parent text: \"" + parent_text + "\"<br>";
        } else {
            if (annotation.pred_entity_id) {
                var entity_name = (["Unknown", "null"].includes(annotation.pred_entity_name)) ? MISSING_LABEL_TEXT : annotation.pred_entity_name;
                var wikidata_url = "https://www.wikidata.org/wiki/" + annotation.pred_entity_id;
                var entity_link = "<a href=\"" + wikidata_url + "\" target=\"_blank\">" + annotation.pred_entity_id + "</a>";
                tooltip_header_text += "Prediction: " + entity_name + " (" + entity_link + ")";
            }
            if (annotation.gt_entity_id ) {
                if (tooltip_header_text) { tooltip_header_text += "<br>"; }
                if (NO_LABEL_ENTITY_IDS.includes(annotation.gt_entity_id) || annotation.gt_entity_id.startsWith("Unknown")) {
                    // For Datetimes, Quantities and Unknown GT entities don't display "Label (QID)"
                    // instead display "[DATETIME]"/"[QUANTITY]" or "[UNKNOWN #xy]" or "[UNKNOWN]"
                    var entity_name = annotation.gt_entity_id;
                    if (annotation.gt_entity_id == "Unknown") {
                        entity_name = "UNKNOWN";
                    } else if (annotation.gt_entity_id.startsWith("Unknown")) {
                        entity_name = "UNKNOWN #" + annotation.gt_entity_id.replace("Unknown", "");
                    }
                    tooltip_header_text += "Groundtruth: [" + entity_name + "]";
                } else {
                    var entity_name = (annotation.gt_entity_name == "Unknown") ? MISSING_LABEL_TEXT : annotation.gt_entity_name;
                    var wikidata_url = "https://www.wikidata.org/wiki/" + annotation.gt_entity_id;
                    var entity_link = "<a href=\"" + wikidata_url + "\" target=\"_blank\">" + annotation.gt_entity_id + "</a>";
                    tooltip_header_text += "Groundtruth: " + entity_name + " (" + entity_link + ")";
                }
                tooltip_classes += " below";
            }
        }
        // Add case type boxes and annotation case type class to tooltip
        if ([ANNOTATION_CLASS_TP, ANNOTATION_CLASS_FN, ANNOTATION_CLASS_FP].includes(annotation.class)) {
            tooltip_case_type_html += "<div class=\"case_type_box " + annotation.class + "\">" + annotation.class.toUpperCase() + "</div>";
            tooltip_classes += " " + annotation.class;
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
    }

    // Use transparent version of the color, if an error category or type is selected
    // and the current annotation does not have a corresponding error category or type label
    if (selected_cell_category) {
        var lowlight_mention = true;
        for (selected_category of selected_cell_category) {
            if (is_type_string(selected_category)) {
                var pred_type_selected = annotation.pred_entity_type && annotation.pred_entity_type.toLowerCase().split("|").includes(selected_category);
                var gt_type_selected = annotation.gt_entity_type && annotation.gt_entity_type.toLowerCase().split("|").includes(selected_category);
                if (pred_type_selected || gt_type_selected) {
                    lowlight_mention = false;
                    break;
                }
            } else {
                if (annotation.error_labels.includes(selected_category) || annotation.mention_type == selected_category) {
                    lowlight_mention = false;
                    break;
                }
            }
        }
        var lowlight = (lowlight_mention) ? "lowlight" : "";
    }

    var annotation_kind = (annotation.gt_entity_id) ? "gt" : "pred";
    var replacement = "<span class=\"annotation " + annotation_kind + " " + annotation.class + " " + lowlight + "\">";
    replacement += inner_annotation;
    if (tooltip_header_text) {
        replacement += "<div class=\"" + tooltip_classes + "\">";
        replacement += "<div class=\"header\">";
        replacement += "<div class=\"left\">" + tooltip_header_text + "</div>";
        replacement += "<div class=\"right\">" + tooltip_case_type_html + "</div>";
        replacement += "</div>";
        replacement += "<div class=\"body\">" + tooltip_body_text + "</div>";
        replacement += "<div class=\"footer\">" + tooltip_footer_html + "</div>";
        replacement += "</div>";
    }
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

async function show_article(selected_approaches, timestamp) {
    /*
    Generate the ground truth textfield and predicted text field for the selected article
    (or all articles if this option is selected) and approach.
    */
    console.log("show_article() called for selected approaches", selected_approaches, "and evaluation cases for", Object.keys(evaluation_cases));

    if (timestamp < last_show_article_request_timestamp) {
        console.log("Dropping function call since newer call exists.");
        return
    }

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
        } else if (timestamp < last_show_article_request_timestamp) {
            console.log("ERROR: Stop waiting for result.");
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
    show_annotated_text(selected_approaches[0], $(columns[column_idx]), selected_cell_categories[0]);
    $(column_headers[column_idx]).text(selected_approaches[0]);
    show_table_column("prediction_overview", column_idx);
    column_idx++;
    if(is_compare_checked() && selected_approaches.length > 1) {
        // Show second prediction column
        show_annotated_text(selected_approaches[1], $(columns[column_idx]), selected_cell_categories[1]);
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

    // Hide the loading GIF
    if (timestamp >= last_show_article_request_timestamp) $("#loading").removeClass("show");
}

function build_overview_table(benchmark_name, default_approach_name) {
    /*
    Build the overview table from the .results files found in the subdirectories of the given path.
    */
    var path = EVALUATION_RESULT_PATH;
    var folders = [];
    result_files = {};
    result_array = [];
    var urls = [];
    $.get(path, function(data) {
        // Get all folders from the evaluation results directory
        $(data).find("a").each(function() {
            var name = $(this).attr("href");
            var name = name.substring(0, name.length - 1);
            folders.push(name);
        });
    }).done(function() {
        // Retrieve file path of .results files for the selected benchmark in each folder
        $.when.apply($, folders.map(function(folder) {
            return $.get(path + "/" + folder, function(folder_data) {
                $(folder_data).find("a").each(function() {
                    var file_name = $(this).attr("href");
                    // This assumes the benchmark is specified in the last dot separated column before the
                    // file extension if it is not our wiki-ex benchmark.
                    var benchmark = file_name.split(".").slice(-2)[0];
                    var benchmark_match = ((benchmark_name == "wiki-ex" && !benchmark_names.includes(benchmark)) || benchmark == benchmark_name);
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
                    // Remove the benchmark extension from the approach name
                    if (approach_name.endsWith("." + benchmark_name)) approach_name = approach_name.substring(0, approach_name.lastIndexOf("."))
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

                    if (!$('#evaluation_tables .checkboxes').html()) {
                        // Add checkboxes if they have not yet been added
                        add_checkboxes(results);
                    }
                });
                // Add table body
                build_evaluation_table_body(result_array);

                // Sort the table according to previously chosen sorting
                var sort_column_index = sorting_variables["column_index"];
                var sort_descending = sorting_variables["desc"];
                if (sort_column_index != null) {
                    var sort_column_header = $('#evaluation table thead tr:nth-child(2) th:nth-child(' + sort_column_index + ')');
                    // Hack to get the right sort order which is determined by
                    // whether the column header already has the class "desc"
                    if (!sort_descending) sort_column_header.addClass("desc");
                    sort_table(sort_column_header);
                }

                if (default_approach_name) {
                    var row = $('#evaluation table tbody tr').filter(function(){ return $(this).children(":first-child").text() === default_approach_name;});
                    if (row.length > 0) on_row_click(row[0]);
                }
            });
        });
    });
}

function build_evaluation_table_body(result_list) {
    /*
    Build the table body.
    Show / Hide rows and columns according to checkbox state and filter-result input field.
    */
    // Add table rows in new sorting order
    result_list.forEach(function(result_tuple) {
        var approach_name = result_tuple[0];
        var results = result_tuple[1];
        if (results) {
            var row = get_table_row(approach_name, results);
            $('#evaluation table tbody').append(row);
        }
    });

    // Show / Hide columns according to checkbox state
    $("input[class^='checkbox_']").each(function() {
        show_hide_columns(this);
    })

    // Show / Hide rows according to filter-result input field
    filter_table_rows();
}

function add_checkboxes(json_obj) {
    /*
    Add checkboxes for showing / hiding columns.
    */
    $.each(json_obj, function(key) {
        if (key == "by_type" || key == "errors") {
            $.each(json_obj[key], function(subkey) {
                var class_name = get_class_name(subkey);
                var title = get_title_from_key(subkey);
                var checkbox_html = "<input type=\"checkbox\" class=\"checkbox_" + class_name + "\" onchange=\"show_hide_columns(this)\">";
                checkbox_html += "<label>" + title + "</label>";
                var checkbox_div_id = (key == "errors") ? "error_checkboxes" : "type_checkboxes";
                $("#" + checkbox_div_id + ".checkboxes").append(checkbox_html);
            });
        } else {
            var class_name = get_class_name(key);
            var title = get_title_from_key(key);
            var checked = (class_name == "all") ? "checked" : ""
            var checkbox_html = "<input type=\"checkbox\" class=\"checkbox_" + class_name + "\" onchange=\"show_hide_columns(this)\" " + checked + ">";
            checkbox_html += "<label>" + title + "</label>";
            $("#general_checkboxes.checkboxes").append(checkbox_html);
        }
    });
}

function show_hide_columns(element) {
    /*
    This function should be called when the state of a checkbox is changed.
    This can't be simply added in on document ready, because checkboxes are added dynamically.
    */
    var col_class = $(element).attr("class");
    col_class = col_class.substring(col_class.indexOf("_") + 1, col_class.length);
    var column = $("#evaluation ." + col_class);
    if($(element).is(":checked")) {
        column.show();
    } else {
        column.hide();
    }

    // The table width has changed therefore change the width of the top scrollbar div accordingly
    var width = $("#evaluation table")[0].getBoundingClientRect().width + 20;  // + width of the side scrollbar
    $("#top_scrollbar").css({"width": width + "px"});

    // Adjust the top position of the sticky second table header row according to the
    // height of the first table header row
    var top = $("#evaluation table thead tr:nth-child(1)")[0].getBoundingClientRect().height;
    $("#evaluation table thead tr:nth-child(2)").css({"top": top});
}

function get_table_header(json_obj) {
    /*
    Get html for the table header.
    */
    var first_row = "<tr><th onclick='produce_latex()' class='produce_latex'>" + copy_latex_text + "</th>";
    var second_row = "<tr><th onclick='sort_table(this)'>System<span class='sort_symbol'>&#9660</span></th>";
    $.each(json_obj, function(key) {
        if (key == "by_type" || key == "errors") {
            $.each(json_obj[key], function(subkey) {
                var row_additions = get_table_header_by_json_key(json_obj[key], subkey);
                first_row += row_additions[0];
                second_row += row_additions[1];
            });
        } else {
            var row_additions = get_table_header_by_json_key(json_obj, key);
            first_row += row_additions[0];
            second_row += row_additions[1];
        }
    });
    first_row += "</tr>";
    second_row += "</tr>";
    return first_row + second_row;
}

function get_table_header_by_json_key(json_obj, key) {
    var first_row_addition = "";
    var second_row_addition = "";
    var colspan = 0;
    var class_name = get_class_name(key);
    $.each(json_obj[key], function(subkey) {
        if (!(ignore_headers.includes(subkey))) {
            var subclass_name = get_class_name(subkey);
            second_row_addition += "<th class='" + class_name + "' onclick='sort_table(this)' data-array-key='" + key + "' data-array-subkey='" + subkey + "'><div class='tooltip'>" + get_title_from_key(subkey) + "<span class='sort_symbol'>&#9660</span>";
            var tooltip_text = get_header_tooltip_text(key, subkey);
            if (tooltip_text) {
                second_row_addition += "<span class='tooltiptext'>" + tooltip_text + "</span>";
            }
            second_row_addition += "</div></th>";
            colspan += 1;
        }
    });
    first_row_addition += "<th colspan=\"" + colspan + "\" class='" + class_name + "'><div class='tooltip'>" + get_title_from_key(key);
    var tooltip_text = get_header_tooltip_text(key, null);
    if (tooltip_text) {
        first_row_addition += "<span class='tooltiptext'>" + tooltip_text + "</span>";
    }
    first_row_addition += "</div></th>";
    return [first_row_addition, second_row_addition];
}

function get_table_row(approach_name, json_obj) {
    /*
    Get html for the table row with the given approach name and result values.
    */
    var row = "<tr onclick='on_row_click(this)'>";
    var onclick_str = " onclick='on_cell_click(this)'";
    row += "<td " + onclick_str + ">" + approach_name + "</td>";
    $.each(json_obj, function(key) {
        if (key == "by_type" || key == "errors") {
            $.each(json_obj[key], function(subkey) {
                row += get_table_row_by_json_key(json_obj[key], subkey, onclick_str);
            });
        } else {
            row += get_table_row_by_json_key(json_obj, key, onclick_str);
        }
    });
    row += "</tr>";
    return row;
}

function get_table_row_by_json_key(json_obj, key, onclick_str) {
    var row_addition = "";
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
                var percentage = get_error_percentage(value);
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
            var data_string = "data-category='" + class_name + "," + subclass_name + "'";
            row_addition += "<td class='" + class_name + " " + class_name + "-" + subclass_name + "' " + data_string + onclick_str + ">" + value + "</td>";
        }
    });
    return row_addition;
}

function get_error_percentage(value) {
    if (value["total"] == 0) {
        return 0.00;
    }
    return (value["errors"] / value["total"] * 100).toFixed(2);
}

function get_tooltip_text(json_obj) {
    tooltip_text = "TP: " + Math.round(json_obj["true_positives"] * 100) / 100 + "<br>";
    tooltip_text += "FP: " + Math.round(json_obj["false_positives"] * 100) / 100 + "<br>";
    tooltip_text += "FN: " + Math.round(json_obj["false_negatives"] * 100) / 100 + "<br>";
    tooltip_text += "GT: " + Math.round(json_obj["ground_truth"] * 100) / 100;
    return tooltip_text;
}

function get_header_tooltip_text(key, subkey) {
    if (key in header_descriptions) {
        if (subkey) {
            return header_descriptions[key][subkey];
        }
        if (typeof header_descriptions[key] == "string") {
            return header_descriptions[key];
        }
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

function sort_table(column_header) {
    /*
    Sort table rows with respect to the selected column.
    This sorts the result_array, removes old table rows and adds them in the new ordering.
    */
    // Get list of values in the selected column
    // + 1 because nth-child indices are 1-based
    var col_index = $(column_header).parent().children().index($(column_header)) + 1;

    // Store the column index to apply the same sorting when selecting a different benchmark
    // Can't just store and use the column header itself since it's the header of the old table
    sorting_variables["column_index"] = col_index;

    var key = $(column_header).data("array-key");
    var subkey = $(column_header).data("array-subkey");
    var col_values = [];
    var index = 0;
    var selected_approach_indices = [null, null];
    result_array.forEach(function(result_tuple) {
        var approach_name = result_tuple[0];
        if (selected_approach_names.includes(approach_name) && selected_rows.length > 0) {
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
        if (is_type_string(key)) {
            results = results["by_type"];
        } else if (key in error_category_mapping && subkey in error_category_mapping[key]) {
            results = results["errors"];
        }
        var value = results[key][subkey];
        if (value && Object.keys(value).length > 0) {
            // An error category contains two keys and the percentage is displayed, so sort by percentage
            value = get_error_percentage(value);
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
    sorting_variables["desc"] = descending;

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
    $("#evaluation table th").each(function() {
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
    $("#evaluation table tbody").empty();

    // Add table rows in new order to the table body
    build_evaluation_table_body(result_array);

    // Re-add selected class if row or cell was previously selected
    if (selected_approach_indices.length > 0) {
        selected_cells = [];
        selected_rows = [];
        // Re-add selected class to previously selected row
        for (var i=0;i<selected_approach_indices.length; i++) {
            if (selected_approach_indices[i] === null) break;
            var new_selected_approach_index = order.indexOf(selected_approach_indices[i]) + 1;  // +1 because nth-child is 1-based
            selected_rows.push($("#evaluation table tbody tr:nth-child(" + new_selected_approach_index + ")"))
            selected_rows[i].addClass("selected");

            if (selected_cells_classes.length > i) {
                // Re-add selected class to previously selected cell
                selected_cells.push($("#evaluation table tbody tr:nth-child(" + new_selected_approach_index + ") td" + selected_cells_classes[i]));
                $(selected_cells[i]).addClass("selected");
                if ($(selected_cells[i]).attr('class')) {
                    var selected_cell_class = $(selected_cells[i]).attr('class').split(/\s+/)[0];
                    if (selected_cell_class in mention_type_headers || is_type_string(selected_cell_class)) {
                        var cls = $(selected_cells[i]).attr('class').split(/\s+/)[0];
                        $(selected_cells[i]).closest('tr').find('.' + cls).each(function(index) {
                            $(this).addClass("selected");
                        });
                    }
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

function read_evaluation_cases(path, approach_name, selected_approaches, timestamp) {
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
        show_article(selected_approaches, timestamp)
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
            show_article(selected_approaches, timestamp);
        }).fail(function() {
            $("#evaluation").html("ERROR: no file with cases found.");
            console.log("FAIL NOW CALL SHOW ARTICLE");
            show_article(selected_approaches, timestamp);
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
        var promise = $.get(path, function(data) {
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

function read_evaluation(approach_name, selected_approaches, timestamp) {
    /*
    Read the predictions and evaluation cases for the selected approach for all articles.
    */
    console.log("read_evaluation() called for ", approach_name, "and ", selected_approaches);
    var cases_path = result_files[approach_name] + ".cases";
    var articles_path = result_files[approach_name] + ".jsonl";

    reading_promise = read_articles_data(articles_path, approach_name);
    reading_promise.then(function() {  // wait until the predictions from the .jsonl file are read, because run_evaluation updates the prediction textfield
        read_evaluation_cases(cases_path, approach_name, selected_approaches, timestamp);
    });
}

function on_row_click(el) {
    /*
    This method is called when a table body row was clicked.
    This marks the row as selected and reads the evaluation cases.
    */
    // Get a timestamp for the click to help maintain the order in which evaluation cases are loaded
    var timestamp = new Date().getTime();
    last_show_article_request_timestamp = timestamp;

    // Show the loading GIF
    $("#loading").addClass("show");

    var approach_name = $(el).find('td:first').text();

    // De-select previously selected rows
    if (!is_compare_checked() || selected_approach_names.length >= MAX_SELECTED_APPROACHES) {
        deselect_all_table_rows();
        selected_approach_names = [];
    }

    if (!selected_approach_names.includes(approach_name)) {
        selected_approach_names.push(approach_name);
        // Select clicked row
        $(el).addClass("selected");
        selected_rows.push(el);
    }
    var selected_approaches = [...selected_approach_names];

    read_evaluation(approach_name, selected_approaches, timestamp);
}

function on_cell_click(el) {
    /*
    Highlight error category / type cells on click and un-highlight previously clicked cell.
    Add or remove error categories and types to/from current selection.
    */
    // Determine whether an already selected cell has been clicked
    var curr_row = $(el).closest("tr").index();
    var prev_selected_rows = $.map(selected_rows, function(sel_row) { return $(sel_row).index(); });
    var already_selected_row_clicked = $.inArray(curr_row, prev_selected_rows);

    if (selected_cells.length > 0) {
        if (!is_compare_checked() || selected_rows.length >= MAX_SELECTED_APPROACHES) {
            // Remove selected classes for all currently selected cells
            for (var i=0; i<selected_cells.length; i++) {
                remove_selected_classes(selected_cells[i]);
            }
            selected_cells = [];
            reset_selected_cell_categories();
        } else {
            // Remove selected class for cells in the same row
            var last_rows = $.map(selected_cells, function(sel_cell) { return $(sel_cell).closest('tr').index(); });
            var index = $.inArray(curr_row, last_rows);
            if (index >= 0) {
                remove_selected_classes(selected_cells[index]);
                selected_cells.splice(index, 1);
                selected_cell_categories[index] = null;
            }
        }
    }

    // Make new selection
    if ($(el).attr('class')) {  // System column has no class attribute
        var classes = $(el).attr('class').split(/\s+/);
        if (is_error_cell(el)) {
            $(el).addClass("selected");
            selected_cells.push(el);
        } else if (classes.length > 0 && (classes[0] in mention_type_headers || is_type_string(classes[0]))) {
            $(el).closest('tr').find('.' + classes[0]).each(function() {
                $(this).addClass("selected");
            });
            selected_cells.push(el);
        }
    }

    // Updated selected cell categories
    // Note that selected_rows is updated in on_row_click(), i.e. after on_cell_click() is called so no -1 necessary.
    approach_index = (already_selected_row_clicked >= 0 || !is_compare_checked()) ? 0 : selected_rows.length % MAX_SELECTED_APPROACHES;
    selected_cell_categories[approach_index] = get_error_category_or_type(el);
}

function deselect_all_table_rows() {
    /*
    Deselect all rows in all evaluation tables
    */
    $("#evaluation tbody tr").each(function() {
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

function get_error_category_or_type(el) {
    /*
    For a given cell return the error category or type it belongs to, or null otherwise.
    */
    if ($(el).attr('class')) {
        var classes = $(el).attr('class').split(/\s+/);
        if (is_error_cell(el)) {
            var keys = classes[1].split("-");
            return error_category_mapping[keys[0]][keys[1]];
        } if (is_type_string(classes[0])) {
            return [classes[0].replace(/(q[0-9]+)_.*/g, "$1")];
        } else if (classes[0] in mention_type_headers) {
            return mention_type_headers[classes[0]];
        }
    }
    return null;
}

function is_type_string(class_name) {
    var match = class_name.match(/[Qq][0-9]+.*/);
    if (match || class_name == "other") {
        return true;
    }
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
        var timestamp = new Date().getTime();
        last_show_article_request_timestamp = timestamp;

        if (selected_approach_names.length > 1) {
            selected_approach_names = [selected_approach_names[1]];
        }

        // De-select evaluation table row
        if (selected_rows.length > 1) {
            deselected_row = selected_rows.shift();  // Remove first element in array
            $(deselected_row).removeClass("selected");
            deselected_cell = selected_cells.shift();
            if (deselected_cell) remove_selected_classes(deselected_cell);
        }

        hide_table_column("prediction_overview", 1);

        show_article(selected_approach_names, timestamp);
    }
}

function is_compare_checked() {
    return $("#checkbox_compare").is(":checked");
}

function on_article_select() {
    var timestamp = new Date().getTime();
    last_show_article_request_timestamp = timestamp;
    show_article(selected_approach_names, timestamp);
}

function produce_latex() {
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
    $('#evaluation table thead tr').each(function(){
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
    $("#evaluation table tbody tr").each(function() {
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
    $("evaluation .latex").show();
    $("evaluation .latex textarea").val(latex_text);
    $("evaluation .latex textarea").show();  // Text is not selected or copied if it is hidden
    $("evaluation .latex textarea").select();
    document.execCommand("copy");
    $("evaluation .latex textarea").hide();

    // Show the notification for the specified number of seconds
    var show_duration_seconds = 5;
    setTimeout(function() { $("#evaluation .latex").hide(); }, show_duration_seconds * 1000);
}

