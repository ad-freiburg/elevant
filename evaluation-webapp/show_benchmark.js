// Colors for the tooltips.
GREEN = ["rgb(125,206,160)", "rgba(125,206,160, 0.3)"]; // "#7dcea0";
RED = ["rgb(241,148,138)", "rgba(241,148,138, 0.3)"];  // "#f1948a";
BLUE = ["rgb(187,143,206)", "rgba(187,143,206, 0.3)"]; // "#bb8fce";
GREY = ["rgb(211,211,211)", "rgba(211,211,211, 0.3)"]; // "lightgrey";

RESULTS_EXTENSION = ".results";

ignore_headers = ["true_positives", "false_positives", "false_negatives", "ground_truth"];
percentage_headers = ["precision", "recall", "f1"];
copy_latex_text = "Copy LaTeX code for table";

header_descriptions = {"undetected": "The span of a GT mention was not linked (= NER FN) / Named GT mentions",
                       "undetected_lowercase": "The span of a lowercase GT mention was not linked / Named lowercase GT mentions",
                       "specificity": "FN and a part of the GT mention was linked to an arbitrary entity / Named GT mentions containing whitespace(s)",
                       "rare": "Mention was linked to a popular entity instead of the true, less popular entity / Named detected",
                       "demonym": "FN from a list of demonyms (German, Germans, ...) / All demonym GT mentions",
                       "partial_name": "FN and the GT mention is part of the entity name / Named GT mentions where the mention is a part of the entity name",
                       "abstraction": "Named FP that does not overlap with a GT mention",
                       "hyperlink": "FN where the mention is a hyperlink / GT mentions that are hyperlinks",
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

show_mentions = {"named": true, "nominal": true, "pronominal": true};

benchmark_names = ["ours", "conll", "conll-dev", "conll-test", "ace", "msnbc"];

error_category_mapping = {"undetected": "UNDETECTED",
    "undetected_lowercase": "UNDETECTED_LOWERCASE",
    "wrong_candidates": "WRONG_CANDIDATES",
    "": "MULTI_CANDIDATES_CORRECT",
    "multi_candidates": "MULTI_CANDIDATES_WRONG",
    "specificity": "SPECIFICITY",
    "rare": "RARE",
    "": "DEMONYM_CORRECT",
    "demonym": "DEMONYM_WRONG",
    "": "PARTIAL_NAME_CORRECT",
    "partial_name": "PARTIAL_NAME_WRONG",
    "abstraction": "ABSTRACTION",
    "": "HYPERLINK_CORRECT",
    "hyperlink": "HYPERLINK_WRONG",
    "non_entity_coreference": "NON_ENTITY_COREFERENCE",
    "referenced_wrong": "COREFERENCE_REFERENCED_WRONG",
    "wrong_reference": "COREFERENCE_WRONG_REFERENCE",
    "no_reference": "COREFERENCE_NO_REFERENCE"}

$("document").ready(function() {
    // Elements from the HTML document for later usage.
    textfield_left = document.getElementById("textfield_left");
    textfield_right = document.getElementById("textfield_right");
    benchmark_select = document.getElementById("benchmark");
    article_select = document.getElementById("article");

    show_all_articles_flag = false;
    show_selected_error = null;

    last_selected_cell = null;

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
        show_ground_truth_entities();
        show_linked_entities();
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

    // Highlight error category cells on click and un-highlight previously clicked cell
    $("#evaluation").on("click", "td", function() {
        if (last_selected_cell) {
            $(last_selected_cell).removeClass("selected");
        }
        if ($(this).attr('class')) {  // System column has no class attribute
            var classes = $(this).attr('class').split(/\s+/);
            if (classes.length > 1 && classes[1] in error_category_mapping) {
                $(this).addClass("selected");
                last_selected_cell = this;
            }
        }
    });
});

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
        // Set default value to "ours".
        $('#benchmark option:contains("ours")').prop('selected',true);
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
    $("#evaluation table thead").empty();
    $("#evaluation table tbody").empty();

    // Remove previous article evaluation content
    $("#article-results .row").hide();
    evaluation_cases = [];

    // Build an overview table over all .results-files from the evaluation-results folder.
    build_overview_table("evaluation-results", benchmark_name);

    // Read the article and ground truth information from the benchmark.
    parse_benchmark(benchmark_file);
}

function filter_table_rows() {
    var filter_keywords = $.trim($("input#result-filter").val()).split(/\s+/);
    var match_type_and = $("#radio_and").is(":checked");
    $("#evaluation tbody tr").each(function() {
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
    Each article is an object indentical to the parsed JSON-object, with an additional property 'labelled_text',
    which is the article text with HTML-hyperlinks for the ground truth entity mentions.
    
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
                    labelled_text = json.text;
                    for (label of json.labels.reverse()) {
                        span = label[0];
                        begin = span[0];
                        end = span[1];
                        entity_id = label[1];
                        wikidata_url = "https://www.wikidata.org/wiki/" + entity_id;
                        before = labelled_text.substring(0, begin);
                        after = labelled_text.substring(end);
                        entity_text = labelled_text.substring(begin, end);
                        entity_representation = entity_text + " [" + entity_id + "]";
                        link = "<a href=\"" + wikidata_url + "\">" + entity_representation +"</a>";
                        labelled_text = before + link + after;
                    }
                    labelled_text = labelled_text.replaceAll("\n", "<br>");
                    json.labelled_text = labelled_text;
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
        // Conll articles don't have a title. In that case use the first 40 characters of the article
        option.text = (article.title) ? article.title : article.text.substring(0, Math.min(40, article.text.length)) + "...";
        option.value = ai;
        article_select.add(option);
    }
}

function show_article_link() {
    /* Link the currently selected article in the element #article_link. */
    $("#article_link").html("<a href=\"" + article.url + "\" target=\"_blank\">Wikipedia article</a>");
    $("#article_link").show();
}

function show_ground_truth_entities() {
    /*
    Generate tooltips for the ground truth entities of the selected article
    and show them in the left textfield.
    */
    if (show_all_articles_flag) {
        var ground_truth_texts = [];
        for (var i=0; i < articles.length; i++) {
            var annotations = get_ground_truth_annotations(i);
            ground_truth_texts.push(annotate_text(articles[i].text, annotations, articles[i].links, articles[i].evaluation_span));
        }
        var ground_truth_text = ground_truth_texts.join("<br>-----------------<br><br>");
    } else {
        var annotations = get_ground_truth_annotations(selected_article_index);
        var ground_truth_text = annotate_text(article.text, annotations, article.links, [0, article.text.length]);
    }
    textfield_left.innerHTML = ground_truth_text;
}

function get_ground_truth_annotations(article_index) {
    /*
    Generate annotations for the ground truth entities of the selected article.
    */
    var annotations = [];

    for (eval_case of evaluation_cases[article_index]) {
        if (eval_case.mention_type && eval_case.mention_type.toLowerCase() in show_mentions) {
            if (!show_mentions[eval_case.mention_type.toLowerCase()]) {
                continue;
            }
        }
        if ("true_entity" in eval_case) {
            if ("predicted_entity" in eval_case) {
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
            var annotation = {
                "span": eval_case.span,
                "color": color,
                "entity_name": eval_case.true_entity.name,
                "entity_id": eval_case.true_entity.entity_id,
                "error_labels": eval_case.error_labels
            };
            annotations.push(annotation);
        }
    }
    return annotations
}

function show_linked_entities() {
    /*
    Generate tooltips for the predicted entities of the selected approach and article
    and show them in the right textfield.
    */
    if (show_all_articles_flag) {
        var predicted_texts = [];
        for (var i=0; i < articles.length; i++) {
            var annotations = get_predicted_annotations(i);
            predicted_texts.push(annotate_text(articles[i].text, annotations, articles[i].links, articles[i].evaluation_span));
        }
        var predicted_text = predicted_texts.join("<br>-----------------<br><br>");
    } else {
        var annotations = get_predicted_annotations(selected_article_index);
        var predicted_text = annotate_text(article.text, annotations, article.links, [0, article.text.length]);
    }
    textfield_right.innerHTML = predicted_text;
}

function get_predicted_annotations(article_index) {
    /*
    Generate annotations for the predicted entities of the selected approach and article.

    This method first combines the predictions outside the evaluation span (from the file <approach>.jsonl)
    with the evaluated predictions inside the evaluation span (from the file <approach>.cases),
    and then generates annotations for all of them.
    */
    var article_cases = evaluation_cases[article_index];  // information from the .cases file
    var article_data = articles_data[article_index];  // information from the .jsonl file

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
    var annotations = []

    for (mention of mentions) {
        if (mention.mention_type && mention.mention_type.toLowerCase() in show_mentions) {
            if (!show_mentions[mention.mention_type.toLowerCase()]) {
                continue;
            }
        }
        if ("true_entity" in mention || "predicted_entity" in mention) {  // mention is inside the evaluation span and therefore an evaluated case
            if ("true_entity" in mention) {
                if (mention.true_entity.entity_id == mention.predicted_entity.entity_id) {
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
            entity_id = mention.predicted_entity.entity_id;
            entity_name = mention.predicted_entity.name;
            predicted_by = mention.predicted_by;
        } else {  // mention is outside the evaluation span
            color = GREY;
            entity_id = mention.id;
            entity_name = null;
            predicted_by = mention.linked_by;
        }
        var annotation = {
            "span": mention.span,
            "color": color,
            "entity_id": entity_id,
            "entity_name": entity_name,
            "predicted_by": predicted_by,
            "error_labels": mention.error_labels
        };
        annotations.push(annotation);
    }
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

function annotate_text(text, annotations, links, evaluation_span) {
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
    // STEP 2: Add the combined annotations and links to the text.
    // This is done in reverse order so that the text before is always unchanged. This allows to use the spans as given.
    cutoff_done = false;
    for (annotation of annotations_with_links.reverse()) {
        // annotation is a tuple with (span, annotation_info)
        span = annotation[0];

        if (span[1] > evaluation_span[1]) {
            continue;
        } else if (span[0] < evaluation_span[0]) {
            break;
        } else if (!cutoff_done){
            cutoff_done = true;
            text = text.substring(0, evaluation_span[1]);
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
            if (annotation.hasOwnProperty("span")) {
                tooltip_text += "<br>span=(" + annotation.span[0] + ", " + annotation.span[1] + ")";
            }
            if (annotation.hasOwnProperty("predicted_by")) {
                tooltip_text += "<br>predicted_by=" + annotation.predicted_by;
            }
            if (annotation.hasOwnProperty("error_labels") && annotation.error_labels.length > 0) {
                tooltip_text += "<br>error=";
                for (var e_i = 0; e_i < annotation.error_labels.length; e_i += 1) {
                    if (e_i > 0) {
                        tooltip_text += ",";
                    }
                    tooltip_text += annotation.error_labels[e_i];
                }
            }
            // Only show selected error category
            var color = annotation.color[0];
            if (show_selected_error && annotation.error_labels &&
                    !annotation.error_labels.includes(show_selected_error)) {
                // Use transparent version of the color, if an error category is selected
                // And the current annotation does not have the corresponding error label
                color = annotation.color[1];
            }
            replacement = "<div class=\"tooltip\" style=\"background-color:" + color + "\">";
            replacement += snippet;
            replacement += "<span class=\"tooltiptext\">" + tooltip_text + "</span>";
            replacement += "</div>";
        } else {
            // no tooltip (just a link)
            replacement = snippet;
        }
        text = before + replacement + after;
    }
    text = text.substring(evaluation_span[0], text.length);
    text = text.replaceAll("\n", "<br>");
    return text;
}

function show_table() {
    /* Generate the table with all cases. */
    table = "<table class=\"casesTable\">\n";
    
    table += "<tr>";
    table += "<th>span</th>";
    table += "<th>text</th>";
    table += "<th>true ID</th>";
    table += "<th>true name</th>";
    table += "<th>detected</th>";
    table += "<th>predicted ID</th>";
    table += "<th>predicted name</th>";
    table += "<th>case</th>";
    table += "</tr>";
    
    for (eval_case of evaluation_cases[selected_article_index]) {
        if (eval_case.mention_type && eval_case.mention_type.toLowerCase() in show_mentions) {
            if (!show_mentions[eval_case.mention_type.toLowerCase()]) {
                continue;
            }
        }

        if ("true_entity" in eval_case) {
            has_true_entity = true;
            true_entity_id = eval_case.true_entity.entity_id;
            true_entity_name = eval_case.true_entity.name;
        } else {
            has_true_entity = false;
            true_entity_id = "-";
            true_entity_name = "-";
        }
        
        if (has_true_entity) {
            if (eval_case.detected) {
                detected = "true positive";
            } else {
                detected = "false negative";
            }
        } else {
            detected = "false positive";
        }
        
        if ("predicted_entity" in eval_case) {
            has_prediction_entity = true;
            predicted_entity_id = eval_case.predicted_entity.entity_id;
            predicted_entity_name = eval_case.predicted_entity.name;
        } else {
            has_prediction_entity = false;
            predicted_entity_id = "-";
            predicted_entity_name = "-";
        }
        
        if (has_prediction_entity && has_true_entity) {
            if (predicted_entity_id == true_entity_id) {
                case_type = "true positive";
            } else {
                case_type = "wrong entity";
            }
        } else if (has_prediction_entity) {
            case_type = "false positive";
        } else {
            case_type = "false negative";
        }
    
        table += "<tr>";
        table += "<td>" + eval_case.span[0] + ", " + eval_case.span[1] + "</td>";
        table += "<td>" + article.text.substring(eval_case.span[0], eval_case.span[1]) + "</td>";
        table += "<td>" + true_entity_id + "</td>";
        table += "<td>" + true_entity_name + "</td>";
        table += "<td>" + detected + "</td>";
        table += "<td>" + predicted_entity_id + "</td>";
        table += "<td>" + predicted_entity_name + "</td>";
        table += "<td>" + case_type + "</td>";
        table += "</tr>\n";
    }
    table += "</table>";
    $("#table").html(table);
}

function show_article() {
    /*
    Generate the ground truth textfield, predicted text field and cases table for the selected article
    (or all articles if this option is selected) and approach.
    */
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

    $("#article-results .row").show();

    if (evaluation_cases.length == 0) {
        textfield_left.innerHTML = article.labelled_text;
        textfield_right.innerHTML = "<b class='warning'>No approach selected or no file with cases found.</b>";
        return;
    }

    show_ground_truth_entities();
    show_linked_entities();
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
                    // file extension if it is not our benchmark.
                    benchmark = file_name.split(".").slice(-2)[0];
                    benchmark_match = ((benchmark_name == "ours" && !benchmark_names.includes(benchmark)) || benchmark == benchmark_name);
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
                        var table_header = get_table_header(results);
                        $('#evaluation table thead').html(table_header);
                    }

                    if (!$('#checkboxes').html()) {
                        // Add checkboxes if they have not yet been added
                        add_checkboxes(results);
                    }
                });
                // Add table body
                build_overview_table_body(result_array);
            });
        });
    });
}

function build_overview_table_body(result_list) {
    /*
    Build the table body.
    Show / Hide rows and columns according to checkbox state and filter-result input field.
    */
    // Add table rows in new sorting order
    result_list.forEach(function(result_tuple) {
        var approach_name = result_tuple[0];
        var results = result_tuple[1];
        var row = get_table_row(approach_name, results);
        $('#evaluation table tbody').append(row);
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
        var class_name = get_class_name(key);
        var title = get_title_from_key(key);
        var checked = (class_name == "all") ? "checked" : ""
        var checkbox_html = "<input type=\"checkbox\" class=\"checkbox_" + class_name + "\" onchange=\"show_hide_columns(this)\" " + checked + ">";
        checkbox_html += "<label>" + title + "</label>";
        $("#checkboxes").append(checkbox_html);
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
}

function get_table_header(json_obj) {
    /*
    Get html for the table header.
    */
    var num_first_cols = json_obj.length;
    var first_row = "<tr><th onclick='produce_latex()' class='produce_latex'>" + copy_latex_text + "</th>";
    var second_row = "<tr><th onclick='sort_table(this)'>System<span class='sort_symbol'>&#9660</span></th>";
    $.each(json_obj, function(key) {
        var colspan = 0;
        var class_name = get_class_name(key);
        $.each(json_obj[key], function(subkey) {
            if (!(ignore_headers.includes(subkey))) {
                second_row += "<th class='" + class_name + "' onclick='sort_table(this)'><div class='tooltip'>" + get_title_from_key(subkey) + "<span class='sort_symbol'>&#9660</span>";
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

function get_table_row(approach_name, json_obj) {
    /*
    Get html for the table row with the given approach name and result values.
    */
    var row = "<tr onclick='on_row_click(this)'>";
    row += "<td onclick=\"show_selected_errors('system')\">" + approach_name + "</td>";
    $.each(json_obj, function(key) {
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
                    var composite_value = "";
                    $.each(value, function(subsubkey) {
                        var val = value[subsubkey];
                        composite_value += val + " / ";
                    });
                    value = composite_value.substring(0, composite_value.length - " / ".length);
                } else if (percentage_headers.includes(subkey)) {
                    // Get rounded percentage but only if number is a decimal < 1
                    processed_value = "<div class='" + class_name + " tooltip'>"
                    processed_value += (value * 100).toFixed(2) + "%";
                    // Create tooltip text
                    processed_value += "<span class='tooltiptext'>" + get_tooltip_text(json_obj[key]) + "</span></div>"
                    value = processed_value;
                }
                var subclass_name = get_class_name(subkey);
                var onclick_string = "onclick=\"show_selected_errors('" + subclass_name + "')\"";
                row += "<td class='" + class_name + " " + subclass_name + "' " + onclick_string + ">" + value + "</td>";
            }
        });
    })
    row += "</tr>";
    return row;
}

function show_selected_errors(error_category) {
    if (error_category in error_category_mapping) {
        show_selected_error = error_category_mapping[error_category];
        show_article();
    } else {
        show_selected_error = null;
    }
}

function get_tooltip_text(json_obj) {
    tooltip_text = "TP: " + json_obj["true_positives"] + "<br>";
    tooltip_text += "FP: " + json_obj["false_positives"] + "<br>";
    tooltip_text += "FN: " + json_obj["false_negatives"] + "<br>";
    tooltip_text += "GT: " + json_obj["ground_truth"];
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
    var col_values = [];
    $('#evaluation table tbody tr td:nth-child(' + col_index + ')').each(function() {
        var text = $(this).html();
        var match = text.match(/<div [^<>]*>([^<>]*)<(span|div)/);
        if (match) {
            text = match[1];
        }
        col_values.push(text);
    });

    // Store approach name of currently selected row
    var selected_approach = $("#evaluation table tbody tr.selected");
    var selected_approach_index = selected_approach.parent().children().index($(selected_approach));  // 0-based

    // Store class name of currently selected cell
    var selected_cell_classes = $("#evaluation table tbody td.selected").attr("class");
    if (selected_cell_classes) {
        selected_cell_classes = selected_cell_classes.split(/\s+/);
        selected_cell_classes.pop();  // We don't want the "selected" class
        selected_cell_classes = "." + selected_cell_classes.join(".");
    }

    // Check if sorting should be ascending or descending
    var descending = !$(column_header).hasClass("desc");

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
    build_overview_table_body(result_array);

    // Re-add selected class to previously selected row
    var new_selected_approach_index = order.indexOf(selected_approach_index) + 1;  // +1 because nth-child is 1-based
    $("#evaluation table tbody tr:nth-child(" + new_selected_approach_index + ")").addClass("selected");

    // Re-add selected class to previously selected cell
    last_selected_cell = $("#evaluation table tbody tr:nth-child(" + new_selected_approach_index + ") td" + selected_cell_classes);
    $(last_selected_cell).addClass("selected");
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

function read_evaluation_cases(path) {
    /*
    Retrieve evaluation cases from the given file and show the linked currently selected article.
    */
    evaluation_cases = [];

    $.get(path, function(data) {
        lines = data.split("\n");
        for (line of lines) {
            if (line.length > 0) {
                cases = JSON.parse(line);
                evaluation_cases.push(cases);
            }
        }
        show_article();
    }).fail(function() {
        $("#evaluation").html("ERROR: no file with cases found.");
        show_article();
    });
}

function read_articles_data(path) {
    /*
    Read the predictions of the selected approach for all articles.
    They are needed later to visualise the predictions outside the evaluation span of an article.
    
    Arguments:
    - path: the .jsonl file of the selected approach
    */
    console.log(path);
    
    articles_data = [];
    
    promise = $.get(path, function(data) {
        lines = data.split("\n");
        for (line of lines) {
            if (line.length > 0) {
                articles_data.push(JSON.parse(line));
            }
        }
    });
    return promise;
}

function on_row_click(el) {
    /*
    This method is called when a table body row was clicked.
    This marks the row as selected and reads the evaluation cases.
    */
    $("#evaluation tbody tr").each(function() {
        $(this).removeClass("selected");
    });
    $(el).addClass("selected");
    var approach_name = $(el).find('td:first').text();
    read_evaluation(approach_name);
}

function read_evaluation(approach_name) {
    /*
    Read the predictions and evaluation cases for the selected approach for all articles.
    */
    cases_path = result_files[approach_name] + ".cases";
    articles_path = result_files[approach_name] + ".jsonl";

    reading_promise = read_articles_data(articles_path);
    reading_promise.then(function() {  // wait until the predictions from the .jsonl file are read, because run_evaluation updates the prediction textfield
        read_evaluation_cases(cases_path);
    });
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
    $("div.latex").show();
    $("div.latex textarea").val(latex_text);
    $("div.latex textarea").show();  // Text is not selected or copied if it is hidden
    $("div.latex textarea").select();
    document.execCommand("copy");
    $("div.latex textarea").hide();

    // Show the notification for the specified number of seconds
    var show_duration_seconds = 5;
    setTimeout(function() { $("div.latex").hide(); }, show_duration_seconds * 1000);
}
