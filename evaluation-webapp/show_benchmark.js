// Immutable global variables ------------------------------------------------------------------------------------------
window.CONFIG_PATH = "config.json";

window.EXAMPLE_BENCHMARK_PATH = "example-benchmark/error-category-examples.benchmark.jsonl";
window.EXAMPLE_BENCHMARK_EVAL_CASES_PATH = "example-benchmark/example.error-category-examples.eval_cases.jsonl";

window.BENCHMARK_EXTENSION = ".benchmark.jsonl"
window.RESULTS_EXTENSION = ".eval_results.json";
window.METADATA_EXTENSION = ".metadata.json";
window.EVALUATION_RESULT_PATH = "evaluation-results";

window.MAX_SELECTED_APPROACHES = 2;
window.MAX_CACHED_FILES = 15;

window.ANNOTATION_CLASS_TP = "tp";
window.ANNOTATION_CLASS_FP = "fp";
window.ANNOTATION_CLASS_FN = "fn";
window.ANNOTATION_CLASS_UNKNOWN = "unknown";
window.ANNOTATION_CLASS_OPTIONAL = "optional";
window.ANNOTATION_CLASS_UNEVALUATED = "unevaluated";

window.MISSING_LABEL_TEXT = "[MISSING LABEL]";
window.NIL_PREDICTION_TEXT = "[NIL]";
window.NO_LABEL_ENTITY_IDS = ["QUANTITY", "DATETIME", "Unknown"];

window.IGNORE_HEADERS = ["true_positives", "false_positives", "false_negatives", "ground_truth"];
window.PERCENTAGE_HEADERS = ["precision", "recall", "f1"];
window.COPY_TABLE_CELL_TEXT = "Copy table";

window.TABLE_FORMAT_LATEX = "LATEX";
window.TABLE_FORMAT_TSV = "TSV";

window.TOOLTIP_EXAMPLE_HTML = "<p><a href=\"#example_benchmark_modal\" onclick=\"show_example_benchmark_modal(this)\" data-toggle=\"modal\" data-target=\"#example_benchmark_modal\">For an example click here</a>.</p>";
window.HEADER_DESCRIPTIONS = {
    "undetected": {
        "": "Errors involving undetected mentions.",
        "all": "<p><i>Numerator:</i> A ground truth mention span is not linked to an entity.</p><p><i>Denominator:</i> All ground truth entity mentions.</p>",
        "lowercased": "<p><i>Numerator:</i> Undetected lowercased ground truth mention.</p><p><i>Denominator:</i> All lowercased ground truth mentions.</p>",
        "partially_included": "<p><i>Numerator:</i> A part of the ground truth mention is linked to an entity.</p><p><i>Denominator:</i> All ground truth mentions consisting of multiple words.</p>",
        "partial_overlap": "<p><i>Numerator:</i> Undetected mention that overlaps with a predicted mention.</p><p><i>Denominator:</i> All ground truth mentions that are not lowercased.</p>",
        "other": "<p><i>Numerator:</i> Undetected mention that does not fall into any of the other categories.</p><p><i>Denominator:</i> All ground truth mentions that are not lowercased.</p>"
    },
    "false_detection": {
        "": "Errors involving false detections.",
        "all": "A mention is predicted whose span is not linked in the ground truth.",
        "lowercased": "The predicted mention is lowercased and does not overlap with a ground truth mention.",
        "groundtruth_unknown": "The predicted mention is uppercased and the ground truth is an unknown entity.",
        "other": "NER false positive that does not fall into any of the other categories.",
        "wrong_span": "<p><i>Numerator:</i> The predicted mention overlaps with a ground truth mention of the same entity, but the spans do not match exactly.</p><p><i>Denominator</i>: All predicted mentions.</p>"
    },
    "wrong_disambiguation": {
        "": "NER true positives where a wrong entity was linked.",
        "all": "<p><i>Numerator:</i> A ground truth span was detected, but linked to the wrong entity.</p><p><i>Denominator:</i> All NER true positives.</p>",
        "demonym": "<p><i>Numerator:</i> FP & FN and the mention text is a demonym, i.e. it is contained in a list of demonyms from Wikidata.</p><p><i>Denominator:</i> NER true positives where the mention text is a demonym.</p>",
        "metonymy": "<p><i>Numerator:</i> FP & FN and the most popular entity for the given mention text and the prediction are locations, the ground truth is not a location.</p><p><i>Denominator:</i> NER true positives where the most popular candidate is a location but the ground truth is not.</p>",
        "partial_name": "<p><i>Numerator:</i> FP & FN and the mention text is a part of the ground truth entity name.</p><p><i>Denominator:</i> NER true positives that are a part of the ground truth entity name.</p>",
        "rare": "<p><i>Numerator:</i> FP & FN and the most popular entity for the given mention text was predicted instead of the less popular ground truth entity.</p><p><i>Denominator:</i> NER true positives where the most popular candidate is not the correct entity.</p>",
        "other": "Disambiguation error that does not fall into any of the other categories.",
        "wrong_candidates": "<p><i>Numerator:</i> FP & FN and the ground truth entity is not in the candidate set returned by the linker for the mention.</p><p><i>Denominator:</i> All NER true positives.</p>",
        "multiple_candidates": "<p><i>Numerator:</i> FP & FN and the candidate set for the mention contains multiple candidate entities, one of which is the ground truth entity, and the linker chose a wrong entity.</p><p><i>Denominator:</i> NER true positives where the linker returned a candidate set with more than one entity and the ground truth is contained in the candidate set.</p>"
    },
    "other_errors": {
        "": "Errors that are not clearly distinguishable as NER false negatives, NER false positives or disambiguation errors.",
        "hyperlink": "<p><i>Numerator:</i> Undetected mention that is also a hyperlink.</p><p><i>Denominator:</i> All ground truth mentions that are hyperlinks.</p>"
    },
    "wrong_coreference": {
        "": "Coreference errors.",
        "false_detection": "NER FP with a mention text in {It, it, This, this, That, that, Its, its}",
        "reference_wrongly_disambiguated": "<p><i>Numerator:</i> Coreference FN & FP and the reference was wrongly disambiguated.</p><p><i>Denominator:</i> Coreference mentions where the correct ground truth mention was referenced.</p>",
        "wrong_mention_referenced": "<p><i>Numerator:</i> Coreference FN + FP and the wrong mention was referenced.</p><p><i>Denominator:</i> Coreference NER true positives.</p>",
        "undetected": "<p><i>Numerator:</i> Coreference FN and the mention was not linked.</p><p><i>Denominator:</i> Ground truth coreference mentions.</p>"
    },
    "ner": {
        "": "Named Entity Recognition results.",
        "tp": "<i>TP</i>: Predictions with a matching ground truth span.",
        "fp": "<i>FP</i>: Predictions with no matching ground truth span.",
        "fn": "<i>FN</i>: Ground truth spans with no matching prediction span."
    },
    "all": {
        "": "Overall entity linking and coreference results.",
        "tp": "<i>TP</i>: Predictions where the mention span and entity match a groundtruth mention span and entity.",
        "fp": "<i>FP</i>: Predictions where the mention either does not match a groundtruth mention span or the predicted entity does not match the groundtruth entity.",
        "fn": "<i>FN</i>: Groundtruth where the mention either does not match a predicted mention span or the predicted entity does not match the groundtruth entity."
    },
    "entity": {
        "": "Entity linking results.",
        "tp": "<i>TP</i>: True positive entities (excluding coreferences).",
        "fp": "<i>FP</i>: False positive entities (excluding coreferences).",
        "fn": "<i>FN</i>: False negative entities (excluding coreferences)."
    },
    "entity_named": {
        "": "Entity linking results for named entities, i.e. entities where the first alphabetic character is an uppercase letter.",
        "tp": "<i>TP</i>: True positive named entities.",
        "fp": "<i>FP</i>: False positive named entities.",
        "fn": "<i>FN</i>: False negative named entities."
    },
    "entity_other": {
        "": "Entity linking results for non-named entities, i.e. entities where the first alphabetic character is a lowercase letter.",
        "tp": "<i>TP</i>: True positive non-named (i.e. lowercase) entities.",
        "fp": "<i>FP</i>: False positive non-named (i.e. lowercase) entities.",
        "fn": "<i>FN</i>: False negative non-named (i.e. lowercase) entities."
    },
    "coref": {
        "": "Coreference results.",
        "tp": "<i>TP</i>: True positive coreferences.",
        "fp": "<i>FP</i>: False positive coreferences.",
        "fn": "<i>FN</i>: False negative coreferences."
    },
    "coref_pronominal": {
        "": "Results for pronominal coreference, i.e. the mention text is a pronoun.",
        "tp": "<i>TP</i>: True positive pronominal coreferences (mention text is a pronoun).",
        "fp": "<i>FP</i>: False positive pronominal coreferences (mention text is a pronoun).",
        "fn": "<i>FN</i>: False negative pronominal coreferences (mention text is a pronoun)."
    },
    "coref_nominal": {
        "": "Results for nominal coreference, i.e. the mention text is \"the &lttype&gt\".",
        "tp": "<i>TP</i>: True positive nominal coreferences (mention text is \"the &lttype&gt\").",
        "fp": "<i>FP</i>: False positive nominal coreferences (mention text is \"the &lttype&gt\").",
        "fn": "<i>FN</i>: False negative nominal coreferences (mention text is \"the &lttype&gt\")."
    },
    "evaluation_mode": {
        "ignored": "Unknown ground truth entities and unknown predicted entities are completely ignored. This is equivalent to GERBIL's \"inKB\" mode.",
        "required": "Unknown ground truth entities must be linked to NIL (or an unknown entity). This is equivalent to GERBIL's \"normal\" mode."
    },
    "precision": "<i>Precision = TP / (TP + FP)</i>",
    "recall": "<i>Recall = TP / (TP + FN)</i>",
    "f1": "<i>F1 = 2 * (P * R) / (P + R)</i>",
};

window.ERROR_CATEGORY_MAPPING = {
    "undetected": {
        "all": ["UNDETECTED"],
        "lowercased": ["UNDETECTED_LOWERCASED"],
        "partially_included": ["UNDETECTED_PARTIALLY_INCLUDED"],
        "partial_overlap": ["UNDETECTED_PARTIAL_OVERLAP"],
        "other": ["UNDETECTED_OTHER"]
    },
    "wrong_disambiguation": {
        "all": ["DISAMBIGUATION_WRONG"],
        "demonym": ["DISAMBIGUATION_DEMONYM_WRONG"],
        "partial_name": ["DISAMBIGUATION_PARTIAL_NAME_WRONG"],
        "metonymy": ["DISAMBIGUATION_METONYMY_WRONG"],
        "rare": ["DISAMBIGUATION_RARE_WRONG"],
        "other": ["DISAMBIGUATION_WRONG_OTHER"],
        "wrong_candidates": ["DISAMBIGUATION_WRONG_CANDIDATES"],
        "multiple_candidates": ["DISAMBIGUATION_MULTI_CANDIDATES_WRONG"]
    },
    "false_detection": {
        "all": ["FALSE_DETECTION"],
        "lowercased": ["FALSE_DETECTION_LOWERCASED"],
        "groundtruth_unknown": ["FALSE_DETECTION_GROUNDTRUTH_UNKNOWN"],
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

window.MENTION_TYPE_HEADERS = {"entity": ["entity_named", "entity_other"],
                        "coref": ["nominal", "pronominal"],
                        "entity_named": ["entity_named"],
                        "entity_other": ["entity_other"],
                        "coref_nominal": ["coref_nominal"],
                        "coref_pronominal": ["coref_pronominal"]};

window.EVALUATION_MODE_LABELS = {
    "ignored": "Unknown entities are ignored",
    "required": "Unknown entities are considered"
}

window.EVALUATION_CATEGORY_TITLES = {
    "mention_types": {
        "all": {"checkbox_label": "All", "table_heading": "All"},
        "entity": {"checkbox_label": "Entity: All", "table_heading": "Entity: All"},
        "entity_named": {"checkbox_label": "Entity: Named", "table_heading": "Entity: Named"},
        "entity_other": {"checkbox_label": "Entity: Other", "table_heading": "Entity: Other"},
        "coref": {"checkbox_label": "Coref: All", "table_heading": "Coref: All"},
        "coref_pronominal": {"checkbox_label": "Coref: Pronominal", "table_heading": "Coref: Pronominal"},
        "coref_nominal": {"checkbox_label": "Coref: Nominal", "table_heading": "Coref: Nominal"},
    },
    "error_categories": {
        "NER": {"checkbox_label": "NER: All", "table_heading": "NER: All"},
        "undetected": {"checkbox_label": "NER: False Negatives", "table_heading": "NER: False Negatives"},
        "false_detection": {"checkbox_label": "NER: False Positives", "table_heading": "NER: False Positives"},
        "wrong_disambiguation": {"checkbox_label": "Disambiguation Errors", "table_heading": "Disambiguation Errors"},
        "other_errors": {"checkbox_label": "Other Errors", "table_heading": "Other Errors"},
        "wrong_coreference": {"checkbox_label": "Coreference Errors", "table_heading": "Coreference Errors"},
    }
}

// Mutable global variables --------------------------------------------------------------------------------------------
window.config = {};
window.whitelist_types = {};

window.evaluation_result_files = {};
window.evaluation_results = [];

window.benchmark_filenames = []
window.benchmark_articles = {};
window.benchmarks_metadata = {};

window.evaluation_cases = {};
window.articles_data = {};
window.experiments_metadata = {};

window.articles_example_benchmark = [];
window.evaluation_cases_example_benchmark = [];

window.is_show_all_articles = false;
window.last_show_article_request_timestamp = 0;

window.selected_experiment_ids = [];
window.selected_rows = [];
window.selected_cells = [];
window.selected_cell_categories = null;

window.all_highlighted_annotations = [[], []];
window.jump_to_annotation_index = [-1, -1];
window.last_highlighted_side = 0;

window.url_param_experiment_filter = null;
window.url_param_benchmark_filter = null;
window.url_param_show_deprecated = null;
window.url_param_compare = null;
window.url_param_article = null;
window.url_param_experiment = null;
window.url_param_emphasis = null;
window.url_param_show_columns = null;
window.url_param_sort_order = null;
window.url_param_access = null;
window.url_param_evaluation_mode = null;
window.url_param_group_by = null;

$("document").ready(function() {
    // JQuery selector variables
    const $experiment_filter = $("input#experiment-filter");
    const $benchmark_filter = $("input#benchmark-filter");
    const $evaluation_table_wrapper = $("#evaluation_table_wrapper");
    const $evaluation_table = $("#evaluation_table_wrapper table");

    read_url_parameters();
    reset_selected_cell_categories();

    // Initialize tippy tooltips contained in the html file
    tippy('[data-tippy-content]', {
        appendTo: document.body,
        theme: 'light-border'
    });

    if (window.url_param_group_by) $("input:radio[name=" + window.url_param_group_by + "]").prop("checked", true);

    $("#checkbox_compare").prop('checked', window.url_param_compare);

    // Read the necessary data files (config, whitelist types, benchmark articles, evaluation results)
    // and build the evaluation results table.
    $("#table_loading").addClass("show");
    read_initial_data().then(function() {
        build_evaluation_results_table(true);
    });

    // Filter table rows by regex in input field (from SPARQL AC evaluation) on key up
    $experiment_filter.keyup(function() {
        filter_table_rows();

        // Update current URL without refreshing the site
        const url = new URL(window.location);
        url.searchParams.set('experiment_filter', $experiment_filter.val());
        window.history.replaceState({}, '', url);
    });

    // Filter results by regex in input field #result-regex on key up
    $benchmark_filter.keyup(function() {
        filter_table_rows();

        // Update current URL without refreshing the site
        const url = new URL(window.location);
        url.searchParams.set('benchmark_filter', $benchmark_filter.val());
        window.history.replaceState({}, '', url);
    });

    // Highlight error category cells on hover
    $evaluation_table_wrapper.on("mouseenter", "td", function() {
        if (is_error_cell(this)) {
            $(this).addClass("hovered");
        }
    });
    $evaluation_table_wrapper.on("mouseleave", "td", function() {
        $(this).removeClass("hovered");
    });

    // Highlight all cells in a row belonging to the same mention_type or type or the "all" column on hover
    $evaluation_table_wrapper.on("mouseenter", "td", function() {
        if ($(this).attr('class')) {
            let cls = $(this).attr('class').split(/\s+/)[0];
            if (cls in MENTION_TYPE_HEADERS || is_type_string(cls) || cls === "all") {
                // Mark all cells in the corresponding row with the corresponding class
                $(this).closest('tr').find('.' + cls).each(function() {
                    $(this).addClass("hovered");
                });
            }
        }
    });
    $evaluation_table_wrapper.on("mouseleave", "td", function() {
        if ($(this).attr('class')) {
            let cls = $(this).attr('class').split(/\s+/)[0];
            if (cls in MENTION_TYPE_HEADERS || is_type_string(cls) || cls === "all") {
                $(this).closest('tr').find('.' + cls).each(function() {
                    $(this).removeClass("hovered");
                });
            }
        }
    });

    // Reposition annotation tooltips on the right edge of the window on mouseenter
    // Annotation could be in the prediction overview or the example modal
    $("table").on("mouseenter", ".annotation", function() {
        reposition_annotation_tooltip(this);
    });

    // Position table tooltips
    $evaluation_table_wrapper.on("mouseenter", ".tooltip", function() {
        position_table_tooltip(this);
    });

    // Annotation tooltip positions and size need to be reset on window resize
    // otherwise some might overlap with the left window edge.
    $(window).on('resize', function(){
        $("table .annotation").find(".tooltiptext").each(function() {
            if (parseInt($(this).css("right")) === 0) {
                $(this).css({"right": "auto", "left": "0", "white-space": "nowrap", "width": "auto",
                             "transform": "none"});
            }
        });
    });

    // Set the table filter strings and show-deprecated checkbox according to the URL parameters
    if (window.url_param_experiment_filter) $experiment_filter.val(window.url_param_experiment_filter);
    if (window.url_param_benchmark_filter) $benchmark_filter.val(window.url_param_benchmark_filter);
    $("#checkbox_deprecated").prop('checked', window.url_param_show_deprecated);
    if (window.url_param_experiment_filter || window.url_param_benchmark_filter || !window.url_param_show_deprecated) filter_table_rows();

    // Synchronize the top and bottom scrollbar of the evaluation table
    // Prevent double calls to .scroll() by using a flag
    let second_call = false;
    $evaluation_table_wrapper.scroll(function(){
        if (!second_call) {
            $("#top_scrollbar_wrapper").scrollLeft($evaluation_table_wrapper.scrollLeft());
            second_call = true;
        } else {
            second_call = false;
        }
    });
    $("#top_scrollbar_wrapper").scroll(function(){
        if (!second_call) {
            $evaluation_table_wrapper.scrollLeft($("#top_scrollbar_wrapper").scrollLeft());
            second_call = true;
        } else {
            second_call = false;
        }
    });

    initialize_table();

    $('table').on('stickyHeadersInit', function() {
        // Add table header tooltips to sticky header
        $("#evaluation_table_wrapper .tablesorter-sticky-wrapper th").each(function() {
            const keys = get_table_header_keys(this);
            const tooltiptext = get_th_tooltip_text(keys[0], keys[1]);
            if (tooltiptext) {
                tippy(this, {
                    content: tooltiptext,
                    allowHTML: true,
                    interactive: (tooltiptext.includes("</a>")),
                    appendTo: document.body,
                    theme: 'light-border',
                });
            }
        });
    });

    // Update URL on table sort (without refreshing the site)
    $evaluation_table.bind("sortEnd",function() {
        const sort_order = $("#evaluation_table_wrapper table")[0].config.sortList;
        const url = new URL(window.location);
        url.searchParams.set('sort_order', sort_order.join(","));
        window.history.replaceState({}, '', url);
    });

    // Jump back and forward between emphasised annotations
    reset_annotation_selection();
    $(document).on("keydown", function(event) {
        if ($experiment_filter.is(":focus") || $benchmark_filter.is(":focus") || $("#article_select").is(":focus")) return;
        if ([39, 37].includes(event.which)) {
            window.all_highlighted_annotations = [[], []];
            window.all_highlighted_annotations[0] = $("#prediction_overview td:nth-child(1) .annotation.beginning").not(".lowlight");
            if (window.selected_experiment_ids.length > 1) {
                window.all_highlighted_annotations[1] = $("#prediction_overview td:nth-child(2) .annotation.beginning").not(".lowlight");
            }
            if (event.ctrlKey && event.which === 39) {
                // Jump to next error highlight
                // This is not needed anymore when only the numerator mentions (i.e. the errors) are highlighted anyway
                // but keep it until we know for sure that we don't want to display denominator mentions.
                scroll_to_next_annotation(true);
            } else if (event.ctrlKey && event.which === 37) {
                scroll_to_previous_annotation(true);
            } else if (event.which === 39) {
                // Jump to next highlight
                scroll_to_next_annotation(false);
            } else if (event.which === 37) {
                // Jump to previous highlight
                scroll_to_previous_annotation(false);
            }
        }
    });
});


/**********************************************************************************************************************
 Functions for READING URL PARAMETERS
 *********************************************************************************************************************/

function read_url_parameters() {
    window.url_param_experiment_filter = get_url_parameter_string(get_url_parameter("experiment_filter"));
    window.url_param_benchmark_filter = get_url_parameter_string(get_url_parameter("benchmark_filter"));
    window.url_param_show_deprecated = get_url_parameter_boolean(get_url_parameter("show_deprecated"));
    window.url_param_compare = get_url_parameter_boolean(get_url_parameter("compare"));
    window.url_param_article = get_url_parameter_string(get_url_parameter("article"));
    window.url_param_experiment = get_url_parameter_array(get_url_parameter("experiment"), false);
    window.url_param_emphasis = get_url_parameter_array(get_url_parameter("emphasis"), false);
    window.url_param_show_columns = get_url_parameter_array(get_url_parameter("show_columns"), false);
    window.url_param_sort_order = get_url_parameter_array(get_url_parameter("sort_order"), true);
    window.url_param_access = get_url_parameter_string(get_url_parameter("access"));
    window.url_param_evaluation_mode = get_url_parameter_string(get_url_parameter("evaluation_mode"));
    window.url_param_group_by = get_url_parameter_string(get_url_parameter("group_by"));
}

function get_url_parameter(parameter_name) {
    /*
     * Retrieve URL parameter.
     * See https://stackoverflow.com/a/21903119/7097579.
     */
    const page_url = window.location.search.substring(1);
    const url_variables = page_url.split('&');

    for (let i = 0; i < url_variables.length; i++) {
        const curr_parameter = url_variables[i].split('=');
        if (curr_parameter[0] === parameter_name) {
            // "+" should be decoded as whitespace
            return curr_parameter[1] === undefined ? true : decodeURIComponent((curr_parameter[1]+'').replace(/\+/g, '%20'));
        }
    }
    return false;
}

function get_url_parameter_boolean(url_parameter) {
    return ["true", "1", true].includes(url_parameter);
}

function get_url_parameter_string(url_parameter) {
    /*
     * Returns the url_parameter if the url parameter value is a String, otherwise (if
     * it is a boolean) returns null.
     */
    if (is_string(url_parameter)) {
        return url_parameter;
    }
    return null;
}

function get_url_parameter_array(url_parameter, is_integer_array) {
    /*
    Returns the url_parameter as array if the url parameter value is a String, with elements separated by ",".
    Otherwise (if it is a boolean) returns an empty array.
    */
    if (is_string(url_parameter)) {
        let array = url_parameter.split(",");
        if (is_integer_array) array = array.map(function(el) { return parseInt(el) })
        return array;
    }
    return [];
}

function is_string(object) {
    return typeof object === 'string' || object instanceof String;
}


/**********************************************************************************************************************
Functions for READING DATA FROM FILES
 *********************************************************************************************************************/

function read_initial_data() {
    /*
     * Read all data files that are necessary when the webapp is first loaded.
     * Start with the config file, since other data readers rely on information from the config.
     */
    return read_config().then(function() {
        return $.when(
            read_whitelist_types(),
            read_example_benchmark_data(),
            read_benchmark_articles(),
            read_evaluation_results()
        );
    });
}

function read_config() {
    /*
     * Read the content of the json configuration file into the config dictionary.
     */
    return $.get(CONFIG_PATH, function(data){
        window.config = data;
    });
}

function read_whitelist_types() {
    /*
     * Read the whitelist type mapping (type QID to label) and returns a promise.
     */
    return $.get("whitelist_types.tsv", function (data) {
        for (let line of data.split("\n")) {
            if (line.length > 0) {
                let lst = line.split("\t");
                // Map from <type_id> (lst[0]) to <type_label> (lst[1])
                window.whitelist_types[lst[0]] = lst[1];
            }
        }
    });
}

function read_example_benchmark_data() {
    /*
     * Read the example benchmark articles and evaluation cases.
     */
    return $.when(
        // Read the example benchmark articles
        $.get(EXAMPLE_BENCHMARK_PATH, function(data) {
            for (let line of data.split("\n")) {
                if (line.length > 0) window.articles_example_benchmark.push(JSON.parse(line));
            }
        }),
        // Read the example benchmark evaluation cases
        $.get(EXAMPLE_BENCHMARK_EVAL_CASES_PATH, function(data) {
            for (let line of data.split("\n")) {
                if (line.length > 0) window.evaluation_cases_example_benchmark.push(JSON.parse(line));
            }
        })
    );
}

function read_benchmark_articles() {
    /*
     * Read the benchmark articles of all available benchmark files in the benchmarks directory.
     */
    // Get the names of the benchmark files from the benchmarks directory
    let metadata_filenames = [];
    return $.get("benchmarks", function(folder_data){
        $(folder_data).find("a").each(function() {
            let filename = $(this).attr("href");
            if (filename.endsWith(BENCHMARK_EXTENSION)) window.benchmark_filenames.push(filename);
            if (filename.endsWith(METADATA_EXTENSION)) metadata_filenames.push(filename);
        });
    }).then(function() {
        // Read all detected benchmark files
        return $.when(
            $.when.apply($, window.benchmark_filenames.map(function(filename) {
                if ("obscure_aida_conll" in window.config && window.config["obscure_aida_conll"] && filename.startsWith("aida") && "42" !== window.url_param_access) {
                    // Show obscured AIDA-CoNLL benchmark if specified in config and no access token is provided
                    filename = filename + ".obscured";
                }
                return $.get("benchmarks/" + filename, function(data) {
                    let benchmark = filename.replace(BENCHMARK_EXTENSION, "");
                    window.benchmark_articles[benchmark] = [];
                    for (let line of data.split("\n")) {
                        if (line.length > 0) window.benchmark_articles[benchmark].push(JSON.parse(line));
                    }
                });
            })),
            // Retrieve benchmarks metadata for table tooltips and the second table column text
            $.when.apply($, metadata_filenames.map(function (filename) {
                let benchmark = filename.replace(METADATA_EXTENSION, "");
                return $.getJSON("benchmarks/" + filename, function (metadata) {
                    window.benchmarks_metadata[benchmark] = metadata;
                });
            }))
        );
    });
}

function read_evaluation_results() {
    let folders = [];
    let results_urls = [];
    let metadata_urls = [];
    return $.get(EVALUATION_RESULT_PATH, function(data) {
        // Get all folders from the evaluation results directory
        $(data).find("a").each(function() {
            let name = $(this).attr("href");
            name = name.substring(0, name.length - 1);
            folders.push(name);
        });
    }).then(function() {
        // Retrieve file path of .eval_results.json files for the selected benchmark in each folder
        return $.when.apply($, folders.map(function(folder) {
            return $.get(EVALUATION_RESULT_PATH + "/" + folder, function(folder_data) {
                $(folder_data).find("a").each(function() {
                    let filename = $(this).attr("href");
                    let url = EVALUATION_RESULT_PATH + "/" + folder + "/" + filename;
                    if (filename.endsWith(RESULTS_EXTENSION)) results_urls.push(url);
                    if (filename.endsWith(METADATA_EXTENSION)) metadata_urls.push(url);
                });
            });
        })).then(function() {
            // Retrieve contents of each .eval_results.json file for the selected benchmark and store it in an array
            return $.when(
                $.when.apply($, results_urls.map(function (url) {
                    let experiment_id = url.substring(url.lastIndexOf("/") + 1, url.length - RESULTS_EXTENSION.length);

                    return $.getJSON(url, function (results) {
                        // Add the radio buttons for the different evaluation modes if they haven't been added yet
                        if ($('#evaluation_overview #evaluation_modes').find("input").length === 0) {
                            add_eval_mode_radio_buttons(results);
                        }

                        window.evaluation_result_files[experiment_id] = url.substring(0, url.length - RESULTS_EXTENSION.length);

                        // Filter out certain keys in results according to config
                        $.each(results, function (eval_mode) {
                            $.each(results[eval_mode]["error_categories"], function (key) {
                                if ("hide_error_checkboxes" in window.config && window.config["hide_error_checkboxes"].includes(key))
                                    delete results[eval_mode]["error_categories"][key];
                            });
                            $.each(results[eval_mode]["entity_types"], function (key) {
                                let type_label = key.toLowerCase().replace(/Q[0-9]+:/g, "");
                                type_label = type_label.replace(" ", "_");
                                if ("hide_type_checkboxes" in window.config && (window.config["hide_type_checkboxes"].includes(key) ||
                                    window.config["hide_type_checkboxes"].includes(type_label)))
                                    delete results[eval_mode]["entity_types"][key];
                            });
                            $.each(results[eval_mode]["mention_types"], function (key) {
                                if ("hide_mention_checkboxes" in window.config && window.config["hide_mention_checkboxes"].includes(key))
                                    delete results[eval_mode]["mention_types"][key];
                            });
                        })
                        // Add results for experiment to array
                        window.evaluation_results.push([experiment_id, results]);
                    })
                })),
                // Retrieve experiments metadata for table tooltips and the first table column text
                $.when.apply($, metadata_urls.map(function (url) {
                    let experiment_id = url.substring(url.lastIndexOf("/") + 1, url.length - METADATA_EXTENSION.length);
                    return $.getJSON(url, function (metadata) {
                        window.experiments_metadata[experiment_id] = metadata;
                    });
                }))
            );
        });
    });
}

function read_evaluation_cases(experiment_id) {
    /*
     * Retrieve evaluation cases from the given file and show the linked currently selected article.
     */
    // Clear evaluation case cache
    if (Object.keys(window.evaluation_cases).length >= MAX_CACHED_FILES) {
        let position = 0;
        let key = null;
        while (position < Object.keys(window.evaluation_cases).length) {
            key = Object.keys(window.evaluation_cases)[position];
            if (key !== experiment_id && !window.selected_experiment_ids.includes(key)) {
                break;
            }
            position++;
        }
        delete window.evaluation_cases[key];
        console.log("Deleting " + key + " from evaluation cases cache.");
    }

    // Read new evaluation cases
    if (!(experiment_id in window.evaluation_cases) || window.evaluation_cases[experiment_id].length === 0) {
        let path = window.evaluation_result_files[experiment_id] + ".eval_cases.jsonl";
        return $.get(path, function(data) {
            window.evaluation_cases[experiment_id] = [];
            for (let line of data.split("\n")) {
                if (line.length > 0) window.evaluation_cases[experiment_id].push(JSON.parse(line));
            }
        }).fail(function() {
            $("#evaluation_table_wrapper").html("ERROR: no file with cases found.");
            console.log("FAIL NOW CALL SHOW ARTICLE");
        });
    } else {
        // evaluation cases are already in cache
        return Promise.resolve(1);
    }
}

function read_linked_articles(experiment_id) {
    /*
     * Read the predictions of the selected experiment for all articles.
     * They are needed later to visualise the predictions outside the evaluation span of an article.
     */
    // Clear articles data cache
    if (Object.keys(window.articles_data).length >= MAX_CACHED_FILES) {
        let position = 0;
        let key = null;
        while (position < Object.keys(window.articles_data).length) {
            key = Object.keys(window.articles_data)[position];
            if (key !== experiment_id && !window.selected_experiment_ids.includes(key)) {
                break;
            }
            position++;
        }
        delete window.articles_data[key];
        console.log("Deleting " + key + " from articles data cache.");
    }

    if (!(experiment_id in window.articles_data) || window.articles_data[experiment_id].length === 0) {
        let path = window.evaluation_result_files[experiment_id] + ".linked_articles.jsonl";
        window.articles_data[experiment_id] = [];
        return $.get(path, function(data) {
            for (let line of data.split("\n")) {
                if (line.length > 0) window.articles_data[experiment_id].push(JSON.parse(line));
            }
        });
    } else {
        // linked articles are already in cache
        return Promise.resolve(1);
    }
}

function read_linking_results(experiment_id) {
    /*
     * Read the predictions and evaluation cases for the selected experiment for all articles.
     */
    let benchmark = get_benchmark_from_experiment_id(experiment_id);

    // The linked_articles.jsonl files are only needed to display linked entities outside the evaluation span.
    // Therefore, only read these files for benchmarks where the evaluation span can be not the entire article.
    if (benchmark.toLowerCase() === "wiki-ex" || benchmark.toLowerCase() === "newscrawl") {
        return $.when(
            read_linked_articles(experiment_id),
            read_evaluation_cases(experiment_id)
        )
    } else {
        return read_evaluation_cases(experiment_id)
    }
}


/**********************************************************************************************************************
 Functions for BUILDING THE EVALUATION RESULTS TABLE
 *********************************************************************************************************************/

function build_evaluation_results_table(initial_call) {
    /*
     * Build the overview table from the .eval_results.json files found in the subdirectories of the given path.
     */
    const $table_loading = $("#table_loading");
    $table_loading.addClass("show");

    const $evaluation_table = $("#evaluation_table_wrapper table");

    // Get current sort order
    const current_sort_order = $evaluation_table[0].config.sortList;

    // Remove previous evaluation table content
    $evaluation_table.trigger("destroy", false);
    $("#evaluation_table_wrapper table thead").empty();
    $("#evaluation_table_wrapper table tbody").remove();

    // Hide linking results section
    $("#prediction_overview").hide();

    let default_selected_experiment_ids;
    let default_selected_emphasis;
    if (initial_call) {
        // If URL parameter is set, select experiment according to URL parameter
        default_selected_experiment_ids = window.url_param_experiment;
        default_selected_emphasis = window.url_param_emphasis;
    } else {
        default_selected_experiment_ids = copy(window.selected_experiment_ids);
        default_selected_emphasis = window.selected_cells.map(function(el) {
            return ($(el).attr('class')) ? $(el).attr('class').split(/\s+/)[1] : null;
        });
    }

    // Reset variables indicating user selections within the table (they'll be set automatically again))
    window.selected_experiment_ids = [];
    window.selected_rows = [];
    window.selected_cells = [];
    reset_selected_cell_categories();

    // Add checkboxes. The evaluation mode does not affect the checkboxes, so just choose one.
    if (initial_call) add_evaluation_checkboxes(window.evaluation_results[0][1][get_evaluation_mode()]);
    // Add table header. The evaluation mode does not affect the table headers, so just choose one.
    add_evaluation_table_header(window.evaluation_results[0][1][get_evaluation_mode()]);
    // Add table body
    add_evaluation_table_body(window.evaluation_results);
    // Add tooltips for the experiment and benchmark columns
    add_experiment_tooltips();
    add_benchmark_tooltips();

    // Select default rows and cells
    if (default_selected_experiment_ids) {
        for (let i=0; i<default_selected_experiment_ids.length; i++) {
            let experiment_id = default_selected_experiment_ids[i];
            let row = $('#evaluation_table_wrapper table tbody tr').filter(function() {
                return get_experiment_id_from_row(this) === experiment_id;
            });
            if (row.length > 0) {
                if (i < default_selected_emphasis.length && default_selected_emphasis[i]) {
                    let cell = $(row).children("." + default_selected_emphasis[i]);
                    if (cell.length > 0) {
                        on_cell_click(cell[0]);
                    } else {
                        on_cell_click($(row).children("td:first")[0]);
                    }
                } else {
                    on_cell_click($(row).children("td:first")[0]);
                }
                on_row_click(row[0]);
            }
        }
    }

    // Remove the table loading GIF
    $table_loading.removeClass("show");

    // Update the tablesorter. The sort order is automatically adapted from the previous table.
    initialize_table();  // Since the entire tbody is replaced, triggering a simple update or updateAll is not enough

    if (initial_call && window.url_param_sort_order.length > 0) {
        // Use sort order from URL parameter
        $.tablesorter.sortOn( $evaluation_table[0].config, [ window.url_param_sort_order ]);
    } else if (initial_call) {
        // Sort on All - F1 column in descending order when loading the page if no sort order is specified in the URL
        $.tablesorter.sortOn( $evaluation_table[0].config, [[4, 1]]);
    } else {
        // Sort on last sort order when the table is rebuilt
        $.tablesorter.sortOn( $evaluation_table[0].config, current_sort_order);
    }

    // Fix the second table column to make it sticky
    position_second_column();

    set_top_scrollbar_width();
}

function add_evaluation_table_header(json_obj) {
    /*
     * Add html for the table header.
     */
    let first_row = "<tr><th colspan=2 onclick=$('#copy_table_modal').modal('show') class='copy_table'>" + COPY_TABLE_CELL_TEXT + "</th>";
    let second_row = "<tr><th>Experiment</th><th>Benchmark</th>";
    $.each(json_obj, function(key) {
        $.each(json_obj[key], function(subkey) {
            let colspan = 0;
            let class_name = get_class_name(subkey);
            $.each(json_obj[key][subkey], function(subsubkey) {
                if (!(IGNORE_HEADERS.includes(subsubkey))) {
                    let subclass_name = get_class_name(subsubkey);
                    let sort_order = (subkey in ERROR_CATEGORY_MAPPING) ? " data-sortinitialorder=\"asc\"" : "";
                    second_row += "<th class='" + class_name + " " + class_name + "-" + subclass_name + " sorter-digit'" + sort_order + ">" + get_table_heading(subkey, subsubkey) + "</th>";
                    colspan += 1;
                }
            });
            first_row += "<th colspan=\"" + colspan + "\" class='" + class_name + "'>" + get_table_heading(key, subkey) + "</th>";
        });
    });
    first_row += "</tr>";
    second_row += "</tr>";
    $('#evaluation_table_wrapper table thead').html(first_row + second_row);

    // Add table header tooltips
    $("#evaluation_table_wrapper th").each(function() {
        let keys = get_table_header_keys(this);
        let tooltiptext = get_th_tooltip_text(keys[0], keys[1]);
        if (tooltiptext) {
            tippy(this, {
                content: tooltiptext,
                allowHTML: true,
                interactive: (tooltiptext.includes("</a>")),
                appendTo: document.body,
                theme: 'light-border',
            });
        }
    });
}

function get_table_heading(key, subkey) {
    /*
     * Get the text for the table header cell that is defined via its evaluation results key and subkey.
     */
    const lower_key = key.toLowerCase();
    const lower_subkey = subkey.toLowerCase();
    if (key === "entity_types" && subkey in window.whitelist_types) {
        return "Type: " + window.whitelist_types[subkey];
    } else if (lower_key in EVALUATION_CATEGORY_TITLES && lower_subkey in EVALUATION_CATEGORY_TITLES[lower_key]) {
        return EVALUATION_CATEGORY_TITLES[lower_key][lower_subkey]["table_heading"];
    } else {
        return to_title_case(subkey.replace(/_/g, " "));
    }
}

function add_evaluation_table_body(result_list) {
    /*
     * Add the table bodies.
     * Show / Hide rows and columns according to checkbox state and filter-result input field.
     */
    const group_by = get_group_by();

    // Sort result list by benchmark
    if (group_by === "benchmark") {
        result_list.sort((a, b) => (get_benchmark_from_experiment_id(a[0]) > get_benchmark_from_experiment_id(b[0])) ? 1 : -1);
    } else {
        result_list.sort((a, b) => (get_experiment_name_from_experiment_id(a[0]) > get_experiment_name_from_experiment_id(b[0])) ? 1 : -1);
    }

    let last_element = null;
    let tbody = "";
    result_list.forEach(function(result_tuple) {
        let exp_id = result_tuple[0];
        let new_element = (group_by === "benchmark") ? get_benchmark_from_experiment_id(exp_id) : get_experiment_name_from_experiment_id(exp_id);
        // Get the results for the currently selected evaluation mode.
        let results = result_tuple[1][get_evaluation_mode()];

        // Append the last tbody if one exists and start the next one
        if (last_element !== new_element) {
            if (tbody.length !== 0) {
                tbody += "</tbody>";
                $('#evaluation_table_wrapper table').append(tbody);
            }
            tbody = "<tbody id='tbody_" + new_element + "'>";
        }

        // Add the new row to the current tbody
        if (results) tbody += get_table_row(exp_id, results);

        last_element = new_element;
    });
    // Append last tbody
    tbody += "</tbody>";
    $('#evaluation_table_wrapper table').append(tbody);

    // Show / Hide columns according to checkbox state
    $("input[id^='checkbox_']").each(function() {
        show_hide_columns(this, false);
    });

    // Show / Hide rows according to filter-result input field
    filter_table_rows();
}

function get_table_row(experiment_id, json_obj) {
    /*
     * Get html for the table row with the given experiment id and result values.
     */
    let benchmark = get_benchmark_from_experiment_id(experiment_id);
    let row = "<tr onclick='on_row_click(this)'>";
    let onclick_str = " onclick='on_cell_click(this)'";
    let displayed_experiment_name = get_displayed_experiment_name(experiment_id);
    let displayed_benchmark_name = get_displayed_benchmark_name(experiment_id);
    row += "<td " + onclick_str + " data-experiment=\"" + experiment_id + "\">" + displayed_experiment_name + "</td>";
    row += "<td " + onclick_str + " data-benchmark=\"" + benchmark + "\">" + displayed_benchmark_name + "</td>";
    $.each(json_obj, function(basekey) {
        $.each(json_obj[basekey], function(key) {
            let new_json_obj = json_obj[basekey][key];
            let class_name = get_class_name(key);
            $.each(new_json_obj, function(subkey) {
                // Include only keys in the table, that are not on the ignore list
                if (!(IGNORE_HEADERS.includes(subkey))) {
                    let value = new_json_obj[subkey];
                    if (value == null) {
                        // This means, the category does not apply to the given experiment
                        value = "-";
                    } else if (Object.keys(value).length > 0) {
                        // Values that consist not of a single number but of multiple
                        // key-value pairs are displayed in a single column.
                        let processed_value = "<div class='" + class_name + " tooltip'>";
                        let percentage = get_error_percentage(value);
                        processed_value += percentage + "%";
                        processed_value += "<span class='tooltiptext'>";
                        processed_value += value["errors"] + " / " + value["total"];
                        processed_value += "</span></div>";
                        value = processed_value;
                    } else if (PERCENTAGE_HEADERS.includes(subkey)) {
                        // Get rounded percentage but only if number is a decimal < 1
                        let processed_value = "<div class='" + class_name + " tooltip'>";
                        processed_value += (value * 100).toFixed(2) + "%";
                        // Create tooltip text
                        processed_value += "<span class='tooltiptext'>" + get_td_tooltip_text(new_json_obj) + "</span></div>";
                        value = processed_value;
                    }
                    let subclass_name = get_class_name(subkey);
                    let data_string = "data-category='" + class_name + "," + subclass_name + "'";
                    row += "<td class='" + class_name + " " + class_name + "-" + subclass_name + "' " + data_string + onclick_str + ">" + value + "</td>";
                }
            });
        });
    });
    row += "</tr>";
    return row;
}

function position_second_column() {
    /*
     * Fix the position of the second column in the evaluation results table to make it sticky.
     */
    // Get the width of the first table column (use th and not td, since all td might be hidden)
    let first_col_width = $("#evaluation_table_wrapper tr:nth-child(2) th:nth-child(1)").outerWidth();
    // Position the header cell in the second row, second column
    $("#evaluation_table_wrapper table thead tr:nth-child(2) th:nth-child(2)").css('left', first_col_width);
    // Position the normal cells in the second column
    $("#evaluation_table_wrapper table td:nth-child(2)").css('left', first_col_width);
}

function filter_table_rows() {
    /*
     * Filter table rows according to the experiment and benchmark filters.
     * Also filter table rows according to whether the show-deprecated checkbox is checked.
     */
    let experiment_keywords = $.trim($("input#experiment-filter").val()).split(/\s+/);
    let benchmark_keywords = $.trim($("input#benchmark-filter").val()).split(/\s+/);
    $("#evaluation_table_wrapper tbody tr").each(function() {
        let name = $(this).children("td:nth-child(1)").text();
        let benchmark = $(this).children("td:nth-child(2)").text();
        // Filter row according to filter keywords
        let show_row = experiment_keywords.every(keyword => name.search(keyword) !== -1);
        show_row &= benchmark_keywords.every(keyword => benchmark.search(keyword) !== -1);

        // Filter row according to show-deprecated checkbox
        if (!$("#checkbox_deprecated").is(":checked")) {
            // Filter if either table column text (from metadata file) or experiment ID (from filename)
            // contains the word deprecated, so that one can simply rename the files for them to be filtered
            // and does not have to go into the metadata files and change the title.
            let exp_id = get_experiment_id_from_row(this);
            show_row &= !name.includes("deprecated");
            show_row &= !exp_id.includes("deprecated");
        }
        if (show_row) $(this).show(); else $(this).hide();
    });

    // Check if a table body consists only of hidden rows and if so add the class 'all_hidden'
    const $evaluation_tbody = $('#evaluation_table_wrapper tbody');
    $.each($evaluation_tbody, function() {
        if($(this).find("tr:visible").length === 0) {
            $(this).addClass("all_hidden");
        } else {
            $(this).removeClass("all_hidden");
        }
    });

    // The table width may have changed due to adding or removing the scrollbar
    // therefore change the width of the top scrollbar div accordingly and re-position
    // the sticky second column.
    set_top_scrollbar_width();
    position_second_column();
}

function on_group_by_change(el) {
    // Update current URL without refreshing the site
    const url = new URL(window.location);
    url.searchParams.set('group_by', $(el).val());
    window.history.replaceState({}, '', url);

    // Re-build the overview table over all .eval_results.json-files from the evaluation-results folder.
    build_evaluation_results_table(false);
}

function initialize_table() {
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
}


/**********************************************************************************************************************
 Functions for HANDLING TABLE CLICKS
 *********************************************************************************************************************/

function comparing_different_benchmarks(selected_exp_id) {
    /*
     * Return true if the user is trying to compare linking results of different benchmarks.
     */
    if (is_compare_checked() && window.selected_experiment_ids.length === 1) {
        let b1 = get_benchmark_from_experiment_id(window.selected_experiment_ids[0]);
        let b2 = get_benchmark_from_experiment_id(selected_exp_id);
        return b1 !== b2;
    }
    return false;
}

function on_row_click(el) {
    /*
     * This method is called when a table body row was clicked.
     * This marks the row as selected and reads the evaluation cases.
     */
    // Get a timestamp for the click to help maintain the order in which evaluation cases are loaded
    let timestamp = new Date().getTime();
    window.last_show_article_request_timestamp = timestamp;

    let experiment_id = get_experiment_id_from_row(el);
    let previous_benchmark = (window.selected_experiment_ids.length >= 1) ? get_benchmark_from_experiment_id(window.selected_experiment_ids[0]) : null;
    let new_benchmark = get_benchmark_from_experiment_id(experiment_id);

    let $evaluation_table_rows = $("#evaluation_table_wrapper table tbody tr");

    // De-select previously selected rows
    if (!is_compare_checked() || window.selected_experiment_ids.length >= MAX_SELECTED_APPROACHES) {
        $("#evaluation_table_wrapper tbody tr").removeClass("selected");
        window.selected_rows = [];
        window.selected_experiment_ids = [];
        $evaluation_table_rows.removeClass("sibling_selected");
    }

    // Show alert message if the user tries to compare experiments on different benchmarks
    if (comparing_different_benchmarks(experiment_id)) {
        alert("Linking results can only be compared side-by-side if the experiments have been run on " +
            "the same benchmark. You tried to select the experiments "
            + window.selected_experiment_ids[0] + " and " + experiment_id);
        return;
    }

    // Show the loading GIF
    $("#loading").addClass("show");

    if (!window.selected_experiment_ids.includes(experiment_id)) {
        window.selected_experiment_ids.push(experiment_id);
        // Select clicked row
        $(el).addClass("selected");
        window.selected_rows.push(el);
    }
    let selected_exp_ids_copy = [...window.selected_experiment_ids];

    // Highlight table rows with experiments of the same name if grouped by benchmark
    if (!is_compare_checked()) $evaluation_table_rows.removeClass("sibling_selected");
    if (get_group_by() === "benchmark") {
        // Get all rows whose experiment column has the same text
        let experiment_name = $(el).find("td:nth-child(1)").text();
        $evaluation_table_rows.each(function() {
            if (this !== el && $(this).find("td:nth-child(1)").text().toLowerCase() === experiment_name.toLowerCase()) {
                $(this).addClass("sibling_selected");
            }
        });
    }

    // Update current URL without refreshing the site
    const url = new URL(window.location);
    url.searchParams.set('experiment', window.selected_experiment_ids.join(","));
    window.history.replaceState({}, '', url);

    read_linking_results(experiment_id).then(function() {
        // Reset article select options only if a different benchmark was previously selected or if it
        const article_select_val = $("#article_select").val();
        if (previous_benchmark !== new_benchmark || article_select_val == null) set_article_select_options(new_benchmark, article_select_val==null);
        show_article(selected_exp_ids_copy, timestamp);
    });
}

function on_cell_click(el) {
    /*
     * Highlight error category / type cells on click and un-highlight previously clicked cell.
     * Add or remove error categories and types to/from current selection.
     */
    // Reject the cell click if the user tries to compare experiments on different benchmarks
    let experiment_id = get_experiment_id_from_row($(el).closest("tr"));
    if (comparing_different_benchmarks(experiment_id)) return;

    // Determine whether an already selected cell has been clicked
    let curr_row = $(el).closest("tr").index();
    let prev_selected_rows = $.map(window.selected_rows, function(sel_row) { return $(sel_row).index(); });
    let already_selected_row_clicked = $.inArray(curr_row, prev_selected_rows);
    if (window.selected_cells.length > 0) {
        if (!is_compare_checked() || window.selected_rows.length >= MAX_SELECTED_APPROACHES) {
            // Remove selected classes for all currently selected cells
            for (let i=0; i<window.selected_cells.length; i++) {
                remove_selected_classes(window.selected_cells[i]);
            }
            window.selected_cells = [];
            reset_selected_cell_categories();
        } else {
            // Remove selected class for cells in the same row
            let last_rows = $.map(window.selected_cells, function(sel_cell) { return $(sel_cell).closest('tr').index(); });
            let index = $.inArray(curr_row, last_rows);
            if (index >= 0) {
                remove_selected_classes(window.selected_cells[index]);
                window.selected_cells.splice(index, 1);
                window.selected_cell_categories[index] = null;
            }
        }
    }

    // Make new selection
    let classes = ($(el).attr('class')) ? $(el).attr('class').split(/\s+/) : [];  // Experiment column has no class attribute
    if (is_error_cell(el)) {
        $(el).addClass("selected");
        window.selected_cells.push(el);
    } else if (classes.length > 0 && (classes[0] in MENTION_TYPE_HEADERS || is_type_string(classes[0]))) {
        $(el).closest('tr').find('.' + classes[0]).each(function() {
            $(this).addClass("selected");
        });
        window.selected_cells.push(el);
    } else {
        // Select "all" column
        let added = false;
        $(el).closest('tr').find('.all').each(function() {
            $(this).addClass("selected");
            if (!added) {
                // Add a single cell from the "all" column. Which one does not matter.
                window.selected_cells.push(this);
                added = true;
            }
        });
    }

    // Updated selected cell categories
    // Note that selected_rows is updated in on_row_click(), i.e. after on_cell_click() is called so no -1 necessary.
    let exp_index = (already_selected_row_clicked >= 0 || !is_compare_checked()) ? 0 : window.selected_rows.length % MAX_SELECTED_APPROACHES;
    window.selected_cell_categories[exp_index] = get_error_category_or_type(el);

    // Update current URL without refreshing the site
    const url = new URL(window.location);
    url.searchParams.set('emphasis', window.selected_cells.map(function(el) {return ($(el).attr('class')) ? $(el).attr('class').split(/\s+/)[1] : []}).join(","));
    window.history.replaceState({}, '', url);
}


/**********************************************************************************************************************
 Functions for HANDLING TOOLTIPS
 *********************************************************************************************************************/

function position_table_tooltip(anchor_el) {
    const anchor_el_rect = anchor_el.getBoundingClientRect();
    $(anchor_el).find(".tooltiptext").each(function() {
        const tooltip_rect = this.getBoundingClientRect();
        const font_size = $(this).css("font-size").replace("px", "");
        const top = anchor_el_rect.top - tooltip_rect.height - (font_size / 2);
        $(this).css({"left": anchor_el_rect.left + "px", "top": top + "px"});
    });
}

function reposition_annotation_tooltip(annotation_el) {
    /*
     * Re-position all tooltips of an annotation such that they don't go outside the window.
     */
    const annotation_rect = annotation_el.getBoundingClientRect();
    // Check whether the annotation contains a line break by checking whether its height is bigger than the line height
    const line_height = parseInt($(annotation_el).css('line-height'));
    const line_break = (annotation_rect.height > line_height + 5);
    $(annotation_el).find(".tooltiptext").each(function() {
        let tooltip_rect = this.getBoundingClientRect();

        // Table could be either prediction_overview or the table in the example modal
        const table_rect = $(this).closest("table")[0].getBoundingClientRect();

        // If the tooltip width is larger than the table width, enable line-wrapping
        // in the tooltip
        if (tooltip_rect.width > table_rect.width) {
            // Set the new width to the width of the table, minus tooltip padding and
            // border since those are added on top of css width.
            const paddings = parseInt($(this).css('paddingLeft')) + parseInt($(this).css('paddingRight'));
            const borders = parseInt($(this).css('borderLeftWidth')) + parseInt($(this).css('borderRightWidth'));
            const new_width = table_rect.width - (paddings + borders);
            $(this).css({"white-space": "normal", "width": new_width + "px"});
            // Recompute the tooltip rectangle
            tooltip_rect = this.getBoundingClientRect();
        }

        // Correct the tooltip position if it overlaps with the right edge of the table
        // If the annotation contains a line break, position to the right
        if ((annotation_rect.left + tooltip_rect.width > table_rect.right) || line_break)  {
            // Align right tooltip edge with right edge of the annotation.
            // Left needs to be set to auto since it is otherwise still 0.
            $(this).css({"right": "0px", "left": "auto"});

            // If now the left tooltip edge overlaps with the left edge of the table
            // translate the table as far right as possible
            if (annotation_rect.right - tooltip_rect.width < table_rect.left) {
                const translation = table_rect.right - annotation_rect.right;
                this.style.transform = "translateX(" + translation + "px)";
            }
        }
    });
}

function add_experiment_tooltips() {
    /*
     * Add tooltips to the experiment column of the table.
     */
    $("#evaluation_table_wrapper table tbody tr").each(function() {
        let experiment_id = get_experiment_id_from_row(this);
        let metadata = window.experiments_metadata[experiment_id];
        if (metadata) {
            let tooltiptext = "";
            if (metadata.experiment_description) tooltiptext += "<p><i>" + metadata.experiment_description + "</i></p>";
            if (metadata.linking_time || metadata.timestamp) tooltiptext += "<p>";
            if (metadata.linking_time) tooltiptext += "Linking took " + metadata.linking_time.toFixed(2) + "s<br>";
            if (metadata.timestamp) tooltiptext += metadata.timestamp;
            if (metadata.linking_time || metadata.timestamp) tooltiptext += "</p>";
            if (tooltiptext) {
                tippy("#evaluation_table_wrapper table tbody tr td[data-experiment=\"" + experiment_id + "\"]", {
                    content: tooltiptext,
                    allowHTML: true,
                    interactive: false,
                    theme: 'light-border',
                });
            }
        }
    });
}

function add_benchmark_tooltips() {
    /*
     * Add tooltips to the benchmark column of the table.
     */
    for (let benchmark in benchmarks_metadata) {
        let metadata = window.benchmarks_metadata[benchmark];
        if (metadata) {
            let tooltiptext = "";
            if (metadata.description) tooltiptext += "<p><i>" + metadata.description + "</i></p>";
            if (metadata.timestamp) tooltiptext += "<p>Added " + metadata.timestamp + "</p>";
            if (tooltiptext) {
                tippy("#evaluation_table_wrapper table tbody tr td[data-benchmark=\"" + benchmark + "\"]", {
                    content: tooltiptext,
                    allowHTML: true,
                    interactive: false,
                    theme: 'light-border',
                });
            }
        }
    }
}

function get_td_tooltip_text(json_obj) {
    /*
     * Get the tooltip text for the table cell from the given json obj.
     */
    let tooltip_text = "TP: " + Math.round(json_obj["true_positives"] * 100) / 100 + "<br>";
    tooltip_text += "FP: " + Math.round(json_obj["false_positives"] * 100) / 100 + "<br>";
    tooltip_text += "FN: " + Math.round(json_obj["false_negatives"] * 100) / 100 + "<br>";
    tooltip_text += "GT: " + Math.round(json_obj["ground_truth"] * 100) / 100;
    return tooltip_text;
}

function get_th_tooltip_text(key, subkey) {
    /*
     * Get the tooltip text (including html) for the table header cell specified by the
     * given evaluation results key and subkey.
     */
    if (key.toLowerCase() in HEADER_DESCRIPTIONS) {
        key = key.toLowerCase();
        subkey = subkey.toLowerCase();
        if (typeof HEADER_DESCRIPTIONS[key] == "string") {
            return HEADER_DESCRIPTIONS[key];
        }
        if (subkey in HEADER_DESCRIPTIONS[key]) {
            let tooltip_text = HEADER_DESCRIPTIONS[key][subkey];
            if (!["", "all"].includes(subkey)) {
                tooltip_text += TOOLTIP_EXAMPLE_HTML;
            }
            return tooltip_text;
        } else {
            const tp_string = "<p>" + HEADER_DESCRIPTIONS[key]["tp"] + "</p>";
            const fp_string = "<p>" + HEADER_DESCRIPTIONS[key]["fp"] + "</p>";
            const fn_string = "<p>" + HEADER_DESCRIPTIONS[key]["fn"] + "</p>";
            let string = "<p>" + HEADER_DESCRIPTIONS[subkey] + "</p>";
            if (subkey === "precision") {
                string += tp_string;
                string += fp_string;
            } else if (subkey === "recall") {
                string += tp_string;
                string += fn_string;
            } else if (subkey === "f1") {
                string += tp_string;
                string += fp_string;
                string += fn_string;
            }
            return string;
        }
    } else if (key.toUpperCase() in window.whitelist_types || key.toLowerCase() === "other") {
        key = key.toUpperCase();
        const type = (key in window.whitelist_types) ? window.whitelist_types[key] : "Other";
        if (subkey) {
            // Get tooltips for precision, recall and f1
            const tp_string = "<p><i>TP</i>: True Positives of type " + type + "</p>";
            const fp_string = "<p><i>FP</i>: False Positives of type " + type + "</p>";
            const fn_string = "<p><i>FN</i>: False Negatives of type " + type + "</p>";
            let string = "<p>" + HEADER_DESCRIPTIONS[subkey] + "</p>";
            if (subkey === "precision") {
                string += tp_string;
                string += fp_string;
            } else if (subkey === "recall") {
                string += tp_string;
                string += fn_string;
            } else if (subkey === "f1") {
                string += tp_string;
                string += fp_string;
                string += fn_string;
            }
            return string;
        } else {
            return "Results for entities of type \"" + type + "\".";
        }
    }
    return "";
}


/**********************************************************************************************************************
 Functions for EVALUATION RESULT CHECKBOXES
 *********************************************************************************************************************/

function add_evaluation_checkboxes(json_obj) {
    /*
     * Add checkboxes for showing / hiding columns.
     */
    $.each(json_obj, function(key) {
        $.each(json_obj[key], function(subkey) {
            const class_name = get_class_name(subkey);
            const label = get_checkbox_label(key, subkey);
            const checked = ((class_name === "all" && window.url_param_show_columns.length === 0) || window.url_param_show_columns.includes(class_name)) ? "checked" : "";
            let checkbox_html = "<span id=\"checkbox_span_" + class_name + "\"><input type=\"checkbox\" id=\"checkbox_" + class_name + "\" onchange=\"on_column_checkbox_change(this, true)\" " + checked + ">";
            checkbox_html += "<label for='checkbox_" + class_name + "'>" + label + "</label></span>\n";
            let checkbox_div_id = "";
            if (key === "mention_types") checkbox_div_id = "mention_type_checkboxes";
            if (key === "error_categories") checkbox_div_id = "error_category_checkboxes";
            if (key === "entity_types") checkbox_div_id = "entity_type_checkboxes";
            $("#" + checkbox_div_id + ".checkboxes").append(checkbox_html);

            // Add tooltip for checkbox
            tippy("#checkbox_span_" + class_name, {
                content: get_th_tooltip_text(subkey, ""),
                allowHTML: true,
                theme: 'light-border',
            });
        });
    });
}

function get_checkbox_label(key, subkey) {
    /*
     * Get the label for the checkbox specified via the given evaluation results key and subkey.
     */
    const lower_key = key.toLowerCase();
    const lower_subkey = subkey.toLowerCase();
    if (key === "entity_types" && subkey in window.whitelist_types) {
        return window.whitelist_types[subkey];
    } else if (lower_key in EVALUATION_CATEGORY_TITLES && lower_subkey in EVALUATION_CATEGORY_TITLES[lower_key]) {
        return EVALUATION_CATEGORY_TITLES[lower_key][lower_subkey]["checkbox_label"];
    } else {
        return to_title_case(subkey.replace(/_/g, " "));
    }
}

function on_column_checkbox_change(element, resize) {
    show_hide_columns(element, resize);

    // Update current URL without refreshing the site
    let checkbox_ids = [];
    $("#evaluation_overview .checkboxes input[type=checkbox]:checked").each(function() {
        checkbox_ids.push($(this).attr("id").split(/\s+/)[0].replace("checkbox_", ""));
    });
    const url = new URL(window.location);
    url.searchParams.set('show_columns', checkbox_ids.join(","));
    window.history.replaceState({}, '', url);
}

function show_hide_columns(element, resize) {
    /*
     * This function should be called when the state of a checkbox is changed.
     * This can't be simply added in on document ready, because checkboxes are added dynamically.
     */
    let col_class = $(element).attr("id");
    col_class = col_class.substring(col_class.indexOf("_") + 1, col_class.length);
    const column = $("#evaluation_table_wrapper table ." + col_class);
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


/**********************************************************************************************************************
 Functions for EVALUATION MODE RADIO BUTTONS
 *********************************************************************************************************************/

function add_eval_mode_radio_buttons(json_obj) {
    /*
     * Add radio buttons for the evaluation modes as extracted from the jsonl results file.
     */
    $.each(json_obj, function(key) {
        const class_name = get_class_name(key);
        const checked = ((class_name === "ignored" && window.url_param_evaluation_mode == null) || window.url_param_evaluation_mode === class_name) ? "checked" : "";
        let radio_button_html = "<span id=\"span_radio_eval_mode_" + class_name + "\">"
        radio_button_html += "<input id='radio_eval_mode_" + class_name + "' type=\"radio\" name=\"eval_mode\" value=\"" + key + "\" onchange=\"on_eval_mode_change(this)\" " + checked + ">";
        radio_button_html += "<label for='radio_eval_mode_" + class_name + "'>" + EVALUATION_MODE_LABELS[class_name] + "</label></span>\n";
        $("#evaluation_modes").append(radio_button_html);

        // Add radio button tooltip
        tippy('#evaluation_modes #span_radio_eval_mode_' + class_name, {
            content: HEADER_DESCRIPTIONS["evaluation_mode"][class_name],
            allowHTML: true,
            theme: 'light-border',
        });
    });
}

function on_eval_mode_change(el) {
    // Update current URL without refreshing the site
    const url = new URL(window.location);
    url.searchParams.set('evaluation_mode', get_class_name($(el).val()));
    window.history.replaceState({}, '', url);

    // Re-build the overview table over all .eval_results.json-files from the evaluation-results folder.
    build_evaluation_results_table(false);
}


/**********************************************************************************************************************
 Functions for ARTICLE SELECTION
 *********************************************************************************************************************/

function set_article_select_options(benchmark, is_initial_call) {
    /*
     * Set the options for the article selector element to the names of the articles from the list 'articles'.
     */
    // Empty previous options
    const $article_select = $("#article_select");
    $article_select.empty();

    // Add default "All articles" option
    let option_text_suffix = (["newscrawl", "wiki-ex"].includes(benchmark)) ? " (evaluated span only)" : "";
    let option_text = "All " + window.benchmark_articles[benchmark].length + " articles" + option_text_suffix;
    $article_select.append(new Option(option_text, ""));

    // Create new options
    for (let ai in window.benchmark_articles[benchmark]) {
        let article = window.benchmark_articles[benchmark][ai];
        // Shorten the article title if it's longer than 40 characters
        let title;
        if (article.title) {
            title = (article.title.length <= 40) ? article.title : article.title.substring(0, 40) + "..."
        } else {
            // On some benchmarks (e.g. AIDA-CoNLL), articles don't have titles.
            // In that case use the first 40 characters of the article.
            title = article.text.substring(0, Math.min(40, article.text.length)) + "...";
        }
        $article_select.append(new Option(title, ai));
    }

    // Set the article according to URL parameter if one with a valid article name exists
    let article_by_url = $('#article_select option').filter(function () { return $(this).html() === window.url_param_article; });
    if (window.url_param_article) {
        if (is_initial_call) {
            if (article_by_url.length > 0) $(article_by_url).prop('selected', true);
        } else {
            // Update current URL without refreshing the site
            const url = new URL(window.location);
            url.searchParams.set('article', $("#article_select option:selected").text());
            window.history.replaceState({}, '', url);
        }
    }
    $("#select_article").css("visibility", "visible");
}

function on_article_select() {
    const timestamp = new Date().getTime();
    window.last_show_article_request_timestamp = timestamp;
    show_article(window.selected_experiment_ids, timestamp);

    // Update current URL without refreshing the site
    const url = new URL(window.location);
    url.searchParams.set('article', $("#article_select option:selected").text());
    window.history.replaceState({}, '', url);
}


/**********************************************************************************************************************
 Functions for EXAMPLE BENCHMARK MODAL
 *********************************************************************************************************************/

function show_example_benchmark_modal(el) {
    /*
     * Open the example benchmark model and show the example article that corresponds
     * to the error category of the clicked table header tooltip.
     */
    // Get example error category of the table tooltip to highlight only corresponding mentions
    // Hack to get the reference object from the clicked tippy tooltip.
    let table_header_cell = $(el).parent().parent().parent().parent()[0]._tippy.reference;
    let selected_category = get_error_category_or_type(table_header_cell);

    // Get table header title
    let keys = get_table_header_keys(table_header_cell);
    let error_category_title = keys[0].replace(/_/g, " ") + " - " + keys[1].replace(/_/g, " ");

    // Determine article index of selected example
    let article_index = 0;
    for (let i=0; i<window.articles_example_benchmark.length; i++) {
        let article = window.articles_example_benchmark[i];
        if (article.title.toLowerCase().includes(error_category_title)) {
            article_index = i;
            break;
        }
    }

    // Display error explanation extracted from table header tooltip text
    let error_explanation = HEADER_DESCRIPTIONS[keys[0]][keys[1]];
    error_explanation = error_explanation.replace(/.*<i>Numerator:<\/i> (.*?)<\/p>.*/, "$1");
    $("#error_explanation").text("Description: " + error_explanation);
    // Display annotated text
    let textfield = $("#example_prediction_overview tr td");
    show_annotated_text("example.error-category-examples", $(textfield[0]), selected_category, 100, article_index);
    $("#example_prediction_overview tr th").text(window.articles_example_benchmark[article_index].title);
}


/**********************************************************************************************************************
 Functions for DISPLAYING ANNOTATED ARTICLES
 *********************************************************************************************************************/

function show_annotated_text(experiment_id, textfield, selected_cell_category, column_idx, article_index) {
    /*
     * Generate annotations and tooltips for predicted and ground truth mentions of the selected experiment
     * and article and show them in the textfield.
     */
    let benchmark = get_benchmark_from_experiment_id(experiment_id);
    let example_benchmark = is_example_benchmark(benchmark);
    let articles = (example_benchmark) ? window.articles_example_benchmark : window.benchmark_articles[benchmark];
    let annotated_text = "";
    if (window.is_show_all_articles && !example_benchmark) {
        let annotated_texts = [];
        for (let i=0; i < articles.length; i++) {
            let annotations = get_annotations(i, experiment_id, benchmark, column_idx);
            annotated_texts.push(annotate_text(articles[i].text,
                                               annotations,
                                               articles[i].hyperlinks,
                                               articles[i].evaluation_span,
                                               selected_cell_category));
        }

        for (let i=0; i < annotated_texts.length; i++) {
            if (i !== 0) annotated_text += "<hr/>";
            if (articles[i].title) annotated_text += "<b>" + articles[i].title + "</b><br>";
            annotated_text += annotated_texts[i];
        }
    } else {
        let curr_article = articles[article_index];
        let annotations = get_annotations(article_index, experiment_id, benchmark, column_idx);
        annotated_text = annotate_text(curr_article.text, annotations, curr_article.hyperlinks, [0, curr_article.text.length], selected_cell_category);
    }
    textfield.html(annotated_text);
}

function get_annotations(article_index, experiment_id, benchmark, column_idx) {
    /*
     * Generate annotations for the predicted entities of the selected experiment and article.
     *
     * This method first combines the predictions outside the evaluation span (from file <experiment_id>.linked_articles.jsonl)
     * with the evaluated predictions inside the evaluation span (from file <experiment_id>.eval_cases.jsonl),
     * and then generates annotations for all of them.
     */
    let eval_mode;
    let example_benchmark = is_example_benchmark(benchmark);
    let article_cases;
    let article_data;
    if (example_benchmark) {
        eval_mode = "IGNORED";
        article_cases = window.evaluation_cases_example_benchmark[article_index];
    } else {
        // Get currently selected evaluation mode
        eval_mode = get_evaluation_mode();
        article_cases = window.evaluation_cases[experiment_id][article_index];
        // Get info from the linked_articles file to display mentions outside the evaluation span
        if (experiment_id in window.articles_data) article_data = window.articles_data[experiment_id][article_index];

    }

    let child_label_to_parent = {};
    let label_id_to_label = {};
    for (let eval_case of article_cases) {
        // Build the parent mapping
        if ("true_entity" in eval_case && eval_case.true_entity.children) {
            label_id_to_label[eval_case.true_entity.id] = eval_case.true_entity;
            for (let child_id of eval_case.true_entity.children) {
                child_label_to_parent[child_id] = eval_case.true_entity.id;
            }
        }
    }

    // evaluation span
    let evaluation_begin = window.benchmark_articles[benchmark][article_index].evaluation_span[0];
    let evaluation_end = window.benchmark_articles[benchmark][article_index].evaluation_span[1];

    // list of all predicted mentions (inside and outside the evaluation span)
    let mentions = [];

    // get the mentions before the evaluation span
    if (article_data && "entity_mentions" in article_data) {
        for (let prediction of article_data.entity_mentions) {
            if (prediction.span[1] < evaluation_begin) {
                mentions.push(prediction);
            }
        }
    }
    // get the cases inside the evaluation span from the cases list
    for (let eval_case of article_cases) {
        mentions.push(eval_case);
    }
    // get the mentions after the evaluation span
    if (article_data && "entity_mentions" in article_data) {
        for (let prediction of article_data.entity_mentions) {
            if (prediction.span[0] >= evaluation_end) {
                mentions.push(prediction);
            }
        }
    }

    // list with tooltip information for each mention
    let annotations = {};
    let prediction_spans = [];
    let annotation_count = 0;
    for (let mention of mentions) {
        if (mention.factor === 0) {
            // Do not display overlapping GT mentions
            continue;
        }

        // Do not display overlapping predictions: Keep the larger one.
        // Assume that predictions are sorted by span start (but not by span end)
        // Includes mentions with "predicted_entity" but also mentions outside the evaluation span
        // with neither "true_entity" nor "predicted_entity"
        if ("predicted_entity" in mention || (!("predicted_entity" in mention) && !("true_entity" in mention))) {
            let last_index = prediction_spans.length - 1;
            if (prediction_spans.length > 0 && prediction_spans[last_index][1] > mention.span[0]) {
                // Overlap detected.
                const previous_span_length = prediction_spans[last_index][1] - prediction_spans[last_index][0];
                const current_span_length = mention.span[1] - mention.span[0];
                if (previous_span_length >= current_span_length) {
                    // Previous span is longer than current span so discard current prediction
                    continue;
                } else if (!("true_entity" in mention) && "gt_entity_id" in annotations[prediction_spans[last_index]]) {
                    // Previous span is shorter or equal to current span but the current prediction contains no GT
                    // entity and the previous did, so discard current prediction
                    continue;
                }
                else {
                    delete annotations[prediction_spans[last_index]];
                    prediction_spans.splice(-1);
                }
            }
            prediction_spans.push(mention.span);
        }

        let gt_annotation = {};
        let pred_annotation = {};
        if ("predicted_entity" in mention || "true_entity" in mention) {
            // mention is an evaluated case. Get the annotation class.
            let linking_eval_types = mention.linking_eval_types[eval_mode];
            if (linking_eval_types.includes("TP")) {
                gt_annotation.class = ANNOTATION_CLASS_TP;
                pred_annotation.class = ANNOTATION_CLASS_TP;
            } else if (linking_eval_types.includes("FP")) {
                pred_annotation.class = ANNOTATION_CLASS_FP;
                if (linking_eval_types.includes("FN")) {
                    gt_annotation.class = ANNOTATION_CLASS_FN;
                } else if (mention.optional) {
                    gt_annotation.class = ANNOTATION_CLASS_OPTIONAL;
                } else if ("true_entity" in mention && mention.true_entity.entity_id.startsWith("Unknown")) {
                    gt_annotation.class = ANNOTATION_CLASS_UNKNOWN;
                }
            } else if (linking_eval_types.includes("FN")) {
                gt_annotation.class = ANNOTATION_CLASS_FN;
                if ("predicted_entity" in mention && mention.predicted_entity.entity_id == null) {
                    pred_annotation.class = ANNOTATION_CLASS_UNKNOWN;
                }
            } else {
                if (mention.optional) {
                    gt_annotation.class = ANNOTATION_CLASS_OPTIONAL;
                } else if ("true_entity" in mention && mention.true_entity.entity_id.startsWith("Unknown")) {
                    gt_annotation.class = ANNOTATION_CLASS_UNKNOWN;
                }
                if ("predicted_entity" in mention && mention.predicted_entity.entity_id == null) {
                    pred_annotation.class = ANNOTATION_CLASS_UNKNOWN;
                } else if ("predicted_entity" in mention) {
                    pred_annotation.class = ANNOTATION_CLASS_UNEVALUATED;
                }
            }

            if ("true_entity" in mention) {
                // Use the type of the parent entity because this is the type that counts in the evaluation.
                let curr_label_id = mention.true_entity.id;
                while (curr_label_id in child_label_to_parent) {
                    curr_label_id = child_label_to_parent[curr_label_id];
                }
                gt_annotation.gt_entity_type = label_id_to_label[curr_label_id].type;
                // Get text of parent span
                if (curr_label_id !== mention.true_entity.id) {
                    let parent_span = label_id_to_label[curr_label_id].span;
                    const articles = (example_benchmark) ? window.articles_example_benchmark : window.benchmark_articles[benchmark];
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
                if (pred_annotation.class === ANNOTATION_CLASS_TP) {
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

        const mention_type = (mention.mention_type) ? mention.mention_type.toLowerCase() : null;
        let annotation = {
            "span": mention.span,
            "mention_type": mention_type,
            "error_labels": [],
            "beginning": true,
        };
        // If the case has a GT and a prediction, don't add error cases to GT if it's an unknown or optional case
        if (!$.isEmptyObject(gt_annotation) && !$.isEmptyObject(pred_annotation)) {
            if (gt_annotation.class === ANNOTATION_CLASS_OPTIONAL || gt_annotation.class === ANNOTATION_CLASS_UNKNOWN) {
                pred_annotation.error_labels = mention.error_labels[eval_mode];
            } else {
                gt_annotation.error_labels = mention.error_labels[eval_mode];
                pred_annotation.error_labels = mention.error_labels[eval_mode];
            }
            gt_annotation.id = column_idx + "_" + article_index+ "_" + annotation_count;
            annotation_count++;
            pred_annotation.id = column_idx + "_" + article_index+ "_" + annotation_count;
            annotation_count++;
        } else {
            if (mention.error_labels) annotation.error_labels = mention.error_labels[eval_mode];
            annotation.id = column_idx + "_" + article_index+ "_" + annotation_count;
            annotation_count++;
        }
        // Merge basic annotations and case specific annotations into a single annotation object
        // If the annotation contains both a ground truth and a prediction, make the prediction the inner annotation of
        // the ground truth annotation in order not to create overlapping annotations.
        if (!$.isEmptyObject(gt_annotation)) {
            gt_annotation = {...annotation, ...gt_annotation};
            annotations[mention.span] = gt_annotation;
            if (!$.isEmptyObject(pred_annotation)) {
                pred_annotation = {...annotation, ...pred_annotation};
                gt_annotation.inner_annotation = pred_annotation;
            }
        } else if (!$.isEmptyObject(pred_annotation)) {
            pred_annotation = {...annotation, ...pred_annotation};
            annotations[mention.span] = pred_annotation;
        }
    }
    annotations = Object.values(annotations);
    return annotations
}

function annotate_text(text, annotations, hyperlinks, evaluation_span, selected_cell_category) {
    /*
     * Generate tooltips for the given annotations and html hyperlinks for the given hyperlinks.
     * Tooltips and hyperlinks can overlap.
     *
     * Arguments:
     * - text: The original text without tooltips or hyperlinks.
     * - annotations: A sorted (by span) list of objects containing tooltip information
     * - hyperlinks: A sorted (by span) list of tuples (span, target_article)
     * - evaluation_span: The span of the article that can be evaluated
     * - selected_cell_categories: categories of the selected cell for the corresponding experiment
     *
     * First the overlapping annotations and hyperlinks get combined to combined_annotations.
     * Second, the annotations with hyperlinks are added to the text and a tooltip is generated for each annotation.
     */
    // Separate mention annotations into two distinct lists such that any one list does not contain annotations that
    // overlap.
    let only_groundtruth_annotations = [];
    let non_groundtruth_annotations = [];
    for (let i=0; i<annotations.length; i++) {
        const ann = annotations[i];
        if (ann.gt_entity_id) {
            only_groundtruth_annotations.push([copy(ann.span), ann]);
        } else {
            non_groundtruth_annotations.push([copy(ann.span), ann]);
        }
    }

    // Transform hyperlinks into a similar format as the mention annotations
    let new_hyperlinks = [];
    if (hyperlinks) {
        for (let link of hyperlinks) { new_hyperlinks.push([copy(link[0]), {"span": link[0], "hyperlink": link[1]}]); }
    }

    // STEP 1: Combine overlapping annotations and hyperlinks.
    // Consumes the first element from the link list or annotation list, or a part from both if they overlap.
    let combined_annotations = combine_overlapping_annotations(only_groundtruth_annotations, non_groundtruth_annotations);
    // Links must be the last list that is added such that they can only be the innermost annotations, because <div>
    // tags are not allowed within <a> tags, but the other way round is valid.
    combined_annotations = combine_overlapping_annotations(combined_annotations, new_hyperlinks);

    // Text should only be the text within the given evaluation span (Careful: This is the entire article if a
    // single article is supposed to be shown and the article evaluation span if all articles are supposed to be
    // shown)
    text = text.substring(0, evaluation_span[1]);

    // STEP 2: Add the combined annotations and hyperlinks to the text.
    // This is done in reverse order so that the text before is always unchanged. This allows to use the spans as given.
    for (const ann of combined_annotations.reverse()) {
        const span = ann[0];
        if (span[1] > evaluation_span[1]) {
            continue;
        } else if (span[0] < evaluation_span[0]) {
            break;
        }
        // annotation is a tuple with (span, annotation_info)
        const annotation = ann[1];
        const before = text.substring(0, span[0]);
        const snippet = text.substring(span[0], span[1]);
        const after = text.substring(span[1]);
        const replacement = generate_annotation_html(snippet, annotation, selected_cell_category);
        text = before + replacement + after;
    }
    text = text.substring(evaluation_span[0], text.length);
    text = text.replaceAll("\n", "<br>");
    return text;
}

function generate_annotation_html(snippet, annotation, selected_cell_category) {
    /*
     * Generate html snippet for a given annotation. A hyperlink is also regarded as an annotation
     * and can be identified by the property "hyperlink". Inner annotations, e.g. hyperlinks contained in
     * a mention annotation, nested mention annotations are contained given by the property "inner_annotation".
     */
    let inner_annotation = snippet;

    if ("inner_annotation" in annotation) {
        inner_annotation = generate_annotation_html(snippet, annotation.inner_annotation, selected_cell_category);
    }

    if ("hyperlink" in annotation) {
        return "<a href=\"https://en.wikipedia.org/wiki/" + annotation.hyperlink + "\" target=\"_blank\">" + inner_annotation + "</a>";
    }

    // Add tooltip
    let tooltip_classes = "tooltiptext";
    let tooltip_header_text = "";
    let tooltip_case_type_html = "";
    let tooltip_body_text = "";
    let tooltip_footer_html = "";
    if (annotation.class === ANNOTATION_CLASS_TP && annotation.pred_entity_id) {
        const wikidata_url = "https://www.wikidata.org/wiki/" + annotation.pred_entity_id;
        const entity_link = "<a href=\"" + wikidata_url + "\" target=\"_blank\">" + annotation.pred_entity_id + "</a>";
        let entity_name;
        if (annotation.pred_entity_name != null) {
            entity_name = (["Unknown", "null"].includes(annotation.pred_entity_name)) ? MISSING_LABEL_TEXT : annotation.pred_entity_name;
            entity_name = entity_name + " (" + entity_link + ")";
        } else {
            entity_name = entity_link;
        }
        tooltip_header_text += entity_name;
    } else if (annotation.class === ANNOTATION_CLASS_TP && annotation.gt_entity_id) {
        tooltip_classes += " below";
    } else {
        if ("pred_entity_id" in annotation) {
            if (annotation.pred_entity_id) {
                let entity_name = (["Unknown", "null"].includes(annotation.pred_entity_name)) ? MISSING_LABEL_TEXT : annotation.pred_entity_name;
                const wikidata_url = "https://www.wikidata.org/wiki/" + annotation.pred_entity_id;
                const entity_link = "<a href=\"" + wikidata_url + "\" target=\"_blank\">" + annotation.pred_entity_id + "</a>";
                tooltip_header_text += "Prediction: " + entity_name + " (" + entity_link + ")";
            } else {
                // NIL prediction
                tooltip_header_text += "Prediction: " + NIL_PREDICTION_TEXT;
            }
        }
        if (annotation.gt_entity_id ) {
            if (tooltip_header_text) { tooltip_header_text += "<br>"; }
            if (NO_LABEL_ENTITY_IDS.includes(annotation.gt_entity_id) || annotation.gt_entity_id.startsWith("Unknown")) {
                // For Datetimes, Quantities and Unknown GT entities don't display "Label (QID)"
                // instead display "[DATETIME]"/"[QUANTITY]" or "[UNKNOWN #xy]" or "[UNKNOWN]"
                let entity_name = annotation.gt_entity_id;
                if (annotation.gt_entity_id === "Unknown") {
                    entity_name = "UNKNOWN";
                } else if (annotation.gt_entity_id.startsWith("Unknown")) {
                    entity_name = "UNKNOWN #" + annotation.gt_entity_id.replace("Unknown", "");
                }
                tooltip_header_text += "Groundtruth: [" + entity_name + "]";
            } else {
                let entity_name = (annotation.gt_entity_name === "Unknown") ? MISSING_LABEL_TEXT : annotation.gt_entity_name;
                const wikidata_url = "https://www.wikidata.org/wiki/" + annotation.gt_entity_id;
                const entity_link = "<a href=\"" + wikidata_url + "\" target=\"_blank\">" + annotation.gt_entity_id + "</a>";
                tooltip_header_text += "Groundtruth: " + entity_name + " (" + entity_link + ")";
            }
            if (annotation.class === ANNOTATION_CLASS_OPTIONAL) tooltip_body_text += "Note: Detection is optional<br>";
            if (annotation.class === ANNOTATION_CLASS_UNKNOWN) tooltip_body_text += "Note: Entity not found in the knowledge base<br>";
            if (![ANNOTATION_CLASS_OPTIONAL, ANNOTATION_CLASS_UNKNOWN].includes(annotation.class) && annotation.gt_entity_type) {
                const type_string = $.map(annotation.gt_entity_type.split("|"), function(qid){ return get_type_label(qid) }).join(", ");
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
    if (![ANNOTATION_CLASS_UNEVALUATED, ANNOTATION_CLASS_UNKNOWN].includes(annotation.class) && annotation.pred_entity_type) {
        const type_string = $.map(annotation.pred_entity_type.split("|"), function(qid){ return get_type_label(qid) }).join(", ");
        tooltip_body_text += "Types: " + type_string + "<br>";
    }
    if (annotation.parent_text) tooltip_body_text += "Alternative span: \"" + annotation.parent_text + "\"<br>";
    // Add error category tags
    // Only show error category tags for once in the FP tooltip, i.e. don't double them in the GT tooltip for TP
    // and for disambiguation errors
    const correct_ner = (annotation.inner_annotation &&
                         annotation.inner_annotation.pred_entity_id &&
                         annotation.inner_annotation.span[0] === annotation.span[0] &&
                         annotation.inner_annotation.span[1] === annotation.span[1]);
    if (annotation.error_labels && annotation.error_labels.length > 0 && !correct_ner) {
        for (let e_i = 0; e_i < annotation.error_labels.length; e_i += 1) {
            let error_label = annotation.error_labels[e_i];
            error_label = error_label.replace(/_/g, " ").toLowerCase();
            if (e_i > 0) {
                tooltip_footer_html += " ";
            }
            tooltip_footer_html += "<span class=\"error_category_tag\">" + error_label + "</span>";
        }
    }

    // Use transparent version of the color, if an error category or type is selected
    // and the current annotation does not have a corresponding error category or type label
    let lowlight_mention = false;
    if (selected_cell_category) {
        lowlight_mention = true;
        for (const selected_category of selected_cell_category) {
            if (is_type_string(selected_category)) {
                const pred_type_selected = annotation.pred_entity_type && annotation.pred_entity_type.toLowerCase().split("|").includes(selected_category);
                const gt_type_selected = annotation.gt_entity_type && annotation.gt_entity_type.toLowerCase().split("|").includes(selected_category);
                if (pred_type_selected || gt_type_selected) {
                    lowlight_mention = false;
                    break;
                }
            } else {
                if ((annotation.error_labels && annotation.error_labels.includes(selected_category)) || annotation.mention_type === selected_category) {
                    lowlight_mention = false;
                    break;
                }
            }
        }
    }
    const lowlight = (lowlight_mention) ? " lowlight" : "";

    const annotation_kind = (annotation.gt_entity_id) ? "gt" : "pred";
    const beginning = (annotation.beginning) ? " beginning" : "";
    // Annotation id is a class because several spans can belong to the same annotation.
    const annotation_id_class = " annotation_id_" + annotation.id;
    let replacement = "<span class=\"annotation " + annotation_kind + " " + annotation.class + lowlight + beginning + annotation_id_class + "\">";
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
     * Combine two lists of potentially overlapping and nested annotations into a single list.
     * Overlaps are resolved by splitting annotations at the overlap into two.
     * Nestings are resolved by adding the inner annotation to the outer annotation via the
     * property "inner_annotation".
     *
     * NOTE: Links must be the last list that is added such that they can only be the inner-most
     * annotations, because <div> tags are not allowed within <a> tags.
     */
    let combined_annotations = [];
    while (list1.length > 0 || list2.length > 0) {
        if (list1.length === 0) {
            const list2_item = list2.shift();
            combined_annotations.push([list2_item[0], list2_item[1]]);
        } else if (list2.length === 0) {
            const list1_item = list1.shift();
            combined_annotations.push([list1_item[0], list1_item[1]]);
        } else {
            const list1_item = list1[0];
            const list2_item = list2[0];
            const list1_item_span = list1_item[0];
            const list2_item_span = list2_item[0];
            if (list2_item_span[0] < list1_item_span[0]) {
                // Add element from second list
                const list2_item_end = Math.min(list2_item_span[1], list1_item_span[0]);
                combined_annotations.push([[list2_item_span[0], list2_item_end], copy(list2_item[1])]);
                if (list2_item_end === list2_item_span[1]) {
                    list2.shift();
                } else {
                    list2[0][0][0] = list2_item_end;
                    list2_item[1].beginning = false;
                }
            } else if (list1_item_span[0] < list2_item_span[0]) {
                // Add element from first list
                const list1_item_end = Math.min(list1_item_span[1], list2_item_span[0]);
                combined_annotations.push([[list1_item_span[0], list1_item_end], copy(list1_item[1])]);
                if (list1_item_end === list1_item_span[1]) {
                    list1.shift();
                } else {
                    list1_item_span[0] = list1_item_end;
                    list1_item[1].beginning = false;
                }
            } else {
                // Add both
                const list1_item_ann = copy(list1_item[1]);
                let most_inner_ann = list1_item_ann;
                // Add element from second list as inner-most annotation of element from first list
                while ("inner_annotation" in most_inner_ann) {
                    most_inner_ann = most_inner_ann["inner_annotation"];
                }
                most_inner_ann["inner_annotation"] = copy(list2_item[1]);
                const list1_item_end = Math.min(list1_item_span[1], list2_item_span[1]);
                combined_annotations.push([[list1_item_span[0], list1_item_end], list1_item_ann]);
                if (list1_item_end === list2_item_span[1]) {
                    list2.shift();
                } else {
                    list2[0][0][0] = list1_item_end;
                    list2_item[1].beginning = false;
                }
                if (list1_item_end === list1_item_span[1]) {
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

async function show_article(selected_exp_ids, timestamp) {
    /*
     * Generate the ground truth textfield and predicted text field for the selected article
     * (or all articles if this option is selected) and experiment.
     */
    reset_annotation_selection();

    console.log("show_article() called for selected experiments", selected_exp_ids);

    if (timestamp < window.last_show_article_request_timestamp) {
        console.log("Dropping function call since newer call exists.");
        return;
    }

    let selected_article_index = $("#article_select").val();

    if (selected_article_index === "" || selected_article_index === null) {
        window.is_show_all_articles = true;
        $("#article_link").hide();
    } else {
        window.is_show_all_articles = false;
        let benchmark = get_benchmark_from_experiment_id(selected_exp_ids[0]);
        let article = window.benchmark_articles[benchmark][selected_article_index];

        let $article_link = $("#article_link");
        if (article.url) {
            $article_link.html("<a href=\"" + article.url + "\" target=\"_blank\">Wikipedia article</a>");
            $article_link.show();
        } else {
            $article_link.hide();
        }
    }

    $("#prediction_overview").show();
    let columns = $("#prediction_overview tbody tr td");
    let column_headers = $("#prediction_overview thead tr th");
    let column_idx = 0;

    let iteration = 0;
    while (!(selected_exp_ids[0] in window.evaluation_cases) || window.evaluation_cases[selected_exp_ids[0]].length === 0) {
        $(column_headers[column_idx]).text("");
        for (let i=1; i<columns.length; i++) {
            hide_table_column("prediction_overview", i);
        }
        if (iteration >= 10) {
            console.log("ERROR: Stop waiting for result.");
            $(columns[column_idx]).html("<b class='warning'>No experiment selected or no file with cases found.</b>");
            return;
        } else if (timestamp < window.last_show_article_request_timestamp) {
            console.log("ERROR: Stop waiting for result.");
            return;
        } else if (!selected_exp_ids[0]) {
            $(columns[column_idx]).html("<b class='warning'>No experiment selected in the evaluation results table.</b>");
            return;
        }
        // TODO: Check if this can still happen
        // TODO: should be triggerable at least by selecting article or toggle compare directly after selecting new experiment
        console.log("WARNING: selected experiment", selected_exp_ids[0], "not in evaluation cases. Waiting for result.");
        $(columns[column_idx]).html("<b>Waiting for results...</b>");
        await new Promise(r => setTimeout(r, 1000));
        iteration++;
    }

    // Show columns
    // Show first prediction column
    show_annotated_text(selected_exp_ids[0], $(columns[column_idx]), window.selected_cell_categories[0], column_idx, selected_article_index);
    let displayed_exp_name = get_displayed_experiment_name(selected_exp_ids[0]);
    let benchmark_name = get_displayed_benchmark_name(selected_exp_ids[0]);
    let emphasis_str = get_emphasis_string(window.selected_cell_categories[0]);
    $(column_headers[column_idx]).html(displayed_exp_name + "<span class='nonbold'> on " + benchmark_name + emphasis_str + "</span>");
    show_table_column("prediction_overview", column_idx);
    column_idx++;
    if(is_compare_checked() && selected_exp_ids.length > 1) {
        // Show second prediction column
        show_annotated_text(selected_exp_ids[1], $(columns[column_idx]), window.selected_cell_categories[1], column_idx, selected_article_index);
        displayed_exp_name = get_displayed_experiment_name(selected_exp_ids[1]);
        emphasis_str = get_emphasis_string(window.selected_cell_categories[1])
        $(column_headers[column_idx]).html(displayed_exp_name + "<span class='nonbold'> on " + benchmark_name + emphasis_str + "</span>");
        show_table_column("prediction_overview", column_idx);
        column_idx++;
    }

    // Hide unused columns
    for (let i=column_idx; i<columns.length; i++) {
        hide_table_column("prediction_overview", i);
    }

    // Set column width
    let width_percentage = 100 / column_idx;
    $("#prediction_overview th, #prediction_overview td").css("width", width_percentage + "%");

    // Hide the loading GIF
    if (timestamp >= window.last_show_article_request_timestamp) $("#loading").removeClass("show");
}

function get_emphasis_string(selected_cell_category) {
    /*
     * Create an emphasis string for the given selected category.
     */
    let emphasis = "all";
    let emphasis_type = "mention type";
    const mention_types = $.map( MENTION_TYPE_HEADERS, function(key){ return MENTION_TYPE_HEADERS[key]; });
    if (selected_cell_category) {
        let emphasis_strs = [];
        for (const selected_category of selected_cell_category) {
            if (is_type_string(selected_category)) {
                 emphasis_strs.push(get_type_label(selected_category));
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


/**********************************************************************************************************************
 Functions for JUMPING BETWEEN ERROR ANNOTATIONS
 *********************************************************************************************************************/

function scroll_to_next_annotation(only_errors) {
    /*
     * Scroll to the next annotation in the list of all annotations on the left and on the right side.
     */
    // Get potential next highlighted annotation for left and right side
    let next_annotation_index = [-1, -1];
    let next_annotations = [null, null];
    for (let i=0; i<2; i++) {
        if (window.all_highlighted_annotations[i].length === 0) continue;
        if (window.jump_to_annotation_index[i] + 1 < window.all_highlighted_annotations[i].length) {
            if (only_errors) {
                next_annotation_index[i] = find_next_annotation_index(i);
                if (next_annotation_index[i] < window.all_highlighted_annotations[i].length) next_annotations[i] = window.all_highlighted_annotations[i][next_annotation_index[i]];
            } else {
                next_annotation_index[i] = window.jump_to_annotation_index[i] + 1;
                next_annotations[i] = window.all_highlighted_annotations[i][next_annotation_index[i]];
            }
        }
    }

    let next_annotation;
    if (next_annotations[0] && next_annotations[1]) {
        if ($(next_annotations[0]).offset().top <= $(next_annotations[1]).offset().top) {
            next_annotation = next_annotations[0];
            window.jump_to_annotation_index[0] = next_annotation_index[0];
            window.last_highlighted_side = 0;
            if (only_errors && window.all_highlighted_annotations[1].length > 0) bring_jump_index_to_same_height(next_annotation, 1);
        } else {
            next_annotation = next_annotations[1];
            window.jump_to_annotation_index[1] = next_annotation_index[1];
            window.last_highlighted_side = 1;
            if (only_errors && window.all_highlighted_annotations[0].length > 0) bring_jump_index_to_same_height(next_annotation, 0);
        }
    } else if (next_annotations[0]) {
        next_annotation = next_annotations[0];
        window.jump_to_annotation_index[0] = next_annotation_index[0];
        window.last_highlighted_side = 0;
        if (only_errors && window.all_highlighted_annotations[1].length > 0) bring_jump_index_to_same_height(next_annotation, 1);
    } else if (next_annotations[1]) {
        next_annotation = next_annotations[1];
        window.jump_to_annotation_index[1] = next_annotation_index[1];
        window.last_highlighted_side = 1;
        if (only_errors && window.all_highlighted_annotations[0].length > 0) bring_jump_index_to_same_height(next_annotation, 0);
    } else if (!only_errors) {
        window.jump_to_annotation_index[window.last_highlighted_side] = window.all_highlighted_annotations[window.last_highlighted_side].length;
    }

    if (next_annotation) {
        scroll_to_annotation(next_annotation);
    }
}

function bring_jump_index_to_same_height(next_annotation, side_index) {
    // Bring the jump index for the other side to the same height
    if (side_index === 0) {
        while (window.jump_to_annotation_index[side_index] < 0 || (window.jump_to_annotation_index[side_index] <= window.all_highlighted_annotations[side_index].length &&
            $(window.all_highlighted_annotations[side_index][window.jump_to_annotation_index[side_index]]).offset().top <= $(next_annotation).offset().top)) {
            window.jump_to_annotation_index[side_index]++;
        }
    } else {
        while (window.jump_to_annotation_index[side_index] < 0 || (window.jump_to_annotation_index[side_index] <= window.all_highlighted_annotations[side_index].length &&
            $(window.all_highlighted_annotations[side_index][window.jump_to_annotation_index[side_index]]).offset().top < $(next_annotation).offset().top)) {
            window.jump_to_annotation_index[side_index]++;
        }
    }
    window.jump_to_annotation_index[side_index]--; // Minus one, because the next annotation should be the one determined above
}

function scroll_to_previous_annotation(only_errors) {
    // Get potential next highlighted annotation for left and right side
    let next_annotation_index = [-1, -1];
    let next_annotations = [null, null];
    for (let i=0; i<2; i++) {
        if (window.all_highlighted_annotations[i].length === 0) continue;
        if (window.jump_to_annotation_index[i] - 1 >= 0) {
            if (only_errors) {
                next_annotation_index[i] = find_previous_annotation_index(i, window.last_highlighted_side);
                if (next_annotation_index[i] >= 0) next_annotations[i] = window.all_highlighted_annotations[i][next_annotation_index[i]];
            } else {
                next_annotation_index[i] = window.jump_to_annotation_index[i] - (window.last_highlighted_side===i);
                next_annotations[i] = window.all_highlighted_annotations[i][next_annotation_index[i]];
            }
        }
    }

    let next_annotation;
    if (next_annotations[0] && next_annotations[1]) {
        if ($(next_annotations[0]).offset().top > $(next_annotations[1]).offset().top) {
            next_annotation = next_annotations[0];
            if (!only_errors || window.last_highlighted_side === 0) window.jump_to_annotation_index[window.last_highlighted_side] = next_annotation_index[window.last_highlighted_side];
            else {
                update_index_to_previous_annotation(next_annotation, window.last_highlighted_side);
                window.jump_to_annotation_index[Math.abs(window.last_highlighted_side - 1)] = next_annotation_index[Math.abs(window.last_highlighted_side - 1)];
            }
            window.last_highlighted_side = 0;
        } else {
            next_annotation = next_annotations[1];
            if (!only_errors || window.last_highlighted_side === 1) window.jump_to_annotation_index[window.last_highlighted_side] = next_annotation_index[window.last_highlighted_side];
            else {
                update_index_to_previous_annotation(next_annotation, window.last_highlighted_side);
                window.jump_to_annotation_index[Math.abs(window.last_highlighted_side - 1)] = next_annotation_index[Math.abs(window.last_highlighted_side - 1)];
            }
            window.last_highlighted_side = 1;
        }
    } else if (next_annotations[0]) {
        next_annotation = next_annotations[0];
        if (!only_errors || window.last_highlighted_side === 0) window.jump_to_annotation_index[window.last_highlighted_side] = next_annotation_index[window.last_highlighted_side];
        else {
            update_index_to_previous_annotation(next_annotation, window.last_highlighted_side);
            window.jump_to_annotation_index[Math.abs(window.last_highlighted_side - 1)] = next_annotation_index[Math.abs(window.last_highlighted_side - 1)];
        }
        window.last_highlighted_side = 0;
    } else if (next_annotations[1]) {
        next_annotation = next_annotations[1];
        if (!only_errors || window.last_highlighted_side === 1) window.jump_to_annotation_index[window.last_highlighted_side] = next_annotation_index[window.last_highlighted_side];
        else {
            update_index_to_previous_annotation(next_annotation, window.last_highlighted_side);
            window.jump_to_annotation_index[Math.abs(window.last_highlighted_side - 1)] = next_annotation_index[Math.abs(window.last_highlighted_side - 1)];
        }
        window.last_highlighted_side = 1;
    } else if (!only_errors) {
        window.jump_to_annotation_index[0] = -1;
        window.jump_to_annotation_index[1] = -1;
    }

    if (next_annotation) {
        scroll_to_annotation(next_annotation);
    }
}

function update_index_to_previous_annotation(next_annotation, side_index) {
    // Bring the jump index for the other side to the same height
    if (side_index === 0) {
        while (window.jump_to_annotation_index[side_index] === window.all_highlighted_annotations[side_index].length || (
            window.jump_to_annotation_index[side_index] >= -1 && $(window.all_highlighted_annotations[side_index][window.jump_to_annotation_index[side_index]]).offset().top > $(next_annotation).offset().top)) {
            window.jump_to_annotation_index[side_index]--;
        }
    } else {
        while (window.jump_to_annotation_index[side_index] === window.all_highlighted_annotations[side_index].length || (
            window.jump_to_annotation_index[side_index] >= -1 && $(window.all_highlighted_annotations[side_index][window.jump_to_annotation_index[side_index]]).offset().top >= $(next_annotation).offset().top)) {
            window.jump_to_annotation_index[side_index]--;
        }
    }
}

function find_next_annotation_index(side_index) {
    for (let i=window.jump_to_annotation_index[side_index] + 1; i<window.all_highlighted_annotations[side_index].length; i++) {
        let classes = $(window.all_highlighted_annotations[side_index][i]).attr("class").split(/\s+/);
        if (classes.includes("fn") || classes.includes("fp")) {
            return i;
        }
    }
    return window.all_highlighted_annotations[side_index].length;
}

function find_previous_annotation_index(side_index, last_highlighted_side) {
    for (let i=window.jump_to_annotation_index[side_index] - (last_highlighted_side===side_index); i > 0; i--) {
        let classes = $(window.all_highlighted_annotations[side_index][i]).attr("class").split(/\s+/);
        if (classes.includes("fn") || classes.includes("fp")) {
            return i;
        }
    }
    return -1;
}

function reset_annotation_selection() {
    window.jump_to_annotation_index = [-1, -1];
    window.last_highlighted_side = 0;
}

function scroll_to_annotation(annotation) {
    /*
    Scroll to the given annotation and mark it as selected for a second.
    */
    const line_height = parseInt($("#prediction_overview td").css('line-height').replace('px',''));
    const header_size = $("#prediction_overview thead")[0].getBoundingClientRect().height;
    $([document.documentElement, document.body]).animate({
        scrollTop: $(annotation).offset().top - header_size - line_height / 2
    }, 200);
    // Get annotation id class such that all spans belonging to one annotation can be marked as selected
    const classes = $(annotation).attr("class").split(/\s+/);
    const annotation_id_class = classes.filter(function(el) {return el.startsWith("annotation_id_"); });
    // Mark spans as selected
    $("." + annotation_id_class).addClass("selected")
    // Unmark spans as selected after timeout
    setTimeout(function() { $("." + annotation_id_class).removeClass("selected"); }, 1000);
}



/**********************************************************************************************************************
 Functions for COPYING TABLE
 *********************************************************************************************************************/

function copy_table() {
    /*
     * Copy the evaluation results table to clipboard.
     */
    // Get selected properties
    const format = $('input[name=copy_as]:checked').val();
    const include_experiment = $("#checkbox_include_experiment").is(":checked");
    const include_benchmark = $("#checkbox_include_benchmark").is(":checked");

    // Get the table header contents and count columns
    let num_cols = 0;
    let table_contents = [];
    $('#evaluation_table_wrapper table thead tr').each(function(row_index){
        // Tablesorter sticky table duplicates the thead. Don't include the duplicate.
        if ($(this).closest(".tablesorter-sticky-wrapper").length > 0) return;

        let table_row_contents = [];
        $(this).find('th').each(function() {
            if (!include_benchmark && $(this).text() === "Benchmark") return;
            if (!include_experiment && $(this).text() === "Experiment") return;
            // Do not add hidden table columns
            if (!$(this).is(":hidden")) {
                if (row_index > 0) num_cols += 1;
                // Underscore not within $ yields error
                let title = $(this).text().replace(/_/g, " ");
                // Get column span of the current header cell
                let colspan = parseInt($(this).attr("colspan"), 10);
                colspan = (colspan) ? colspan : 1;
                // Copy-Latex-cell should not have a header and colspan depends on whether to include
                // the experiment and benchmark columns
                if (title === COPY_TABLE_CELL_TEXT) {
                    title = "";
                    colspan = include_benchmark + include_experiment;
                    if (colspan === 0) return;
                }
                // Syntax: [cell_text, cell_span, header_cell?, numerical_cell?]
                table_row_contents.push([title, colspan, true, false]);
            }
        });
        table_contents.push(table_row_contents);
    });

    // Get the table body contents
    $("#evaluation_table_wrapper table tbody tr").each(function() {
        // Do not add hidden table rows
        if (!$(this).is(":hidden")) {
            let table_row_contents = [];
            let header_cell = false;
            let col_idx = 0;
            const num_header_cols = include_benchmark + include_experiment;
            $(this).find("td").each(function () {
                if ((!include_experiment && col_idx === 0) || (!include_benchmark && col_idx === 1)) {
                    col_idx += 1;
                    return;
                }

                // Do not add hidden table columns
                if (!$(this).is(":hidden")) {
                    let text = $(this).html();
                    // Filter out tooltip texts and html
                    const match = text.match(/<div [^<>]*>([^<>]*)<(span|div)/);
                    if (match) text = match[1];
                    const numerical_cell = (col_idx > num_header_cols - 1);
                    table_row_contents.push([text, 1, header_cell, numerical_cell]);
                    col_idx += 1;
                }
            });
            if (table_row_contents) table_contents.push(table_row_contents);
        }
    });

    // Get table text in the specified format
    let table_text;
    if (format === TABLE_FORMAT_LATEX) {
        table_text = produce_latex(table_contents, num_cols, include_experiment, include_benchmark);
    } else {
        table_text = produce_tsv(table_contents);
    }

    // Copy the table text to the clipboard
    const $copy_table_text_div = $("#evaluation_overview .copy_table_text");
    const $copy_table_textarea = $("#evaluation_overview .copy_table_text textarea");
    $copy_table_text_div.show();
    $copy_table_textarea.val(table_text);
    $copy_table_textarea.show();  // Text is not selected or copied if it is hidden
    $copy_table_textarea.select();
    document.execCommand("copy");
    $copy_table_textarea.hide();

    // Show the notification for the specified number of seconds
    const show_duration_seconds = 5;
    setTimeout(function() { $copy_table_text_div.hide(); }, show_duration_seconds * 1000);
}

function produce_latex(table_contents, n_cols, include_experiment, include_benchmark) {
    /*
     * Produce LaTeX source code for the given table contents.
     */
    // Comment that clarifies the origin of this code.
    let latex_string = "% Copied from " + window.location.href + " on " + new Date().toLocaleString();
    latex_string += "\n\n";

    // Begin table
    let alignment = "";
    const num_header_cols = include_benchmark + include_experiment;
    latex_string += "\\begin{table*}\n\\centering\n\\begin{tabular}{" + "l".repeat(num_header_cols) + "c".repeat(n_cols - num_header_cols) + "}\\hline\n";

    // Generate the header row of the table and count columns
    let last_cell_is_header = true;
    for (let row of table_contents) {
        let col_index = 0;
        for (let cell of row) {
            if (cell[2]) {
                // Cell is a header_cell
                alignment = (["Experiment", "Benchmark"].includes(cell[0])) ? "l" : "c";
                latex_string += "\\multicolumn{" + cell[1] + "}{" + alignment + "}{\\textbf{" + cell[0] + "}}";
                last_cell_is_header = true;
            } else {
                // Cell is a tbody cell
                if (last_cell_is_header) {
                    latex_string += ("\\hline\n");
                }
                const cell_text = cell[0].replace(/%/g, "\\%").replace(/_/g, " ");
                latex_string += (cell[3]) ? "$" + cell_text + "$" : cell_text;
                last_cell_is_header = false;
            }
            if (col_index < row.length - 1) latex_string += " & ";
            col_index += 1;
        }
        latex_string += "\\\\\n";
    }
    // End table
    latex_string += "\\hline\n\\end{tabular}\n\\caption{\\label{results}Fancy caption.}\n\\end{table*}\n";
    return latex_string;
}

function produce_tsv(table_contents) {
    /*
     * Produce TSV for the given table contents.
     */
    let tsv_string = "";
    for (let row of table_contents) {
        let col_idx = 0;
        for (let col of row) {
            let col_span = (col_idx < row.length - 1) ? col[1] : col[1] - 1;
            tsv_string += col[0] + "\t".repeat(col_span);
            col_idx += 1;
        }
        tsv_string += "\n";
    }
    return tsv_string;
}

/**********************************************************************************************************************
 Functions for MISC
 *********************************************************************************************************************/

function toggle_compare() {
    /*
     * Toggle compare checkbox.
     */
    if (!is_compare_checked()) {
        let timestamp = new Date().getTime();
        window.last_show_article_request_timestamp = timestamp;

        if (window.selected_experiment_ids.length > 1) {
            window.selected_experiment_ids = [window.selected_experiment_ids[1]];
        }

        // De-select evaluation table row
        if (window.selected_rows.length > 1) {
            let deselected_row = window.selected_rows.shift();  // Remove first element in array
            $(deselected_row).removeClass("selected");
            let deselected_cell = window.selected_cells.shift();
            window.selected_cell_categories = [window.selected_cell_categories[1], null];
            if (deselected_cell) remove_selected_classes(deselected_cell);
        }

        hide_table_column("prediction_overview", 1);

        show_article(window.selected_experiment_ids, timestamp);
    }
    // Update current URL without refreshing the site
    const url = new URL(window.location);
    url.searchParams.set('compare', $("#checkbox_compare").is(":checked"));
    url.searchParams.set('experiment', window.selected_experiment_ids.join(","));
    url.searchParams.set('emphasis', window.selected_cells.map(function(el) {return ($(el).attr('class')) ? $(el).attr('class').split(/\s+/)[1] : []}).join(","));
    window.history.replaceState({}, '', url);
}

function toggle_show_deprecated() {
    filter_table_rows();

    // Update current URL without refreshing the site
    const url = new URL(window.location);
    url.searchParams.set('show_deprecated', $("#checkbox_deprecated").is(":checked"));
    window.history.replaceState({}, '', url);
}

/**********************************************************************************************************************
 Functions for MINI UTILS
 *********************************************************************************************************************/

function get_table_header_keys(th_element) {
    /*
     * Get keys for table headers.
     * For the first table header row this is a single key, e.g. "entity_named".
     * For the second table header row this is two keys, e.g. "entity_named" and "precision".
     */
    let keys = ["", ""];
    const all_classes_string = $(th_element).attr('class');
    // Experiment column has no attribute 'class'
    if (all_classes_string) {
        const all_classes = all_classes_string.split(/\s+/);
        if (all_classes.length > 1) {
            // Second table header row
            const classes = all_classes[1].split("-");
            keys[0] = classes[0];
            keys[1] = classes[1]
        } else if (all_classes.length === 1) {
            // First table header row
            keys[0] = all_classes[0];
        }
    }
    return keys;
}

function show_table_column(table_id, index) {
    /*
     * Show the column with the given index in the table with the given id.
     */
    $("#" + table_id + " th:nth-child(" + (index + 1) + ")").show();
    $("#" + table_id + " td:nth-child(" + (index + 1) + ")").show();
}

function hide_table_column(table_id, index) {
    /*
     * Show the column with the given index in the table with the given id.
     */
    $("#" + table_id + " th:nth-child(" + (index + 1) + ")").hide();
    $("#" + table_id + " td:nth-child(" + (index + 1) + ")").hide();
}

function is_error_cell(el) {
    /*
     * Return true if the given cell is a error category td.
     */
    if ($(el).attr('class')) {  // Experiment column has no class attribute
        const classes = $(el).attr('class').split(/\s+/);
        if (classes.length > 1) {
            // The second class of a cell is its header and subheader (as class name) connected by "-"
            const keys = classes[1].split("-");
            if (keys[0] in ERROR_CATEGORY_MAPPING) {
                if (keys[1] in ERROR_CATEGORY_MAPPING[keys[0]]) {
                    return true;
                }
            }
        }
    }
    return false;
}

function get_error_category_or_type(el) {
    /*
     * For a given cell return the error category or type it belongs to, or null otherwise.
     */
    if ($(el).attr('class')) {
        const classes = $(el).attr('class').split(/\s+/);
        if (is_error_cell(el)) {
            const keys = classes[1].split("-");
            return ERROR_CATEGORY_MAPPING[keys[0]][keys[1]];
        } if (is_type_string(classes[0])) {
            return [get_type_qid(classes[0])];
        } else if (classes[0] in MENTION_TYPE_HEADERS) {
            return MENTION_TYPE_HEADERS[classes[0]];
        }
    }
    return null;
}

function is_type_string(class_name) {
    const match = class_name.match(/[Qq][0-9]+.*/);
    if (match || class_name === "other") {
        return true;
    }
}

function get_type_qid(string) {
    return string.replace(/([Qq][0-9]+).*/, "$1");
}

function get_type_label(qid) {
    const qid_upper = qid.replace("q", "Q");
    if (qid_upper in window.whitelist_types) {
        return window.whitelist_types[qid_upper];
    }
    return qid_upper + " (label missing)";
}

function get_class_name(text) {
    const name = text.toLowerCase().replace(/[ ,.#:]/g, "_");
    if (name !== text.toLowerCase()) console.log("WARNING! Class name is not identical to key: " + name + " vs. " + text);
    return name;
}

function to_title_case(str) {
    return str.replace(/\w\S*/g, function(txt) {
        return txt.charAt(0).toUpperCase() + txt.substring(1);
    });
}

function remove_selected_classes(el) {
    const cls = $(el).attr('class').split(/\s+/)[0];
    $(el).closest('tr').find('.' + cls).each(function() {
        $(this).removeClass("selected");
    });
}

function reset_selected_cell_categories() {
    /*
     * Initialize or reset the selected error categories.
     * The array contains one entry for each experiment that can be compared.
     */
    window.selected_cell_categories = new Array(MAX_SELECTED_APPROACHES).fill(null);
}

function set_top_scrollbar_width() {
    /*
     * Set width of the top scrollbar to the current width of the evaluation table + side scrollbar.
     */
    let width = $("#evaluation_table_wrapper table")[0].getBoundingClientRect().width + 20;  // + width of the side scrollbar
    $("#top_scrollbar").css({"width": width + "px"});
}

function is_example_benchmark(benchmark) {
    return benchmark === EXAMPLE_BENCHMARK_PATH.split("/")[1].replace(".benchmark.jsonl", "");
}

function is_compare_checked() {
    return $("#checkbox_compare").is(":checked");
}

function copy(object) {
    return JSON.parse(JSON.stringify(object));
}

function get_error_percentage(value) {
    if (value["total"] === 0) return 0.00;
    return (value["errors"] / value["total"] * 100).toFixed(2);
}

function get_evaluation_mode() {
    return $('input[name=eval_mode]:checked', '#evaluation_modes').val();
}

function get_group_by() {
    return $('input[name=group_by]:checked').val();
}

function get_benchmark_from_experiment_id(exp_id) {
    return exp_id.substring(exp_id.lastIndexOf(".") + 1, exp_id.length);
}

function get_experiment_name_from_experiment_id(exp_id) {
    return exp_id.substring(0, exp_id.lastIndexOf("."));
}

function get_experiment_id_from_row(row) {
    return $(row).find('td:nth-child(1)').data("experiment");
}

function get_displayed_experiment_name(exp_id) {
    /*
     * Get the experiment name that should be displayed in the experiment table column from the experiment ID.
     */
    let metadata_exp_name = (exp_id in window.experiments_metadata) ? window.experiments_metadata[exp_id].experiment_name : null;
    return (metadata_exp_name) ? metadata_exp_name : get_experiment_name_from_experiment_id(exp_id);
}

function get_displayed_benchmark_name(exp_id) {
    /*
     * Get the benchmark name that should be displayed in the benchmark table column from the experiment ID.
     */
    let benchmark = get_benchmark_from_experiment_id(exp_id);
    let metadata_benchmark_name = (benchmark in window.benchmarks_metadata) ? window.benchmarks_metadata[benchmark].name : null;
    return (metadata_benchmark_name) ? metadata_benchmark_name : benchmark;
}
