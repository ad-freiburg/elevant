ANNOTATION_CLASS_TP = "tp";
ANNOTATION_CLASS_FP = "fp";
ANNOTATION_CLASS_FN = "fn";
ANNOTATION_CLASS_UNKNOWN = "unknown";
ANNOTATION_CLASS_OPTIONAL = "optional";
ANNOTATION_CLASS_UNEVALUATED = "unevaluated";

RESULTS_EXTENSION = ".results";
EVALUATION_RESULT_PATH = "evaluation-results";

EXAMPLE_BENCHMARK_PATH = "example-benchmark/error-category-examples.benchmark.jsonl";
EXAMPLE_BENCHMARK_RESULTS_PATH = "example-benchmark/example.error-category-examples.results";

MAX_SELECTED_APPROACHES = 2;
MAX_CACHED_FILES = 15;

MISSING_LABEL_TEXT = "[MISSING LABEL]";
NO_LABEL_ENTITY_IDS = ["QUANTITY", "DATETIME", "Unknown"];

ignore_headers = ["true_positives", "false_positives", "false_negatives", "ground_truth"];
percentage_headers = ["precision", "recall", "f1"];
copy_latex_text = "Copy LaTeX code for table";

tooltip_example_html = " <a href=\"#example_benchmark_modal\"onclick=\"show_example_benchmark_modal(this)\" data-toggle=\"modal\" data-target=\"#example_benchmark_modal\">For an example click here</a>.";
header_descriptions = {
    "undetected": {
        "all": "The span of a GT mention was not linked (= NER FN) (Total: Named GT mentions).",
        "lowercase": "The span of a lowercase GT mention was not linked (Total: Named lowercase GT mentions).",
        "partially_included": "FN and a part of the GT mention was linked to an arbitrary entity (Total: Named GT mentions containing whitespace(s)).",
        "partial_overlap": "FN and the GT span overlaps with a predicted span (Total: Named uppercase GT mentions).",
        "other": "Other detection error (Total: Named uppercase GT mentions)."
    },
    "wrong_disambiguation": {
        "all": "Detected, but wrong entity linked (Total: Detected).",
        "demonym": "FN from a list of demonyms (German, Germans, ...) (Total: All demonym GT mentions).",
        "partial_name": "FN and the GT mention is part of the entity name (Total: Named GT mentions where the mention is a part of the entity name).",
        "metonymy": "Predicted and most popular candidate are locations, but ground truth is not (Total: Most popular candidate is a location, but ground truth is not).",
        "rare": "Most popular candidate is wrongly predicted (Total: Detected mentions where the most popular candidate is not the correct entity).",
        "other": "Other disambiguation error",
        "wrong_candidates": "A GT mention was recognized but the GT entity is not among the candidates (Total: Named detected).",
        "multi_candidates": "A GT mention was recognized and the GT entity is one of the candidates, but the wrong candidate was selected (Total: Named detected where the GT entity is one of multiple candidates)."
    },
    "false_detection": {
        "all": "Predicted mention that does not match a groundtruth mention span",
        "abstract_entity": "Lowercase named FP that does not overlap with a GT mention",
        "unknown_entity": "Uppercase mention wrongly linked, where the ground truth is either Unknown or has no label at all",
        "other": "Other false detection",
        "wrong_span": "Predicted mention whose span does not match, but overlaps with a GT mention with a matching entity (Total: Predicted mentions)."
    },
    "other_errors": {
        "hyperlink": "FN where the mention is a hyperlink (Total: GT mentions that are hyperlinks)."
    },
    "wrong_coreference": {
        "false_detection": "FP mentions in {It, it, This, this, That, that, Its, its}",
        "reference_wrongly_disambiguated": "FN + FP, the reference was wrongly disambiguated (Total: Coreference mentions where correct GT mention was referenced).",
        "wrong_mention_referenced": "FN + FP, wrong mention was referenced (Total: Linked GT coreference mentions).",
        "undetected": "FN, mention was not linked (Total: GT coreference mentions)."
    }
};

error_category_mapping = {
    "undetected": {
        "all": ["UNDETECTED"],
        "lowercase": ["UNDETECTED_LOWERCASE"],
        "partially_included": ["UNDETECTED_PARTIALLY_INCLUDED"],
        "partial_overlap": ["UNDETECTED_PARTIAL_OVERLAP"],
        "other": ["UNDETECTED_OTHER"]
    },
    "wrong_disambiguation": {
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
        "abstract_entity": ["FALSE_DETECTION_ABSTRACT_ENTITY"],
        "unknown_entity": ["FALSE_DETECTION_UNKNOWN_ENTITY"],
        "other": ["FALSE_DETECTION_OTHER"],
        "wrong_span": ["FALSE_DETECTION_WRONG_SPAN"]
    },
    "other_errors": {
        "hyperlink": ["HYPERLINK_WRONG"]
    },
    "wrong_coreference": {
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

$("document").ready(function() {
    read_url_parameters();

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

    type_name_mapping = {};

    $("#checkbox_compare").prop('checked', url_param_compare);

    read_example_benchmark_data();

    set_benchmark_select_options();

    // Filter results by regex in input field #result-regex (from SPARQL AC evaluation)
    // Filter on key up
    $("input#result-filter").keyup(function() {
        filter_table_rows();

        // Update current URL without refreshing the site
        const url = new URL(window.location);
        url.searchParams.set('system_filter', $("input#result-filter").val());
        window.history.replaceState({}, '', url);
    });

    // Highlight error category cells on hover
    $("#evaluation_table_wrapper").on("mouseenter", "td", function() {
        if (is_error_cell(this)) {
            $(this).addClass("hovered");
        }
    });
    $("#evaluation_table_wrapper").on("mouseleave", "td", function() {
        $(this).removeClass("hovered");
    });

    // Highlight all cells in a row belonging to the same mention_type or type or the "all" column on hover
    $("#evaluation_table_wrapper").on("mouseenter", "td", function() {
        if ($(this).attr('class')) {
            var cls = $(this).attr('class').split(/\s+/)[0];
            if (cls in mention_type_headers || is_type_string(cls) || cls == "all") {
                // Mark all cells in the corresponding row with the corresponding class
                $(this).closest('tr').find('.' + cls).each(function(index) {
                    $(this).addClass("hovered");
                });
            }
        }
    });
    $("#evaluation_table_wrapper").on("mouseleave", "td", function() {
        if ($(this).attr('class')) {
            var cls = $(this).attr('class').split(/\s+/)[0];
            if (cls in mention_type_headers || is_type_string(cls) || cls == "all") {
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
    $("#evaluation_table_wrapper").on("mouseenter", ".tooltip", function() {
        position_table_tooltip(this);
    });

    // Tooltips need to be repositioned on window resize
    // otherwise some might overlap with the left window edge.
    $(window).on('resize', function(){
        $("#prediction_overview").find(".tooltiptext").each(function() {
            if ($(this).css("right") == "0px") $(this).css({"right": "auto", "left": "0px"});
        });
    });

    // Set the result filter string and show-deprecated checkbox according to the URL parameters
    if (url_param_filter_string) $("input#result-filter").val(url_param_filter_string);
    $("#checkbox_deprecated").prop('checked', url_param_show_deprecated);
    if (url_param_filter_string || !url_param_show_deprecated) filter_table_rows();

    // Synchronize the top and bottom scrollbar of the evaluation table
    // Prevent double calls to .scroll() by using a flag
    var second_call = false;
    $("#evaluation_table_wrapper").scroll(function(){
        if (!second_call) {
            $("#top_scrollbar_wrapper").scrollLeft($("#evaluation_table_wrapper").scrollLeft());
            second_call = true;
        } else {
            second_call = false;
        }
    });
    $("#top_scrollbar_wrapper").scroll(function(){
        if (!second_call) {
            $("#evaluation_table_wrapper").scrollLeft($("#top_scrollbar_wrapper").scrollLeft());
            second_call = true;
        } else {
            second_call = false;
        }
    });

    $("#evaluation_table_wrapper table").tablesorter({
        sortInitialOrder: 'desc',
        selectorHeaders: '> thead > tr:last-child > th',  // First header row should not be sortable
        stringTo: "bottom",  // Columns that are numerically sorted should always have strings (e.g. "-") at the bottom
        widgets: ['stickyHeaders'],
        widgetOptions: {
                        stickyHeaders_attachTo: '#evaluation_table_wrapper',  // jQuery selector or object to attach sticky header to
                        stickyHeaders_zIndex : 20,
                       },
        sortRestart: true
    });

    // Update URL on table sort
    $("#evaluation_table_wrapper table").bind("sortEnd",function() {
        // Update current URL without refreshing the site
        var sort_order = $("#evaluation_table_wrapper table")[0].config.sortList;
        const url = new URL(window.location);
        url.searchParams.set('sort_order', sort_order.join(","));
        window.history.replaceState({}, '', url);
    });

    reset_annotation_selection();
    $(document).on("keydown", function(event) {
        if ($("input#result-filter").is(":focus") || $("#benchmark").is(":focus") || $("#article_select").is(":focus")) return;
        if ([39, 37].includes(event.which)) {
            all_highlighted_annotations = [[], []];
            all_highlighted_annotations[0] = $("#prediction_overview td:nth-child(1) .annotation.beginning").not(".lowlight");
            if (selected_approach_names.length > 1) {
                all_highlighted_annotations[1] = $("#prediction_overview td:nth-child(2) .annotation.beginning").not(".lowlight");
            }
            if (event.ctrlKey && event.which == 39) {
                // Jump to next error highlight
                scroll_to_next_annotation(true);
            } else if (event.ctrlKey && event.which == 37) {
                scroll_to_previous_annotation(true);
            } else if (event.which == 39) {
                // Jump to next highlight
                scroll_to_next_annotation(false);
            } else if (event.which == 37) {
                // Jump to previous highlight
                scroll_to_previous_annotation(false);
            }
        }
    });
});

function get_type_label(qid) {
    var qid_lower = qid.toLowerCase();
    if (qid_lower in type_name_mapping) {
        return type_name_mapping[qid_lower];
    }
    return qid + " (label missing)";
}

function read_example_benchmark_data() {
    var filename = EXAMPLE_BENCHMARK_RESULTS_PATH.substring(0, EXAMPLE_BENCHMARK_RESULTS_PATH.length - RESULTS_EXTENSION.length);
    var articles_path = filename + ".jsonl";
    var cases_path = filename + ".cases";

    articles_example_benchmark = [];
    $.get(EXAMPLE_BENCHMARK_PATH, function(data) {
        lines = data.split("\n");
        for (line of lines) {
            if (line.length > 0) {
                articles_example_benchmark.push(JSON.parse(line));
            }
        }
    });

    articles_data_example_benchmark = [];
    evaluation_cases_example_benchmark = [];
    var promise = $.get(articles_path, function(data) {
        lines = data.split("\n");
        for (line of lines) {
            if (line.length > 0) {
                articles_data_example_benchmark.push(JSON.parse(line));
            }
        }
    }).then(function() {
        $.get(cases_path, function(data) {
            lines = data.split("\n");
            for (line of lines) {
                if (line.length > 0) {
                    evaluation_cases_example_benchmark.push(JSON.parse(line));
                }
            }
        });
    });
}

function show_example_benchmark_modal(el) {
    /*
    Open the example benchmark model and show the example article that corresponds
    to the error category of the clicked table header tooltip.
    */
    // Get example error category of the table tooltip to highlight only corresponding mentions
    var selected_category = get_error_category_or_type($(el).closest("th")[0]);

    // Get table header title
    var table_header_cell = $(el).closest("th")[0];
    var classes = $(table_header_cell).attr('class').split(/\s+/);
    var error_category_title = classes[1].replace(/_/g, " ").replace("-", " - ");

    // Determine article index of selected example
    var article_index = 0;
    for (var i=0; i<articles_example_benchmark.length; i++) {
        var article = articles_example_benchmark[i];
        if (article.title.toLowerCase().includes(error_category_title)) {
            article_index = i;
            break;
        }
    }

    // Display annotated text
    var textfield = $("#example_prediction_overview tr td");
    show_annotated_text("example_annotations", $(textfield[0]), selected_category, 100, article_index, true);
    $("#example_prediction_overview tr th").text(articles_example_benchmark[article_index].title);
}

function scroll_to_next_annotation(only_errors) {
    /*
    Scroll to the next annotation in the list of all annotations on the left and on the right side.
    */
    // Get potential next highlighted annotation for left and right side
    var next_annotation_index = [-1, -1];
    var next_annotations = [null, null];
    for (var i=0; i<2; i++) {
        if (all_highlighted_annotations[i].length == 0) continue;
        if (jump_to_annotation_index[i] + 1 < all_highlighted_annotations[i].length) {
            if (only_errors) {
                next_annotation_index[i] = find_next_annotation_index(i);
                if (next_annotation_index[i] < all_highlighted_annotations[i].length) next_annotations[i] = all_highlighted_annotations[i][next_annotation_index[i]];
            } else {
                next_annotation_index[i] = jump_to_annotation_index[i] + 1;
                next_annotations[i] = all_highlighted_annotations[i][next_annotation_index[i]];
            }
        }
    }

    var next_annotation;
    if (next_annotations[0] && next_annotations[1]) {
        if ($(next_annotations[0]).offset().top <= $(next_annotations[1]).offset().top) {
            next_annotation = next_annotations[0];
            jump_to_annotation_index[0] = next_annotation_index[0];
            last_highlighted_side = 0;
            if (only_errors && all_highlighted_annotations[1].length > 0) bring_jump_index_to_same_height(next_annotation, 1);
        } else {
            next_annotation = next_annotations[1];
            jump_to_annotation_index[1] = next_annotation_index[1];
            last_highlighted_side = 1;
            if (only_errors && all_highlighted_annotations[0].length > 0) bring_jump_index_to_same_height(next_annotation, 0);
        }
    } else if (next_annotations[0]) {
        next_annotation = next_annotations[0];
        jump_to_annotation_index[0] = next_annotation_index[0];
        last_highlighted_side = 0;
        if (only_errors && all_highlighted_annotations[1].length > 0) bring_jump_index_to_same_height(next_annotation, 1);
    } else if (next_annotations[1]) {
        next_annotation = next_annotations[1];
        jump_to_annotation_index[1] = next_annotation_index[1];
        last_highlighted_side = 1;
        if (only_errors && all_highlighted_annotations[0].length > 0) bring_jump_index_to_same_height(next_annotation, 0);
    } else if (!only_errors) {
        jump_to_annotation_index[last_highlighted_side] = all_highlighted_annotations[last_highlighted_side].length;
    }

    if (next_annotation) {
        scroll_to_annotation(next_annotation);
    }
}

function bring_jump_index_to_same_height(next_annotation, side_index) {
    // Bring the jump index for the other side to the same height
    var original_jump_index = jump_to_annotation_index[side_index];
    if (side_index == 0) {
        while (jump_to_annotation_index[side_index] < 0 || (jump_to_annotation_index[side_index] <= all_highlighted_annotations[side_index].length &&
               $(all_highlighted_annotations[side_index][jump_to_annotation_index[side_index]]).offset().top <= $(next_annotation).offset().top)) {
            jump_to_annotation_index[side_index]++;
        }
    } else {
        while (jump_to_annotation_index[side_index] < 0 || (jump_to_annotation_index[side_index] <= all_highlighted_annotations[side_index].length &&
               $(all_highlighted_annotations[side_index][jump_to_annotation_index[side_index]]).offset().top < $(next_annotation).offset().top)) {
            jump_to_annotation_index[side_index]++;
        }
    }
    jump_to_annotation_index[side_index]--; // Minus one, because the next annotation should be the one determined above
}

function scroll_to_previous_annotation(only_errors) {
    // Get potential next highlighted annotation for left and right side
    var next_annotation_index = [-1, -1];
    var next_annotations = [null, null];
    for (var i=0; i<2; i++) {
        if (all_highlighted_annotations[i].length == 0) continue;
        if (jump_to_annotation_index[i] - 1 >= 0) {
            if (only_errors) {
                next_annotation_index[i] = find_previous_annotation_index(i, last_highlighted_side);
                if (next_annotation_index[i] >= 0) next_annotations[i] = all_highlighted_annotations[i][next_annotation_index[i]];
            } else {
                next_annotation_index[i] = jump_to_annotation_index[i] - (last_highlighted_side==i);
                next_annotations[i] = all_highlighted_annotations[i][next_annotation_index[i]];
            }
        }
    }

    var next_annotation;
    if (next_annotations[0] && next_annotations[1]) {
        if ($(next_annotations[0]).offset().top > $(next_annotations[1]).offset().top) {
            next_annotation = next_annotations[0];
            if (!only_errors || last_highlighted_side == 0) jump_to_annotation_index[last_highlighted_side] = next_annotation_index[last_highlighted_side];
            else {
                update_index_to_previous_annotation(next_annotation, last_highlighted_side);
                jump_to_annotation_index[Math.abs(last_highlighted_side - 1)] = next_annotation_index[Math.abs(last_highlighted_side - 1)];
            }
            last_highlighted_side = 0;
        } else {
            next_annotation = next_annotations[1];
            if (!only_errors || last_highlighted_side == 1) jump_to_annotation_index[last_highlighted_side] = next_annotation_index[last_highlighted_side];
            else {
                update_index_to_previous_annotation(next_annotation, last_highlighted_side);
                jump_to_annotation_index[Math.abs(last_highlighted_side - 1)] = next_annotation_index[Math.abs(last_highlighted_side - 1)];
            }
            last_highlighted_side = 1;
        }
    } else if (next_annotations[0]) {
        next_annotation = next_annotations[0];
        if (!only_errors || last_highlighted_side == 0) jump_to_annotation_index[last_highlighted_side] = next_annotation_index[last_highlighted_side];
        else {
            update_index_to_previous_annotation(next_annotation, last_highlighted_side);
            jump_to_annotation_index[Math.abs(last_highlighted_side - 1)] = next_annotation_index[Math.abs(last_highlighted_side - 1)];
        }
        last_highlighted_side = 0;
    } else if (next_annotations[1]) {
        next_annotation = next_annotations[1];
        if (!only_errors || last_highlighted_side == 1) jump_to_annotation_index[last_highlighted_side] = next_annotation_index[last_highlighted_side];
        else {
            update_index_to_previous_annotation(next_annotation, last_highlighted_side);
            jump_to_annotation_index[Math.abs(last_highlighted_side - 1)] = next_annotation_index[Math.abs(last_highlighted_side - 1)];
        }
        last_highlighted_side = 1;
    } else if (!only_errors) {
        jump_to_annotation_index[0] = -1;
        jump_to_annotation_index[1] = -1;
    }

    if (next_annotation) {
        scroll_to_annotation(next_annotation);
    }
}

function update_index_to_previous_annotation(next_annotation, side_index) {
    // Bring the jump index for the other side to the same height
    var original_jump_index = jump_to_annotation_index[side_index];
    if (side_index == 0) {
        while (jump_to_annotation_index[side_index] == all_highlighted_annotations[side_index].length || (
               jump_to_annotation_index[side_index] >= -1 && $(all_highlighted_annotations[side_index][jump_to_annotation_index[side_index]]).offset().top > $(next_annotation).offset().top)) {
            jump_to_annotation_index[side_index]--;
        }
    } else {
        while (jump_to_annotation_index[side_index] == all_highlighted_annotations[side_index].length || (
               jump_to_annotation_index[side_index] >= -1 && $(all_highlighted_annotations[side_index][jump_to_annotation_index[side_index]]).offset().top >= $(next_annotation).offset().top)) {
            jump_to_annotation_index[side_index]--;
        }
    }
}

function find_next_annotation_index(side_index) {
    for (var i=jump_to_annotation_index[side_index] + 1; i<all_highlighted_annotations[side_index].length; i++) {
        var classes = $(all_highlighted_annotations[side_index][i]).attr("class").split(/\s+/);
        if (classes.includes("fn") || classes.includes("fp")) {
            return i;
        }
    }
    return all_highlighted_annotations[side_index].length;
}

function find_previous_annotation_index(side_index, last_highlighted_side) {
    for (var i=jump_to_annotation_index[side_index] - (last_highlighted_side==side_index); i > 0; i--) {
        var classes = $(all_highlighted_annotations[side_index][i]).attr("class").split(/\s+/);
        if (classes.includes("fn") || classes.includes("fp")) {
            return i;
        }
    }
    return -1;
}

function decrease_index(index) {
    return Math.max(0, index - 1);
}

function increase_index(index, array_length) {
    return Math.min(index + 1, array_length - 1);
}

function reset_annotation_selection() {
    jump_to_annotation_index = [-1, -1];
    last_highlighted_side = 0;
}

function scroll_to_annotation(annotation) {
    /*
    Scroll to the given annotation and mark it as selected for a second.
    */
    var line_height = parseInt($("#prediction_overview td").css('line-height').replace('px',''));
    var header_size = $("#prediction_overview thead")[0].getBoundingClientRect().height;
    $([document.documentElement, document.body]).animate({
        scrollTop: $(annotation).offset().top - header_size - line_height / 2
    }, 200);
    // Get annotation id class such that all spans belonging to one annotation can be marked as selected
    var classes = $(annotation).attr("class").split(/\s+/);
    var annotation_id_class = classes.filter(function(el) {return el.startsWith("annotation_id_"); });
    // Mark spans as selected
    $("." + annotation_id_class).addClass("selected")
    // Unmark spans as selected after timeout
    setTimeout(function() { $("." + annotation_id_class).removeClass("selected"); }, 1000);
}

function read_url_parameters() {
    url_param_filter_string = get_url_parameter_string(get_url_parameter("system_filter"));
    url_param_show_deprecated = get_url_parameter_boolean(get_url_parameter("show_deprecated"));
    url_param_compare = get_url_parameter_boolean(get_url_parameter("compare"));
    url_param_benchmark = get_url_parameter_string(get_url_parameter("benchmark"));
    url_param_article = get_url_parameter_string(get_url_parameter("article"));
    url_param_system = get_url_parameter_array(get_url_parameter("system"), false);
    url_param_emphasis = get_url_parameter_array(get_url_parameter("emphasis"), false);
    url_param_show_columns = get_url_parameter_array(get_url_parameter("show_columns"), false);
    url_param_sort_order = get_url_parameter_array(get_url_parameter("sort_order"), true);
    url_param_access = get_url_parameter_string(get_url_parameter("access"));
}

function get_url_parameter_boolean(url_parameter) {
    return ["true", "1", true].includes(url_parameter);
}

function get_url_parameter_string(url_parameter) {
    /*
    Returns the url_parameter if the url parameter value is a String, otherwise (if
    it is a boolean) returns null.
    */
    if (is_string(url_parameter)) {
        return url_parameter;
    }
    return null;
}

function get_url_parameter_array(url_parameter, integer_array) {
    /*
    Returns the url_parameter as array if the url parameter value is a String, with elements separated by ",".
    Otherwise (if it is a boolean) returns an empty array.
    */
    if (is_string(url_parameter)) {
        array = url_parameter.split(",");
        if (integer_array) array = array.map(function(el) { return parseInt(el) })
        return array;
    }
    return [];
}

function is_string(object) {
    return typeof object === 'string' || object instanceof String;
}

function position_table_tooltip(anchor_el) {
    var tag_name = $(anchor_el).prop("tagName").toLowerCase();
    var anchor_el_rect = anchor_el.getBoundingClientRect();
    $(anchor_el).find(".tooltiptext").each(function() {
        var tooltip_rect = this.getBoundingClientRect();
        var font_size = $(this).css("font-size").replace("px", "");
        if (tag_name =="th") {
            var top = anchor_el_rect.bottom;
        } else {
            var top = anchor_el_rect.top - tooltip_rect.height - (font_size / 2);
        }
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
            // "+" should be decoded as whitespace
            return curr_parameter[1] === undefined ? true : decodeURIComponent((curr_parameter[1]+'').replace(/\+/g, '%20'));
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
    // Show loading GIF
    $("#table_loading").addClass("show");

    // Retrieve file path of .results files in each folder
    benchmarks = [];
    $.get("benchmarks", function(folder_data) {
        $(folder_data).find("a").each(function() {
            file_name = $(this).attr("href");
            if (file_name.endsWith(".benchmark.jsonl")) {
                benchmarks.push(file_name);
            }
        });
    }).then(function() {
        benchmarks.sort();
        for (bi in benchmarks) {
            benchmark = benchmarks[bi];
            var option = document.createElement("option");
            option.text = benchmark.replace(/(.*)\.benchmark\.jsonl/, "$1");
            option.value = benchmark;
            benchmark_select.add(option);
        }

        // Set benchmark
        var benchmark_by_url = $('#benchmark option').filter(function () { return $(this).html() == url_param_benchmark; });
        if (url_param_benchmark && benchmark_by_url.length > 0) {
            // Set the benchmark according to URL parameter if one with a valid benchmark name exists
            $(benchmark_by_url).prop('selected',true);
        } else {
            // Set default value to "wiki-ex".
            $('#benchmark option:contains("wiki-ex")').prop('selected',true);
        }
        show_benchmark_results(true);
    });
}

function reset_selected_cell_categories() {
    /*
    Initialize or reset the selected error categories.
    The array contains one entry for each approach that can be compared.
    */
    selected_cell_categories = new Array(MAX_SELECTED_APPROACHES).fill(null);
}

function show_benchmark_results(initial_call) {
    /*
    Show overview table and set up the article selector for a selected benchmark.
    */
    $("#table_loading").addClass("show");
    $("#evaluation_table_wrapper table").trigger("update");
    benchmark_file = benchmark_select.value;
    benchmark_name = $("#benchmark option:selected").text();

    if (benchmark_file == "") {
        return;
    }

    if (!initial_call) {
        // Update current URL without refreshing the site
        const url = new URL(window.location);
        url.searchParams.set('benchmark', benchmark_name);
        window.history.replaceState({}, '', url);
    }

    // Remove previous evaluation table content
    $("#evaluation_table_wrapper table thead").empty();
    $("#evaluation_table_wrapper table tbody").empty();

    // Remove previous article evaluation content
    $("#prediction_overview").hide();
    evaluation_cases = {};
    articles_data = {};
    var default_selected_systems = [];
    var default_selected_emphasis = [];
    if (initial_call) {
        // If URL parameter is set, select system according to URL parameter
        default_selected_systems = url_param_system;
        default_selected_emphasis = url_param_emphasis;
    } else {
        default_selected_systems = copy(selected_approach_names);
        default_selected_emphasis = selected_cells.map(function(el) {return ($(el).attr('class')) ? $(el).attr('class').split(/\s+/)[1] : null});
    }
    selected_approach_names = [];
    selected_rows = [];
    selected_cells = [];
    reset_selected_cell_categories();

    // Build an overview table over all .results-files from the evaluation-results folder.
    build_overview_table(benchmark_name, default_selected_systems, default_selected_emphasis, initial_call);

    // Read the article and ground truth information from the benchmark.
    parse_benchmark(benchmark_file, initial_call);
}

function filter_table_rows() {
    var filter_keywords = $.trim($("input#result-filter").val()).split(/\s+/);
    $("#evaluation_table_wrapper tbody tr").each(function() {
        var name = $(this).children(":first-child").text();
        // Filter row according to filter keywords
        var show_row = filter_keywords.every(keyword => name.search(keyword) != -1);

        // Filter row according to show-deprecated checkbox
        if (!$("#checkbox_deprecated").is(":checked")) {
            show_row = show_row && !name.includes("deprecated");
        }
        if (show_row) $(this).show(); else $(this).hide();
    });
    // The table width may have changed due to adding or removing the scrollbar
    // therefore change the width of the top scrollbar div accordingly
    set_top_scrollbar_width();
}

function set_top_scrollbar_width() {
    /*
    Set width of the top scrollbar to the current width of the evaluation table + side scrollbar.
    */
    var width = $("#evaluation_table_wrapper table")[0].getBoundingClientRect().width + 20;  // + width of the side scrollbar
    $("#top_scrollbar").css({"width": width + "px"});
}

function parse_benchmark(benchmark_file, initial_call) {
    /*
    Read the articles and ground truth labels from the benchmark.

    Reads the file benchmarks/<benchmark_file> and adds each article to the list 'articles'.
    Each article is an object identical to the parsed JSON-object.

    Calls set_article_select_options(), which sets the options for the article selector element.
    */
    // List of articles with ground truth information from the benchmark.
    articles = [];
    if (benchmark_file.startsWith("aida") && url_param_access != "42") {
        benchmark_file = benchmark_file + ".obscured";
    }
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
            set_article_select_options(initial_call);
        }
    );
}

function set_article_select_options(initial_call) {
    /*
    Set the options for the article selector element to the names of the articles from the list 'articles'.
    */
    // Empty previous options
    $("#article_select").empty();

    reset_annotation_selection();

    // Add default "All articles" option
    var option = document.createElement("option");
    var selected_benchmark = $("#benchmark option:selected").text();
    var option_text_suffix = (["newscrawl", "wiki-ex"].includes(selected_benchmark)) ? " (evaluated span only)" : "";
    option.text = "All " + articles.length + " articles" + option_text_suffix;
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

    // Set the article according to URL parameter if one with a valid article name exists
    var article_by_url = $('#article_select option').filter(function () { return $(this).html() == url_param_article; });
    if (url_param_article && article_by_url.length > 0) {
        $(article_by_url).prop('selected',true);
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

function show_annotated_text(approach_name, textfield, selected_cell_category, column_idx, article_index, example_benchmark) {
    /*
    Generate annotations and tooltips for predicted and groundtruth mentions of the selected approach and article
    and show them in the textfield.
    */
    var benchmark_articles = (example_benchmark) ? articles_example_benchmark : articles;
    if (show_all_articles_flag && !example_benchmark) {
        var annotated_texts = [];
        for (var i=0; i < benchmark_articles.length; i++) {
            var annotations = get_annotations(i, approach_name, column_idx, example_benchmark);
            annotated_texts.push(annotate_text(benchmark_articles[i].text, annotations, benchmark_articles[i].hyperlinks, benchmark_articles[i].evaluation_span, selected_cell_category));
        }
        annotated_text = "";
        for (var i=0; i < annotated_texts.length; i++) {
            if (i != 0) annotated_text += "<hr/>";
            if (benchmark_articles[i].title) annotated_text += "<b>" + benchmark_articles[i].title + "</b><br>";
            annotated_text += annotated_texts[i];
        }
    } else {
        var curr_article = benchmark_articles[article_index];
        var annotations = get_annotations(article_index, approach_name, column_idx, example_benchmark);
        var annotated_text = annotate_text(curr_article.text, annotations, curr_article.hyperlinks, [0, curr_article.text.length], selected_cell_category);
    }
    textfield.html(annotated_text);
}

function get_annotations(article_index, approach_name, column_idx, example_benchmark) {
    /*
    Generate annotations for the predicted entities of the selected approach and article.

    This method first combines the predictions outside the evaluation span (from the file <approach>.jsonl)
    with the evaluated predictions inside the evaluation span (from the file <approach>.cases),
    and then generates annotations for all of them.
    */
    if (example_benchmark) {
        var article_cases = evaluation_cases_example_benchmark[article_index];  // information from the .cases file
        var article_data = articles_data_example_benchmark[article_index];  // information from the .jsonl file
    } else {
        var article_cases = evaluation_cases[approach_name][article_index];  // information from the .cases file
        var article_data = articles_data[approach_name][article_index];  // information from the .jsonl file
    }

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
    if ("entity_mentions" in article_data) {
        for (prediction of article_data.entity_mentions) {
            if (prediction.span[1] < evaluation_begin) {
                mentions.push(prediction);
            }
        }
    }

    // get the cases inside the evaluation span from the cases list
    for (eval_case of article_cases) {
        mentions.push(eval_case);
    }
    // get the mentions after the evaluation span
    if ("entity_mentions" in article_data) {
        for (prediction of article_data.entity_mentions) {
            if (prediction.span[0] >= evaluation_end) {
                mentions.push(prediction);
            }
        }
    }

    // list with tooltip information for each mention
    var annotations = {};
    var prediction_spans = [];
    var annotation_count = 0;
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
                    var benchmark_articles = (example_benchmark) ? articles_example_benchmark : articles;
                    gt_annotation.parent_text = benchmark_articles[article_index].text.substring(parent_span[0], parent_span[1]);
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
            "error_labels": [],
            "beginning": true,
        };
        // If the case has a GT and a prediction, don't add error cases to GT if it's an unknown or optional case
        if (!$.isEmptyObject(gt_annotation) && !$.isEmptyObject(pred_annotation)) {
            if (gt_annotation.class == ANNOTATION_CLASS_OPTIONAL || gt_annotation.class == ANNOTATION_CLASS_UNKNOWN) {
                pred_annotation.error_labels = mention.error_labels;
            } else {
                gt_annotation.error_labels = mention.error_labels;
                pred_annotation.error_labels = mention.error_labels;
            }
            gt_annotation.id = column_idx + "_" + article_index+ "_" + annotation_count;
            annotation_count++;
            pred_annotation.id = column_idx + "_" + article_index+ "_" + annotation_count;
            annotation_count++;
        } else {
            annotation.error_labels = mention.error_labels;
            annotation.id = column_idx + "_" + article_index+ "_" + annotation_count;
            annotation_count++;
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

function annotate_text(text, annotations, hyperlinks, evaluation_span, selected_cell_category) {
    /*
    Generate tooltips for the given annotations and html hyperlinks for the given hyperlinks.
    Tooltips and hyperlinks can overlap.

    Arguments:
    - text: The original text without tooltips or hyperlinks.
    - annotations: A sorted (by span) list of objects containing tooltip information
    - hyperlinks: A sorted (by span) list of tuples (span, target_article)
    - evaluation_span: The span of the article that can be evaluated
    - selected_cell_categories: categories of the selected cell for the corresponding approach

    First the overlapping annotations and hyperlinks get combined to combined_annotations.
    Second, the annotations with hyperlinks are added to the text and a tooltip is generated for each annotation.
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
    var new_hyperlinks = [];
    if (hyperlinks) {
        for (link of hyperlinks) { new_hyperlinks.push([copy(link[0]), {"span": link[0], "hyperlink": link[1]}]); }
    }

    // STEP 1: Combine overlapping annotations and hyperlinks.
    // Consumes the first element from the link list or annotation list, or a part from both if they overlap.
    var combined_annotations = combine_overlapping_annotations(only_groundtruth_annotations, non_groundtruth_annotations);
    // Links must be the last list that is added such that they can only be the inner most annotations, because <div>
    // tags are not allowed within <a> tags, but the other way round is valid.
    combined_annotations = combine_overlapping_annotations(combined_annotations, new_hyperlinks);

    // Text should only be the text within the given evaluation span (Careful: This is the entire article if a
    // single article is supposed to be shown and the article evaluation span if all articles are supposed to be
    // shown)
    text = text.substring(0, evaluation_span[1]);

    // STEP 2: Add the combined annotations and hyperlinks to the text.
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
    and can be identified by the property "hyperlink". Inner annotations, e.g. hyperlinks contained in
    a mention annotation, nested mention annotations are contained given by the property "inner_annotation".
    */
    var inner_annotation = snippet;

    if ("inner_annotation" in annotation) {
        inner_annotation = generate_annotation_html(snippet, annotation.inner_annotation, selected_cell_category, annotation.parent_text);
    }

    if ("hyperlink" in annotation) {
        return "<a href=\"https://en.wikipedia.org/wiki/" + annotation.hyperlink + "\" target=\"_blank\">" + inner_annotation + "</a>";
    }

    // Add tooltip
    var tooltip_classes = "tooltiptext";
    var tooltip_header_text = "";
    var tooltip_case_type_html = "";
    var tooltip_body_text = "";
    var tooltip_footer_html = "";
    if (annotation.class == ANNOTATION_CLASS_TP && annotation.pred_entity_id) {
        wikidata_url = "https://www.wikidata.org/wiki/" + annotation.pred_entity_id;
        entity_link = "<a href=\"" + wikidata_url + "\" target=\"_blank\">" + annotation.pred_entity_id + "</a>";
        if (annotation.pred_entity_name != null) {
            var entity_name = (["Unknown", "null"].includes(annotation.pred_entity_name)) ? MISSING_LABEL_TEXT : annotation.pred_entity_name;
            entity_name = entity_name + " (" + entity_link + ")";
        } else {
            entity_name = entity_link;
        }
        tooltip_header_text += entity_name;
    } else if (annotation.class == ANNOTATION_CLASS_TP && annotation.gt_entity_id) {
        tooltip_classes += " below";
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
            if (annotation.class == ANNOTATION_CLASS_OPTIONAL) tooltip_body_text += "Note: Detection is optional<br>";
            if (annotation.class == ANNOTATION_CLASS_UNKNOWN) tooltip_body_text += "Note: Entity not found in the knowledge base<br>";
            if (![ANNOTATION_CLASS_OPTIONAL, ANNOTATION_CLASS_UNKNOWN].includes(annotation.class) && annotation.gt_entity_type) {
                var type_string = $.map(annotation.gt_entity_type.split("|"), function(qid){ return get_type_label(qid) }).join(", ");
                tooltip_body_text += "Types: " + type_string + "<br>";
            }
            tooltip_classes += " below";
        }
    }
    // Add case type boxes and annotation case type class to tooltip
    if ([ANNOTATION_CLASS_TP, ANNOTATION_CLASS_FN, ANNOTATION_CLASS_FP].includes(annotation.class)) {
        if (tooltip_header_text) {
            tooltip_case_type_html += "<div class=\"case_type_box " + annotation.class + "\">" + annotation.class.toUpperCase() + "</div>";
        }
        tooltip_classes += " " + annotation.class;
    }
    if (annotation.predicted_by) tooltip_body_text += "Predicted by " + annotation.predicted_by + "<br>";
    if (annotation.pred_entity_type) {
        var type_string = $.map(annotation.pred_entity_type.split("|"), function(qid){ return get_type_label(qid) }).join(", ");
        tooltip_body_text += "Types: " + type_string + "<br>";
    }
    if (annotation.parent_text) tooltip_body_text += "Alternative span: \"" + annotation.parent_text + "\"<br>";
    // Add error category tags
    // Only show error category tags for once in the FP tooltip, i.e. don't double them in the GT tooltip for TP
    // and for disambiguation errors
    var correct_ner = (annotation.inner_annotation && annotation.inner_annotation.pred_entity_id && annotation.inner_annotation.span[0] == annotation.span[0] && annotation.inner_annotation.span[1] == annotation.span[1]);
    if (annotation.error_labels && annotation.error_labels.length > 0 && !correct_ner) {
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
                if ((annotation.error_labels && annotation.error_labels.includes(selected_category)) || annotation.mention_type == selected_category) {
                    lowlight_mention = false;
                    break;
                }
            }
        }
    }
    var lowlight = (lowlight_mention) ? " lowlight" : "";

    var annotation_kind = (annotation.gt_entity_id) ? "gt" : "pred";
    var beginning = (annotation.beginning) ? " beginning" : "";
    var annotation_id_class = " annotation_id_" + annotation.id;
    var replacement = "<span class=\"annotation " + annotation_kind + " " + annotation.class + lowlight + beginning + annotation_id_class + "\">";
    replacement += inner_annotation;
    if (tooltip_header_text || tooltip_body_text) {
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
                combined_annotations.push([[list2_item_span[0], list2_item_end], copy(list2_item[1])]);
                if (list2_item_end == list2_item_span[1]) {
                    list2.shift();
                } else {
                    list2[0][0][0] = list2_item_end;
                    list2_item[1].beginning = false;
                }
            } else if (list1_item_span[0] < list2_item_span[0]) {
                // Add element from first list
                var list1_item_end = Math.min(list1_item_span[1], list2_item_span[0]);
                combined_annotations.push([[list1_item_span[0], list1_item_end], copy(list1_item[1])]);
                if (list1_item_end == list1_item_span[1]) {
                    list1.shift();
                } else {
                    list1_item_span[0] = list1_item_end;
                    list1_item[1].beginning = false;
                }
            } else {
                // Add both
                var list1_item_ann = copy(list1_item[1]);
                var most_inner_ann = list1_item_ann;
                // Add element from second list as inner-most annotation of element from first list
                while ("inner_annotation" in most_inner_ann) {
                    most_inner_ann = most_inner_ann["inner_annotation"];
                }
                most_inner_ann["inner_annotation"] = copy(list2_item[1]);
                var list1_item_end = Math.min(list1_item_span[1], list2_item_span[1]);
                combined_annotations.push([[list1_item_span[0], list1_item_end], list1_item_ann]);
                if (list1_item_end == list2_item_span[1]) {
                    list2.shift();
                } else {
                    list2[0][0][0] = list1_item_end;
                    list2_item[1].beginning = false;
                }
                if (list1_item_end == list1_item_span[1]) {
                    list1.shift();
                } else {
                    list1[0][0][0] = list1_item_end;
                    list1_item[1].beginning = false;
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
    show_annotated_text(selected_approaches[0], $(columns[column_idx]), selected_cell_categories[0], column_idx, selected_article_index, false);
    var benchmark_name = $("#benchmark option:selected").text();
    var emphasis_str = get_emphasis_string(selected_cell_categories[0])
    $(column_headers[column_idx]).html(selected_approaches[0] + "<span class='nonbold'> on " + benchmark_name + emphasis_str + "</span>");
    show_table_column("prediction_overview", column_idx);
    column_idx++;
    if(is_compare_checked() && selected_approaches.length > 1) {
        // Show second prediction column
        show_annotated_text(selected_approaches[1], $(columns[column_idx]), selected_cell_categories[1], column_idx, selected_article_index, false);
        emphasis_str = get_emphasis_string(selected_cell_categories[1])
        $(column_headers[column_idx]).html(selected_approaches[1] + "<span class='nonbold'> on " + benchmark_name + emphasis_str + "</span>");
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

function get_emphasis_string(selected_cell_category) {
    /*
    Create an emphasis string for the given selected category.
    */
    var emphasis = "all";
    var emphasis_type = "mention type";
    var mention_types = $.map( mention_type_headers, function(key){ return mention_type_headers[key]; });
    if (selected_cell_category) {
        var emphasis_strs = [];
        for (selected_category of selected_cell_category) {
            if (is_type_string(selected_category)) {
                 emphasis_strs.push(type_name_mapping[selected_category]);
                 emphasis_type = "entity type";
            } else if (mention_types.includes(selected_category)) {
                emphasis_strs.push(selected_category.replace(/_/g, " ").toLowerCase());
            } else {
                emphasis_strs.push(selected_category.replace(/_/g, " ").toLowerCase());
                emphasis_type = "error category";
            }
        }
        emphasis = emphasis_strs.join(", ");
    }
    return " (emphasis: " + emphasis_type + " \"" + emphasis + "\")";
}

function build_overview_table(benchmark_name, default_selected_systems, default_selected_emphasis, initial_call) {
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
                    // file extension.
                    var benchmark = file_name.split(".").slice(-2)[0];
                    if (file_name.endsWith(RESULTS_EXTENSION) && benchmark == benchmark_name) {
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
                result_array.sort();
                // Add table header and checkboxes
                result_array.forEach(function(result_tuple) {
                    var approach_name = result_tuple[0];
                    var results = result_tuple[1];
                    if (!$('#evaluation_table_wrapper table thead').html()) {
                        // Add table header if it has not yet been added
                        var table_header = get_table_header(results, "evaluation");
                        $('#evaluation_table_wrapper table thead').html(table_header);
                    }

                    if (!$('#evaluation_overview .checkboxes').html()) {
                        // Add checkboxes if they have not yet been added
                        add_checkboxes(results, initial_call);
                    }
                    return;
                });
                // Add table body
                build_evaluation_table_body(result_array);

                // Select default rows and cells
                if (default_selected_systems) {
                    for (var i=0; i<default_selected_systems.length; i++) {
                        var system = default_selected_systems[i];
                        var row = $('#evaluation_table_wrapper table tbody tr').filter(function(){ return $(this).children(":first-child").text() === system;});
                        if (row.length > 0) {
                            if (i < default_selected_emphasis.length && default_selected_emphasis[i]) {
                                var cell = $(row).children("." + default_selected_emphasis[i]);
                                if (cell.length > 0) {
                                    on_cell_click(cell[0]);
                                } else {
                                    on_cell_click($(row).children(":first-child")[0]);
                                }
                            } else {
                                on_cell_click($(row).children(":first-child")[0]);
                            }
                            on_row_click(row[0]);
                        }
                    }
                }

                // Update the tablesorter. The sort order is automatically adapted from the previous table.
                $("#evaluation_table_wrapper table").trigger("updateAll")

                // Remove the table loading GIF
                $("#table_loading").removeClass("show");

                if (initial_call && url_param_sort_order.length > 0) {
                    // Use sort order from URL parameter
                    $.tablesorter.sortOn( $("#evaluation_table_wrapper table")[0].config, [ url_param_sort_order ]);
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
            $('#evaluation_table_wrapper table tbody').append(row);
        }
    });

    // Show / Hide columns according to checkbox state
    $("input[class^='checkbox_']").each(function() {
        show_hide_columns(this, false);
    })

    // Show / Hide rows according to filter-result input field
    filter_table_rows();
}

function add_checkboxes(json_obj, initial_call) {
    /*
    Add checkboxes for showing / hiding columns.
    */
    $.each(json_obj, function(key) {
        if (key == "by_type" || key == "errors") {
            $.each(json_obj[key], function(subkey) {
                var class_name = get_class_name(subkey);
                var title = get_title_from_key(subkey);
                var checked = (url_param_show_columns.includes(class_name)) ? "checked" : ""
                var checkbox_html = "<span><input type=\"checkbox\" class=\"checkbox_" + class_name + "\" onchange=\"on_column_checkbox_change(this, true)\" " + checked + ">";
                checkbox_html += "<label>" + title + "</label></span>\n";
                var checkbox_div_id = (key == "errors") ? "error_checkboxes" : "type_checkboxes";
                $("#" + checkbox_div_id + ".checkboxes").append(checkbox_html);
                if (key == "by_type") type_name_mapping[get_type_qid(subkey).toLowerCase()] = title;
            });
        } else {
            var class_name = get_class_name(key);
            var title = get_title_from_key(key);
            var checked = ((class_name == "all" && url_param_show_columns.length == 0) || url_param_show_columns.includes(class_name)) ? "checked" : ""
            var checkbox_html = "<span><input type=\"checkbox\" class=\"checkbox_" + class_name + "\" onchange=\"on_column_checkbox_change(this, true)\" " + checked + ">";
            checkbox_html += "<label>" + title + "</label></span>\n";
            $("#general_checkboxes.checkboxes").append(checkbox_html);
        }
    });
}

function on_column_checkbox_change(element, resize) {
    show_hide_columns(element, resize);

    // Update current URL without refreshing the site
    var checkbox_classes = [];
    var checkboxes = $("#evaluation_overview .checkboxes input:checked").each(function() {
        checkbox_classes.push($(this).attr("class").split(/\s+/)[0].replace("checkbox_", ""));
    });
    const url = new URL(window.location);
    url.searchParams.set('show_columns', checkbox_classes.join(","));
    window.history.replaceState({}, '', url);
}

function show_hide_columns(element, resize) {
    /*
    This function should be called when the state of a checkbox is changed.
    This can't be simply added in on document ready, because checkboxes are added dynamically.
    */
    var col_class = $(element).attr("class");
    col_class = col_class.substring(col_class.indexOf("_") + 1, col_class.length);
    var column = $("#evaluation_table_wrapper table ." + col_class);
    if($(element).is(":checked")) {
        column.show();
    } else {
        column.hide();
    }

    if (resize) {
        // Resizing takes a long time especially on Chrome, therefore do it only when necessary.
        // The table width has changed therefore change the width of the top scrollbar div accordingly.
        set_top_scrollbar_width();
    }
}

function get_table_header(json_obj) {
    /*
    Get html for the table header.
    */
    var first_row = "<tr><th onclick='produce_latex()' class='produce_latex'>" + copy_latex_text + "</th>";
    var second_row = "<tr><th>System</th>";
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
            var sort_order = (key in error_category_mapping) ? " data-sortinitialorder=\"asc\"" : "";
            second_row_addition += "<th class='" + class_name + " " + class_name + "-" + subclass_name + " tooltip sorter-digit'" + sort_order + ">" + get_title_from_key(subkey);
            var tooltip_text = get_header_tooltip_text(key, subkey);
            if (tooltip_text) second_row_addition += "<span class='tooltiptext'>" + tooltip_text + "</span>";
            second_row_addition += "</th>";
            colspan += 1;
        }
    });
    first_row_addition += "<th colspan=\"" + colspan + "\" class='" + class_name + " tooltip'>" + get_title_from_key(key);
    var tooltip_text = get_header_tooltip_text(key, null);
    if (tooltip_text) {
        first_row_addition += "<span class='tooltiptext'>" + tooltip_text + "</span>";
    }
    first_row_addition += "</th>";
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
                Math.round(json_obj[key][subkey] * 100) / 100;
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
            var tooltip_text = header_descriptions[key][subkey];
            if (subkey != "all") {
                tooltip_text += tooltip_example_html;
            }
            return tooltip_text;
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
            $("#evaluation_table_wrapper").html("ERROR: no file with cases found.");
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

    // Update current URL without refreshing the site
    const url = new URL(window.location);
    url.searchParams.set('system', selected_approach_names.join(","));
    window.history.replaceState({}, '', url);

    read_evaluation(approach_name, selected_approaches, timestamp);
}

function on_cell_click(el) {
    /*
    Highlight error category / type cells on click and un-highlight previously clicked cell.
    Add or remove error categories and types to/from current selection.
    */
    reset_annotation_selection();

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
    var classes = ($(el).attr('class')) ? $(el).attr('class').split(/\s+/) : [];  // System column has no class attribute
    if (is_error_cell(el)) {
        $(el).addClass("selected");
        selected_cells.push(el);
    } else if (classes.length > 0 && (classes[0] in mention_type_headers || is_type_string(classes[0]))) {
        $(el).closest('tr').find('.' + classes[0]).each(function() {
            $(this).addClass("selected");
        });
        selected_cells.push(el);
    } else {
        // Select "all" column
        var added = false;
        $(el).closest('tr').find('.all').each(function() {
            $(this).addClass("selected");
            if (!added) {
                // Add a single cell from the "all" column. Which one does not matter.
                selected_cells.push(this);
                added = true;
            }
        });
    }

    // Updated selected cell categories
    // Note that selected_rows is updated in on_row_click(), i.e. after on_cell_click() is called so no -1 necessary.
    approach_index = (already_selected_row_clicked >= 0 || !is_compare_checked()) ? 0 : selected_rows.length % MAX_SELECTED_APPROACHES;
    selected_cell_categories[approach_index] = get_error_category_or_type(el);

    // Update current URL without refreshing the site
    const url = new URL(window.location);
    url.searchParams.set('emphasis', selected_cells.map(function(el) {return ($(el).attr('class')) ? $(el).attr('class').split(/\s+/)[1] : []}).join(","));
    window.history.replaceState({}, '', url);
}

function deselect_all_table_rows() {
    /*
    Deselect all rows in all evaluation tables
    */
    $("#evaluation_table_wrapper tbody tr").each(function() {
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
            return [get_type_qid(classes[0])];
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

function get_type_qid(string) {
    return string.replace(/([Qq][0-9]+).*/, "$1");
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
            selected_cell_categories = [selected_cell_categories[1], null];
            if (deselected_cell) remove_selected_classes(deselected_cell);
        }

        hide_table_column("prediction_overview", 1);

        show_article(selected_approach_names, timestamp);
    }
    // Update current URL without refreshing the site
    const url = new URL(window.location);
    url.searchParams.set('compare', $("#checkbox_compare").is(":checked"));
    url.searchParams.set('system', selected_approach_names.join(","));
    url.searchParams.set('emphasis', selected_cells.map(function(el) {return ($(el).attr('class')) ? $(el).attr('class').split(/\s+/)[1] : []}).join(","));
    window.history.replaceState({}, '', url);
}

function is_compare_checked() {
    return $("#checkbox_compare").is(":checked");
}

function toggle_show_deprecated() {
    filter_table_rows();

    // Update current URL without refreshing the site
    const url = new URL(window.location);
    url.searchParams.set('show_deprecated', $("#checkbox_deprecated").is(":checked"));
    window.history.replaceState({}, '', url);
}

function on_article_select() {
    var timestamp = new Date().getTime();
    last_show_article_request_timestamp = timestamp;
    show_article(selected_approach_names, timestamp);

    // Update current URL without refreshing the site
    const url = new URL(window.location);
    url.searchParams.set('article', $("#article_select option:selected").text());
    window.history.replaceState({}, '', url);
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
    $('#evaluation_table_wrapper table thead tr').each(function(){
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
    $("#evaluation_table_wrapper table tbody tr").each(function() {
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
    $("#evaluation_overview .latex").show();
    $("#evaluation_overview .latex textarea").val(latex_text);
    $("#evaluation_overview .latex textarea").show();  // Text is not selected or copied if it is hidden
    $("#evaluation_overview .latex textarea").select();
    document.execCommand("copy");
    $("#evaluation_overview .latex textarea").hide();

    // Show the notification for the specified number of seconds
    var show_duration_seconds = 5;
    setTimeout(function() { $("#evaluation_overview .latex").hide(); }, show_duration_seconds * 1000);
}

