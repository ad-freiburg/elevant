// List of articles with ground truth information from the benchmark.
var articles = [];

// Colors for the tooltips.
GREEN = "#7dcea0";
RED = "#f1948a";
BLUE = "#bb8fce";
GREY = "lightgrey";

$("document").ready(function() {
    // Elements from the HTML document for later usage.
    textfield_left = document.getElementById("textfield_left");
    textfield_right = document.getElementById("textfield_right");
    article_select = document.getElementById("article");
    file_select = document.getElementById("evaluation_file");

    // Read the article and ground truth information from the benchmark.
    parse_benchmark();
    
    // Get all .case-files from the evaluation-results folder.
    get_approaches("evaluation-results");
});

function parse_benchmark() {
    /*
    Read the articles and ground truth labels from the benchmark.
    
    Reads the file development_labels.jsonl and adds each article to the list 'articles'.
    Each article is an object indentical to the parsed JSON-object, with an additional property 'labelled_text',
    which is the article text with HTML-hyperlinks for the ground truth entity mentions.
    
    Calls set_article_select_options(), which sets the options for the article selector element.
    */
    $.get("development_labels.jsonl",
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
    for (ai in articles) {
        article = articles[ai];
        var option = document.createElement("option");
        option.text = article.title;
        option.value = ai;
        article_select.add(option);
    }
    // Set default value to nothing.
    $("#article").prop("selectedIndex", -1);
}

function show_article_link() {
    /* Link the currently selected article in the element #article_link. */
    $("#article_link").html("<a href=\"" + article.url + "\" target=\"_blank\">Wikipedia article</a>");
}

function show_ground_truth_entities() {
    /*
    Generate tooltips for the ground truth entities of the selected article
    and show them in the left textfield.
    */
    annotations = [];
    for (eval_case of evaluation_cases[approach_index]) {
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
                "entity_id": eval_case.true_entity.entity_id
            };
            annotations.push(annotation);
        }
    }
    
    ground_truth_text = annotate_text(article.text, annotations, article.links);
    textfield_left.innerHTML = ground_truth_text;
}

function show_linked_entities() {
    /*
    Generate tooltips for the predicted entities of the selected approach and article
    and show them in the right textfield.
    
    This method first combines the predictions outside the evaluation span (from the file <approach>.jsonl)
    with the evaluated predictions inside the evaluation span (from the file <approach>.cases),
    and then generates tooltips for all of them.
    */
    article_cases = evaluation_cases[approach_index];  // information from the .cases file
    article_data = articles_data[approach_index];  // information from the .jsonl file
    
    // evaluation span
    evaluation_begin = article_data.evaluation_span[0];
    evaluation_end = article_data.evaluation_span[1];
    
    // list of all predicted mentions (inside and outside the evaluation span)
    mentions = [];
    
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
    annotations = []
    
    for (mention of mentions) {
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
            "predicted_by": predicted_by
        };
        annotations.push(annotation);
    }
    
    // generate tooltips and visualise them in the right textfield
    predicted_text = annotate_text(article.text, annotations, article.links);
    textfield_right.innerHTML = predicted_text;
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

function annotate_text(text, annotations, links) {
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
    for (annotation of annotations_with_links.reverse()) {
        // annotation is a tuple with (span, annotation_info)
        span = annotation[0];
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
            replacement = "<div class=\"tooltip\" style=\"background-color:" + annotation.color + "\">";
            replacement += snippet;
            replacement += "<span class=\"tooltiptext\">" + tooltip_text + "</span>";
            replacement += "</div>";
        } else {
            // no tooltip (just a link)
            replacement = snippet;
        }
        text = before + replacement + after;
    }
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
    
    for (eval_case of evaluation_cases[approach_index]) {
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
    /* Generate the ground truth textfield, predicted text field and cases table for the selected article and approach. */
    approach_index = article_select.value;
    
    if (approach_index == "") {
        return;
    }
    article = articles[approach_index];
    
    show_article_link();
    
    if (evaluation_cases.length == 0) {
        textfield_left.innerHTML = article.labelled_text;
        textfield_right.innerHTML = "ERROR: no file with cases found.";
        $("#table").html("");
        return;
    }
    
    show_ground_truth_entities();
    show_linked_entities();
    show_table();
}

function get_approaches(path) {
    /* Get a list of all approaches from the evaluation results at the given path. */
    console.log(path);
    folders = [];
    
    promise = new Promise(function(request_done) {
        $.get(path, function(data) {
            request_done(data);
        });    
    });
    
    promise.then(function(data) {
        // get all folders from the evaluation results directory
        $(data).find("a").each(function() {
            name = $(this).attr("href");
            name = name.substring(0, name.length - 1);
            folders.push(name);
        });
        // get all .cases files from the folders
        get_cases_files(path, folders);
    });
}

function get_cases_files(path, folders) {
    /*
    Get all .cases files from the subfolders of the given path.
    Sets the options for the approach selector element #evaluation_file.
    */
    result_files = {};
    folders.forEach(function(folder) {
        $.get(path + "/" + folder, function(folder_data) {
            console.log(path + "/" + folder);
            $(folder_data).find("a").each(function() {
                file_name = $(this).attr("href");
                if (file_name.endsWith(".cases")) {
                    approach_name = file_name.substring(0, file_name.length - 6);
                    result_files[approach_name] = path + "/" + folder + "/" + approach_name;
                    
                    option = document.createElement("option");
                    option.text = approach_name;
                    option.value = approach_name;
                    file_select.add(option);
                    
                    // Set default to nothing.
                    $("#evaluation_file").prop("selectedIndex", -1);
                }
            });
        });
    });
}

function run_evaluation(path) {
    /*
    Update the results table.
    
    Gets called when the selected approach changes.
    Reads the provided .cases file and counts true positives, false positives and false negatives.
    Calls show_article() to update the ground truth textfield, predictions textfield and cases table.
    */
    console.log(cases_path);
    
    evaluation_cases = [];
    
    n_tp = 0;
    n_fp = 0;
    n_fn = 0;
    
    $.get(path, function(data) {
        lines = data.split("\n");
        for (line of lines) {
            if (line.length > 0) {
                cases = JSON.parse(line);
                evaluation_cases.push(cases);
                
                for (eval_case of cases) {
                    if ("true_entity" in eval_case && "predicted_entity" in eval_case && eval_case.true_entity.entity_id == eval_case.predicted_entity.entity_id) {
                        n_tp += 1;
                    } else {
                        if ("true_entity" in eval_case) {
                            n_fn += 1;
                        }
                        if ("predicted_entity" in eval_case) {
                            n_fp += 1;
                        }
                    }
                }
            }
        }
        precision = n_tp / (n_tp + n_fp);
        recall = n_tp / (n_tp + n_fn);
        f1 = 2 * precision * recall / (precision + recall);
        $("#n_tp").html(n_tp);
        $("#n_fp").html(n_fp);
        $("#n_fn").html(n_fn);
        $("#precision").html((precision * 100).toFixed(2) + " %");
        $("#recall").html((recall * 100).toFixed(2) + " %");
        $("#f_score").html((f1 * 100).toFixed(2) + " %");
        $("#evaluation").show();
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

function read_evaluation() {
    /*
    Read the predictions and evaluation cases for the current approach for all articles,
    then run the evaluation and update the results table.
    */
    approach = $("#evaluation_file").val();

    cases_path = result_files[approach] + ".cases";
    articles_path = result_files[approach] + ".jsonl";

    reading_promise = read_articles_data(articles_path);
    reading_promise.then(function() {  // wait until the predictions from the .jsonl file are read, because run_evaluation updates the prediction textfield
        run_evaluation(cases_path);
    });
}
