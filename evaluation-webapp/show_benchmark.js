// List of articles with ground truth information from the benchmark.
var articles = [];

// Colors for the tooltips.
GREEN = "#7dcea0";
RED = "#f1948a";
BLUE = "#bb8fce";
GREY = "lightgrey";


ignore_headers = ["true_positives", "false_positives", "false_negatives", "ground_truth"];
percentage_headers = ["precision", "recall", "f1"];

$("document").ready(function() {
    // Elements from the HTML document for later usage.
    textfield_left = document.getElementById("textfield_left");
    textfield_right = document.getElementById("textfield_right");
    article_select = document.getElementById("article");

    // Read the article and ground truth information from the benchmark.
    parse_benchmark();
    
    // Build an overview table over all .results-files from the evaluation-results folder.
    build_overview_table("evaluation-results");

    // Filter results by regex in input field #result-regex (from SPARQL AC evaluation)
    $("input#result-filter").focus();
    $("input#result-filter").keyup(function() {
      var filter_keywords = $(this).val().split(/\s+/);
      $("#evaluation tbody tr").each(function() {
        var name = $(this).children(":first-child").text();
        var show_row = filter_keywords.every(keyword => name.search(keyword) != -1);
        if (show_row) $(this).show(); else $(this).hide();
      });
    });
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

function build_overview_table(path) {
    /*
    Build the overview table from the .results files found at the given path.
    */
    console.log(path);
    folders = [];
    
    promise = new Promise(function(request_done) {
        $.get(path, function(data) {
            request_done(data);
        });    
    });
    
    promise.then(function(data) {
        // Get all folders from the evaluation results directory
        $(data).find("a").each(function() {
            name = $(this).attr("href");
            name = name.substring(0, name.length - 1);
            folders.push(name);
        });

        // Add a row to the results table for each .results file in the folders
        add_result_rows(path, folders);
    });
}

function add_result_rows(path, folders) {
    /*
    Read all .result files in the given folders, generate a table row for each
    and add them to the table body.
    */
    result_rows = [];
    result_files = {};
    folders.forEach(function(folder) {
        $.get(path + "/" + folder, function(folder_data) {
            $(folder_data).find("a").each(function() {
                file_name = $(this).attr("href");
                var file_extension = ".results";
                if (file_name.endsWith(file_extension)) {
                    var url = path + "/" + folder + "/" + file_name;
                    $.getJSON(url, function(results) {
                        approach_name = url.substring(url.lastIndexOf("/") + 1, url.length - file_extension.length);
                        result_files[approach_name] = path + "/" + folder + "/" + approach_name;

                        if (!$('#evaluation table thead').html()) {
                            // Add table header if it has not yet been added
                            var table_header = get_table_header(results);
                            $('#evaluation table thead').html(table_header);
                        }

                        if (!$('#checkboxes').html()) {
                            // Add checkboxes if they have not yet been added
                            add_checkboxes(results);
                        }

                        var row = get_table_row(approach_name, results);
                        $('#evaluation table tbody').append(row);
                    });
                }
            });
        });
    });
}

function add_checkboxes(jsonObj) {
    /*
    Add checkboxes for showing / hiding columns.
    */
    $.each(jsonObj, function(key) {
        var class_name = get_class_name(key);
        var title = get_title_from_key(key);
        var checkbox_html = "<input type=\"checkbox\" class=\"checkbox_" + class_name + "\" onchange=\"on_checkbox_change(this)\" checked>";
        checkbox_html += "<label>" + title + "</label>";
        $("#checkboxes").append(checkbox_html);
    });
}

function on_checkbox_change(element) {
    /*
    This function should be called when the state of a checkbox is changed.
    This can't be easily implemented in on document ready, because checkboxes are added dynamically.
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


function get_table_header(jsonObj) {
    /*
    Get html for the table header.
    */
    var num_first_cols = jsonObj.length;
    var num_header_rows = 2;
    var first_row = "<tr onclick='produce_latex()'>\n\t<th rowspan=\"" + num_header_rows + "\"></th>\n";
    var second_row = "<tr>\n";
    $.each(jsonObj, function(key) {
        var colspan = 0;
        var class_name = get_class_name(key);
        $.each(jsonObj[key], function(subkey) {
            if (!(ignore_headers.includes(subkey))) {
                second_row += "\t<th class='" + class_name + "'>" + get_title_from_key(subkey) + "</th>\n";
                colspan += 1;
            }
        });
        first_row += "\t<th colspan=\"" + colspan + "\" class='" + class_name + "'>" + get_title_from_key(key) + "</th>\n";

    });
    first_row += "</tr>\n";
    second_row += "</tr>\n";
    return first_row + second_row;
}

function get_class_name(text) {
    return text.toLowerCase().replace(/[ ,.#:]/g, "_");
}

function get_title_from_key(key) {
    return to_title_case(key.replace("_", " "));
}


function to_title_case(str) {
    return str.replace(/\w\S*/g, function(txt) {
        return txt.charAt(0).toUpperCase() + txt.substr(1);
    });
}


function get_table_row(approach_name, jsonObj) {
    /*
    Get html for the table row with the given approach name and result values.
    */
    var row = "<tr onclick='on_row_click(this)'>";
    row += "<td>" + approach_name + "</td>";
    $.each(jsonObj, function(key) {
        var class_name = get_class_name(key);
        var tooltip_text = "";
        $.each(jsonObj[key], function(subkey) {
            // Include only keys in the table, that are not on the ignore list
            if (!(ignore_headers.includes(subkey))) {
                var value = jsonObj[key][subkey];
                if (!value) {
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
                    processed_value += "<span class='tooltiptext'>" + get_tooltip_text(jsonObj[key]) + "</span></div>"
                    value = processed_value;
                }
                row += "<td class='" + class_name + "'>" + value + "</td>";
            }
        });

    })
    row += "</tr>";
    return row;
}

function get_tooltip_text(jsonObj) {
    tooltip_text = "TP: " + jsonObj["true_positives"] + "<br>";
    tooltip_text += "FP: " + jsonObj["false_positives"] + "<br>";
    tooltip_text += "FN: " + jsonObj["false_negatives"] + "<br>";
    tooltip_text += "GT: " + jsonObj["ground_truth"];
    return tooltip_text;
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
                var title = $(this).text();
                title = title.replace(/_/g, " ");  // Underscore not within $ yields error
                var colspan = parseInt($(this).attr("colspan"), 10);
                if (colspan) {
                    // First column header is empty and is skipped here, so starting with "&" works
                    header_string += "& \\multicolumn{" + colspan + "}{c}{\\textbf{" + title + "}} ";
                } else if (title) {
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
                if (match) {
                    text = match[1];
                }
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
    $("div.latex textarea").show();
    $("div.latex textarea").select();
    document.execCommand("copy");
    $("div.latex textarea").hide();

    // Show the notification for the specified number of seconds
    var show_duration_seconds = 5;
    setTimeout(function() { $("div.latex").hide(); }, show_duration_seconds * 1000);
}
