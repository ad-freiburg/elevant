window.ANNOTATION_CLASS_NORMAL = "normal";
window.ANNOTATION_CLASS_UNKNOWN = "unknown";
window.ANNOTATION_CLASS_OPTIONAL = "optional";

window.BENCHMARK_EXTENSION = ".benchmark.jsonl";
window.BENCHMARK_STATISTICS_EXTENSION = ".benchmark_statistics.jsonl";
window.METADATA_EXTENSION = ".metadata.json";

window.whitelist_types = {};

window.evaluation_result_files = {};
window.evaluation_results = [];

window.benchmark_filenames = [];
window.benchmark_statistics_filenames = [];

window.benchmark_statistics = {};
window.benchmark_metadata = {};
window.benchmark_articles = {};
window.benchmark_cases = {};

// Table parameters
window.selected_benchmark = null;
window.selected_row = null;
window.selected_cell = null;
window.selected_cell_category = null;

window.internal_benchmark_filter = "";

window.url_param_benchmark = null;
window.url_param_show_values_as = null;

window.HEADER_DESCRIPTIONS = {
    "text_statistics": {
        "": "Statistics about the benchmark texts. Only text within the evaluation span is considered (e.g., on Wiki-Fair, only the text within the three annotated paragraphs in each article is considered).",
        "words": "Number of words in the benchmark text (i.e., number of tokens as detected by spaCy that are not punctuation or whitespaces).",
        "sents": "Number of sentences in the benchmark text.",
        "articles": "Number of articles in the benchmark.",
        "labels": "Number of ground truth labels in the benchmark."
    },
    "mention_types": {
        "": "Statistics about the mention types of the ground truth labels.",
        "entity_named": "Amount of named entity ground truth mentions.",
        "entity_non_named": "Amount of non-named entity ground truth mentions.",
        "entity_unknown": "Amount of unknown ground truth mentions.",
        "coref_nominal": "Amount of nominal coreference mentions.",
        "coref_pronominal": "Amount of pronominal coreference mentions."
    },
    "types": {
        "": "Statistics about the entity types of the ground truth labels."
    },
    "multi_word_statistics": {
        "": "Statistics about the number of words in the ground truth mentions.",
        "1 word": "Amount of ground truth mentions that consist of one word.",
        "2 words": "Amount of ground truth mentions that consist of two words.",
        "3 words": "Amount of ground truth mentions that consist of three words.",
        "4 words": "Amount of ground truth mentions that consist of four words.",
        ">= 5 words": "Amount of ground truth mentions that consist of five or more words."
    },
    "tags": {
        "": "Other statistics about the ground truth labels.",
        "capitalized": "Amount of ground truth mentions that start with an uppercase letter.",
        "lowercased": "Amount of ground truth mentions that start with a lowercased letter.",
        "non_alpha": "Amount of ground truth mentions that start with a non-alphabetic character.",
        "lowercased_non_named": "Amount of non-named entity ground truth mentions that start with a lowercased letter.",
        "demonym": "Amount of ground truth mentions where the mention text is contained in a list of demonyms.",
        "metonym": "Amount of ground truth mentions where the ground truth entity is not a location but the most popular candidate entity is.",
        "rare": "Amount of ground truth mentions where the ground truth entity is not the most popular candidate entity.",
        "partial_name": "Amount of ground truth mentions where the mention text is only a part of the ground truth entity's name.",
        "unknown": "Amount of ground truth mentions where the ground truth entity is unknown.",
        "unknown_nil": "Amount of ground truth mentions that are unknown because the ground truth entity was not provided in the benchmark or explicitly marked as NIL.",
        "unknown_no_mapping": "Amount of ground truth mentions that are unknown because ELEVANT could not map the annotated entity to a Wikidata entity.",
        "optional": "Amount of ground truth mentions that are marked as optional to annotate.",
        "root": "Amount of ground truth mentions that are the root of a mention, i.e. is the outermost mention of potentially nested (alternative) mentions.",
        "child": "Amount of ground truth mentions that are a child of a mention, i.e. is the innermost mention of potentially nested (alternative) mentions."
    }
}


$("document").ready(function() {
    // JQuery selector variables
    const $benchmark_filter = $("input#benchmark-filter");
    const $evaluation_table_wrapper = $("#evaluation_table_wrapper");
    const $evaluation_table = $("#evaluation_table_wrapper table");

    read_url_parameters();
    reset_selected_cell_categories();

    // Initialize tippy tooltips contained in the html file
    tippy('[data-tippy-content]', {
        appendTo: document.body,
        theme: 'light-border',
        allowHTML: true
    });

    // Set the table filter strings, radio buttons and show-deprecated/compare checkboxes according to the URL parameters
    if (window.url_param_benchmark_filter) $benchmark_filter.val(window.url_param_benchmark_filter);
    if (window.url_param_internal_benchmark_filter) window.internal_benchmark_filter = new RegExp(window.url_param_internal_benchmark_filter, "i");
    if (window.url_param_group_by) $("#show_values_as input:radio[value=" + window.url_param_show_values_as + "]").prop("checked", true);

    // Read the necessary data files ( whitelist types, benchmark articles, benchmark statistics)
    // and build the benchmark statistics table.
    $("#table_loading").addClass("show");

    read_initial_data().then(function() {
        set_up_benchmark_filter_multiselect();
        build_benchmark_statistics_table(true);
    });

    // Filter results by regex in input field #result-regex on key up
    $benchmark_filter.keyup(function() {
        update_multi_select_checkboxes(this);
        update_benchmark_filter($benchmark_filter.val())

        // Update current URL without refreshing the site
        const url = new URL(window.location);
        url.searchParams.set('benchmark_filter', $benchmark_filter.val());
        window.history.replaceState({}, '', url);
    });


    // Highlight all cells in a row belonging to the same mention_type or type or the "all" column or
    // an error category cell on hover
    $evaluation_table_wrapper.on("mouseenter", "td", function() {
        if ($(this).attr('class')) {
            const cls = $(this).attr('class').split(/\s+/)[0];
            const evaluation_category = get_evaluation_category_string(this, true);
            const base_category = (evaluation_category) ? evaluation_category.split("|")[0] : null;
            if (base_category === "text_statistics") {
                // Mark all cells in the corresponding row with the corresponding class
                $(this).closest('tr').find('.' + cls).each(function() {
                    $(this).addClass("hovered");
                });
            } else {
                $(this).addClass("hovered");
            }
        }
    });
    $evaluation_table_wrapper.on("mouseleave", "td", function() {
        if ($(this).attr('class')) {
            const cls = $(this).attr('class').split(/\s+/)[0];
            const evaluation_category = get_evaluation_category_string(this, true);
            const base_category = (evaluation_category) ? evaluation_category.split("|")[0] : null;
            if (base_category === "text_statistics") {
                $(this).closest('tr').find('.' + cls).each(function() {
                    $(this).removeClass("hovered");
                });
            } else {
                $(this).removeClass("hovered");
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
            const evaluation_categories = get_evaluation_category_string(this, false).split("|");
            const category = (evaluation_categories.length >= 2) ? evaluation_categories[1] : "";
            const subcategory = (evaluation_categories.length >= 3) ? evaluation_categories[2] : "";
            const tooltiptext = get_th_tooltip_text(category, subcategory);
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
        if ($benchmark_filter.is(":focus") || $("#article_select").is(":focus")) return;
        if ([39, 37].includes(event.which)) {
            window.all_highlighted_annotations = [[], []];
            window.all_highlighted_annotations[0] = $("#prediction_overview td:nth-child(1) .annotation.beginning").not(".lowlight");
            if (window.selected_experiment_ids.length > 1) {
                window.all_highlighted_annotations[1] = $("#prediction_overview td:nth-child(2) .annotation.beginning").not(".lowlight");
            }
            if (event.ctrlKey && event.which === 39) {
                // Jump to next error highlight
                scroll_to_next_annotation(false);
            } else if (event.ctrlKey && event.which === 37) {
                scroll_to_previous_annotation(false);
            }
        }
    });

    $('#graph_modal').on('hidden.bs.modal', function () {
        // Destroy the current graph when the modal is closed.
        // This is necessary to prevent the graph from switching to a previous version due
        // to hover effects.
        Chart.getChart('graph_canvas').destroy();
    });

    $(".checkbox_menu").on("change", "input[type='checkbox']", function() {
        update_filter_regex_from_checkboxes($(this).closest("ul"));
    });
    $(document).on('click', '.allow-focus', function (e) {
        e.stopPropagation();
    });
});


/**********************************************************************************************************************
 Functions for READING URL PARAMETERS
 *********************************************************************************************************************/

function read_url_parameters() {
    window.url_param_benchmark_filter = get_url_parameter_string(get_url_parameter("benchmark_filter"));
    window.url_param_benchmark = get_url_parameter_string(get_url_parameter("benchmark"));
    window.url_param_article = get_url_parameter_string(get_url_parameter("article"));
    window.url_param_emphasis = get_url_parameter_array(get_url_parameter("emphasis"), false);
    window.url_param_show_columns = get_url_parameter_array(get_url_parameter("show_columns"), false);
    window.url_param_sort_order = get_url_parameter_array(get_url_parameter("sort_order"), true);
    window.url_param_access = get_url_parameter_string(get_url_parameter("access"));
    window.url_param_show_values_as = get_url_parameter_string(get_url_parameter("show_values_as"));
    window.url_param_internal_benchmark_filter = get_url_parameter_string(get_url_parameter("internal_benchmark_filter"));
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
            read_benchmark_statistics()
        );
    });
}

function read_benchmark_statistics() {
    /*
     * Read the benchmark articles of all available benchmark files in the benchmarks directory.
     */
    // Get the names of the benchmark files from the benchmarks directory
    let metadata_filenames = [];
    return $.get("benchmarks", function(folder_data){
        $(folder_data).find("a").each(function() {
            let filename = $(this).attr("href");
            if (filename.endsWith(BENCHMARK_STATISTICS_EXTENSION)) window.benchmark_statistics_filenames.push(filename);
            if (filename.endsWith(BENCHMARK_EXTENSION)) window.benchmark_filenames.push(filename);
            if (filename.endsWith(METADATA_EXTENSION)) metadata_filenames.push(filename);
        });
    }).then(function() {
        // Read all detected benchmark files
        return $.when(
            $.when.apply($, window.benchmark_statistics_filenames.map(function(filename) {
                return $.get("benchmarks/" + filename, function(data) {
                    let benchmark_name = filename.replace(BENCHMARK_STATISTICS_EXTENSION, "");
                    window.benchmark_cases[benchmark_name] = [];
                    let first_line = true;
                    for (let line of data.split("\n")) {
                        if (line.length === 0) break;
                        if (first_line) {
                            // The first line contains the benchmark statistics
                            window.benchmark_statistics[benchmark_name] = JSON.parse(line);
                            first_line = false;
                        } else {
                            // The following lines contain the benchmark ground truth cases
                            window.benchmark_cases[benchmark_name].push(JSON.parse(line));
                        }
                    }
                });
            })),
            // Retrieve benchmarks metadata for table tooltips and the displayed benchmark name
            $.when.apply($, metadata_filenames.map(function (filename) {
                // The metadata only needs to be loaded if a benchmark statistics file exists.
                // Otherwise, the benchmark is not shown in the table.
                let benchmark_name = filename.replace(METADATA_EXTENSION, "");
                let benchmark_statistics_filename = benchmark_name + BENCHMARK_STATISTICS_EXTENSION;
                if (window.benchmark_statistics_filenames.includes(benchmark_statistics_filename)) {
                    return $.getJSON("benchmarks/" + filename, function (metadata) {
                        window.benchmark_metadata[benchmark_name] = metadata;
                    });
                }
                return Promise.resolve(1);
            }))
        );
    });
}

function read_benchmark_article(benchmark_name) {
    /*
     * Read the benchmark articles for the given benchmark name.
     */
    const filename = benchmark_name + BENCHMARK_EXTENSION;
    return $.get("benchmarks/" + filename, function(data) {
        let benchmark = filename.replace(BENCHMARK_EXTENSION, "").replace(".obscured", "");
        window.benchmark_articles[benchmark] = [];
        for (let line of data.split("\n")) {
            if (line.length > 0) window.benchmark_articles[benchmark].push(JSON.parse(line));
        }
    }).fail(function() {
        $("#evaluation_table_wrapper").html("ERROR: No matching benchmark.jsonl file found.");
    });
}

/**********************************************************************************************************************
 Functions for BUILDING THE EVALUATION RESULTS TABLE
 *********************************************************************************************************************/

function build_benchmark_statistics_table(initial_call) {
    /*
     * Build the overview table from the .benchmark_statistics.jsonl files.
     */
    const $table_loading = $("#table_loading");
    $table_loading.addClass("show");

    const $benchmark_table = $("#evaluation_table_wrapper table");

    // Get current sort order
    const current_sort_order = $benchmark_table[0].config.sortList;

    // Remove previous evaluation table content
    $benchmark_table.trigger("destroy", false);
    $("#evaluation_table_wrapper table thead").empty();
    $("#evaluation_table_wrapper table tbody").empty();

    // Reset variables indicating user selections within the table (they'll be set automatically again))
    window.selected_benchmark = null;
    window.selected_row = null;
    window.selected_cell = null;

    // Hide linking results section
    $("#prediction_overview").hide();

    let default_selected_benchmark;
    let default_selected_emphasis;
    if (initial_call) {
        // If URL parameter is set, select experiment according to URL parameter
        default_selected_benchmark = window.url_param_benchmark;
        default_selected_emphasis = window.url_param_emphasis;
    } else {
        default_selected_benchmark = copy(window.selected_benchmark);
        default_selected_emphasis = window.selected_cells.map(function(el) {
            return ($(el).attr('class')) ? $(el).attr('class').split(/\s+/)[1] : null;
        });
    }

    // Add checkboxes for statistics categories. All benchmark statistics should have the same
    // categories, so it doesn't matter which element I choose for the initialization.
    const some_benchmark_statistics = Object.values(window.benchmark_statistics)[0]
    if (initial_call) add_statistics_category_checkboxes(some_benchmark_statistics);
    // Add table header. The evaluation mode does not affect the table headers, so just choose one.
    add_benchmark_table_header(some_benchmark_statistics);
    // Add table body
    add_benchmark_table_body(window.benchmark_statistics);
    // Add tooltips for the experiment and benchmark columns
    add_benchmark_tooltips();

    // Select default rows and cells
    if (default_selected_benchmark) {
        let row = $('#evaluation_table_wrapper table tbody tr').filter(function() {
            return get_benchmark_from_row(this) === default_selected_benchmark;
        });
        if (row.length > 0) {
            if (default_selected_emphasis) {
                let cell = $(row).children("." + default_selected_emphasis);
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

    // Remove the table loading GIF
    $table_loading.removeClass("show");

    // Update the tablesorter. The sort order is automatically adapted from the previous table.
    initialize_table();  // Since the entire tbody is replaced, triggering a simple update or updateAll is not enough

    if (initial_call && window.url_param_sort_order.length > 0) {
        // Use sort order from URL parameter
        $.tablesorter.sortOn( $benchmark_table[0].config, [ window.url_param_sort_order ]);
    } else if (initial_call) {
        // Sort on All - F1 column in descending order when loading the page if no sort order is specified in the URL
        $.tablesorter.sortOn( $benchmark_table[0].config, [[0, 0]]);
    } else {
        // Sort on last sort order when the table is rebuilt
        $.tablesorter.sortOn( $benchmark_table[0].config, current_sort_order);
    }

    set_top_scrollbar_width();
}

function add_statistics_category_checkboxes(json_obj) {
    /*
     * Add checkboxes for showing / hiding columns.
     */
    $.each(json_obj, function(key) {
        const class_name = get_class_name(key);
        // const label = get_checkbox_or_column_title(key, subkey, true);
        const checked = ((class_name === "text_statistics" && window.url_param_show_columns.length === 0) || window.url_param_show_columns.includes(class_name)) ? "checked" : "";
        let checkbox_html = "<span id=\"checkbox_span_" + class_name + "\"><input type=\"checkbox\" id=\"checkbox_" + class_name + "\" onchange=\"on_column_checkbox_change(this, true)\" " + checked + ">";
        checkbox_html += "<label for='checkbox_" + class_name + "'>" + to_title_case(key.replace(/_/g, " ")) + "</label></span>\n";
        $("#statistics_categories").append(checkbox_html);

        // Add tooltip for checkbox
        tippy("#checkbox_span_" + class_name, {
            content: get_th_tooltip_text(class_name, ""),
            allowHTML: true,
            theme: 'light-border',
        });
    });
}

function add_benchmark_table_header(json_obj) {
    /*
     * Add html for the table header.
     */
    let first_row = "<tr><th></th>";
    let second_row = "<tr><th>Benchmark</th>";
    $.each(json_obj, function(key) {
        const class_name = get_class_name(key);
        let colspan = 0;
        if (key === "types") {
            // Only those types that occur in a benchmark are listed in its statistics file. Therefore, get all types
            // from the type whitelist in order to display all types in the table header.
            $.each(window.whitelist_types, function (type) {
                const subclass_name = get_class_name(type);
                const type_name = window.whitelist_types[type];
                const data_string = " data-evaluation_category='" + key + "|" + type + "' ";
                second_row += "<th class='" + class_name + " " + class_name + "-" + subclass_name + "'" + data_string + ">" + to_title_case(type_name.replace(/_/g, " ")) + "</th>";
                colspan += 1;
            });
        } else if (key === "multi_word_statistics") {
            // For multi-word statistics, add a column for each multi-word length, up to 4 and one for >= 5.
            for(let i = 1; i <= 5; i++) {
                let column_title = (i === 1) ? "1 word" : i + " words";
                if (i === 5) column_title = ">= 5 words";
                const subclass_name = get_class_name(column_title);
                const data_string = " data-evaluation_category='" + key + "|" + column_title + "' ";
                second_row += "<th class='" + class_name + " " + class_name + "-" + subclass_name + "'" + data_string + ">" + to_title_case(column_title) + "</th>";
                colspan += 1;
            }
        } else {
            // For other columns, retrieve the columns from the statistics file.
            $.each(json_obj[key], function(subkey) {
                const subclass_name = get_class_name(subkey);
                const data_string = " data-evaluation_category='" + key + "|" + subkey + "' ";
                second_row += "<th class='" + class_name + " " + class_name + "-" + subclass_name + "'" + data_string + ">" + to_title_case(subkey.replace(/_/g, " "))  + "</th>";
                colspan += 1;
            });
        }
        const data_string = " data-evaluation_category='" + key + "' ";
        first_row += "<th colspan=\"" + colspan + "\" class='" + class_name  +  "'" + data_string + ">" + to_title_case(key.replace(/_/g, " "))  + "</th>";
    });
    first_row += "</tr>";
    second_row += "</tr>";
    $('#evaluation_table_wrapper table thead').html(first_row + second_row);

    // Add table header tooltips
    $("#evaluation_table_wrapper th").each(function() {
        const evaluation_categories = get_evaluation_category_string(this, false).split("|");
        const category = (evaluation_categories.length >= 1) ? evaluation_categories[0] : "";
        const subcategory = (evaluation_categories.length >= 2) ? evaluation_categories[1] : "";
        const tooltiptext = get_th_tooltip_text(category, subcategory);
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

function add_benchmark_table_body(benchmark_statistics) {
    /*
     * Add the table bodies.
     * Show / Hide rows and columns according to checkbox state and filter-result input field.
     */
    // Sort benchmark statistics list by benchmark name (as given in metadata)
    const benchmark_name_comparator = (key1, key2) => {
        // Example custom logic: case-insensitive comparison
        const name1 = get_displayed_benchmark_name(key1);
        const name2 = get_displayed_benchmark_name(key2)
        return name1.localeCompare(name2);
    };
    const sorted_keys = Object.keys(benchmark_statistics).sort(benchmark_name_comparator);

    let tbody = "";
    sorted_keys.forEach(function(key) {
        // Get the results for the currently selected evaluation mode.
        let statistics = benchmark_statistics[key];

        // Add the new row to the current tbody
        tbody += get_table_row(key, statistics);
    });
    $('#evaluation_table_wrapper table tbody').append(tbody);

    // Show / Hide columns according to checkbox state
    $("input[id^='checkbox_']").each(function() {
        show_hide_columns(this, false);
    });

    // Show / Hide rows according to filter-result input field
    filter_table_rows();
}

function get_table_row(benchmark, json_obj) {
    /*
     * Get html for the table row with the given benchmark name and statistics.
     */
    let row = "<tr onclick='on_row_click(this)'>";
    let onclick_str = " onclick='on_cell_click(this)'";
    let displayed_benchmark_name = get_displayed_benchmark_name(benchmark);
    row += "<td " + onclick_str + " data-benchmark=\"" + benchmark + "\">" + displayed_benchmark_name + "</td>";
    $.each(json_obj, function(key) {
        if (key === "types") {
            // Add a column for each type
            $.each(window.whitelist_types, function(type) {
                row += get_cell_content(key, type, json_obj);
            });
        } else if (key === "multi_word_statistics") {
            // Add a column for each multi-word length, up to 4
            for (let i=1; i<=4; i++) {
                row += get_cell_content(key, i, json_obj);
            }
            // Add a column for multi-word lengths >= 5
            let sum = 0;
            $.each(json_obj[key], function(subkey) {
                if (subkey >= 5) {
                    sum += json_obj[key][subkey];
                }
            });
            row += get_cell_content(key, ">=5 words", json_obj, sum);
        } else {
            $.each(json_obj[key], function(subkey) {
                row += get_cell_content(key, subkey, json_obj);
            });
        }
    });
    row += "</tr>";
    return row;
}

function get_cell_content(key, subkey, json_obj, value) {
    /*
     * Get the content for each cell in the table.
     */
    const total_labels = json_obj["text_statistics"]["labels"];
    let onclick_str = " onclick='on_cell_click(this)'";
    let class_name = get_class_name(key);
    if (value == null)
        value = (subkey in json_obj[key]) ? json_obj[key][subkey] : 0;
    // If the show percentages radio button is selected, display percentages instead of total values.
    // Text statistics are always displayed as total values.
    if (is_show_percentages() && key !== "text_statistics") {
        let processed_value = "<div class='" + class_name + " tooltip'>";
        let percentage = get_percentage(value, total_labels);
        processed_value += percentage + "%";
        processed_value += "<span class='tooltiptext'>";
        processed_value += value + " / " + total_labels;
        processed_value += "</span></div>";
        value = processed_value;
    }
    let subclass_name = get_class_name(String(subkey));
    let data_string = "data-evaluation_category='" + key + "|" + subkey + "' ";
    return "<td class='" + class_name + " " + class_name + "-" + subclass_name + "' " + data_string + onclick_str + ">" + value + "</td>";
}


function filter_table_rows() {
    /*
     * Filter table rows according to the benchmark filter.
     */
    $("#evaluation_table_wrapper tbody tr").each(function() {
        let benchmark = $(this).children("td:nth-child(1)").text();
        // Filter row according to filter keywords
        const show_row = benchmark.search(window.internal_benchmark_filter) !== -1;
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
    // therefore change the width of the top scrollbar div accordingly
    set_top_scrollbar_width();
}

function on_row_click(el) {
    /*
     * This method is called when a table body row was clicked.
     * This marks the row as selected and reads the evaluation cases.
     */
    // Get a timestamp for the click to help maintain the order in which evaluation cases are loaded
    let timestamp = new Date().getTime();
    window.last_show_article_request_timestamp = timestamp;

    let previous_benchmark = (window.selected_benchmark !== null) ? get_benchmark_from_experiment_id(window.selected_benchmark) : null;
    let new_benchmark = get_benchmark_from_row(el);

    // De-select previously selected row
    $("#evaluation_table_wrapper tbody tr").removeClass("selected");

    // Select new row
    window.selected_row = el;
    window.selected_benchmark = new_benchmark;
    $(el).addClass("selected");

    // Show the loading GIF
    $("#loading").addClass("show");

    // Update current URL without refreshing the site
    const url = new URL(window.location);
    url.searchParams.set('benchmark', window.selected_benchmark);
    window.history.replaceState({}, '', url);

    read_benchmark_article(new_benchmark).then(function() {
        // Reset article select options only if a different benchmark was previously selected
        // or if it has not been initialized yet
        const article_select_val = $("#article_select").val();
        if (previous_benchmark !== new_benchmark || article_select_val == null) set_article_select_options(new_benchmark, article_select_val==null);
        show_article(window.selected_benchmark, timestamp);
    });
}

function on_show_values_as_change(el) {
    // Update current URL without refreshing the site
    const url = new URL(window.location);
    url.searchParams.set('show_values_as', $(el).val());
    window.history.replaceState({}, '', url);

    // Re-build the overview table over all .eval_results.json-files from the evaluation-results folder.
    build_benchmark_statistics_table(false);
}

function on_cell_click(el) {
    /*
     * Highlight error category / type cells on click and un-highlight previously clicked cell.
     * Add or remove error categories and types to/from current selection.
     */
    // Determine whether an already selected cell has been clicked
    if (window.selected_cell !== null) {
        // Remove selected class for currently selected cells
        remove_selected_classes(window.selected_cell);
        window.selected_cell = null;
        window.selected_cell_category = null;
    }

    // Make new selection
    const evaluation_categories = get_evaluation_category_string(el, true);
    const category = (evaluation_categories) ? evaluation_categories.split("|")[0] : null;
    if (category === "text_statistics") {
        // Mark all cells belonging to the same column as selected
        const classes = $(el).attr('class').split(/\s+/);
        $(el).closest('tr').find('.' + classes[0]).each(function() {
            $(this).addClass("selected");
        });
        window.selected_cell = el;
    } else {
        // Mark just the clicked cell as selected
        $(el).addClass("selected");
        window.selected_cell = el;
    }

    // Updated selected cell category
    window.selected_cell_category = evaluation_categories;

    // Update current URL without refreshing the site
    const url = new URL(window.location);
    const url_param = ($(window.selected_cell).attr('class')) ? $(window.selected_cell).attr('class').split(/\s+/)[1] : null;
    url.searchParams.set('emphasis', url_param);
    window.history.replaceState({}, '', url);
}


/**********************************************************************************************************************
 Functions for ARTICLE SELECTION
 *********************************************************************************************************************/

function on_article_select() {
    const timestamp = new Date().getTime();
    window.last_show_article_request_timestamp = timestamp;
    show_article(window.selected_benchmark, timestamp);

    // Update current URL without refreshing the site
    const url = new URL(window.location);
    url.searchParams.set('article', $("#article_select option:selected").text());
    window.history.replaceState({}, '', url);
}

/**********************************************************************************************************************
 Functions for DISPLAYING BENCHMARK ARTICLES
 *********************************************************************************************************************/

async function show_article(benchmark, timestamp) {
    /*
     * Show the benchmark article and its annotations for the given benchmark
     */
    reset_annotation_selection();

    console.log("show_article() called for benchmark ", benchmark);

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
    let column_headers = $("#prediction_overview thead tr:nth-child(2) th");
    let column_idx = 0;

    if (!benchmark || !benchmark in window.benchmark_cases || window.benchmark_cases[benchmark].length === 0) {
        $(column_headers[column_idx]).text("");
        for (let i=1; i<columns.length; i++) {
            hide_table_column("prediction_overview", i);
        }
        $(columns[column_idx]).html("<b class='warning'>No experiment selected in the evaluation results table.</b>");
        return;
    }

    // Show benchmark articles
    show_annotated_text(benchmark, $(columns[column_idx]), window.selected_cell_category, selected_article_index, false);
    let benchmark_name = get_displayed_benchmark_name(benchmark);
    let emphasis_str = " (emphasis: \"" + window.selected_cell_category.replace(/_/g, " ").toLowerCase() + "\")";
    $(column_headers[column_idx]).html(benchmark_name + "<span class='nonbold'>  " + emphasis_str + "</span>");
    show_table_column("prediction_overview", column_idx);

    // Set column width
    let width_percentage = 100 / column_idx;
    $("#prediction_overview th, #prediction_overview td").css("width", width_percentage + "%");

    // Hide the loading GIF
    if (timestamp >= window.last_show_article_request_timestamp) $("#loading").removeClass("show");
}

function show_annotated_text(benchmark, textfield, selected_cell_category, article_index, example_modal) {
    /*
     * Generate annotations and tooltips for predicted and ground truth mentions of the selected experiment
     * and article and show them in the textfield.
     */
    const articles = (example_modal) ? window.articles_example_benchmark : window.benchmark_articles[benchmark];
    let annotated_text = "";
    const highlight_mode = (example_modal) ? "errors" : get_highlight_mode();
    if (window.is_show_all_articles && !example_modal) {
        let annotated_texts = [];
        for (let i=0; i < articles.length; i++) {
            let annotations = get_annotations(i, benchmark);
            annotated_texts.push(annotate_text(articles[i].text,
                annotations,
                articles[i].hyperlinks,
                articles[i].evaluation_span,
                selected_cell_category,
                highlight_mode));
        }

        for (let i=0; i < annotated_texts.length; i++) {
            if (i !== 0) annotated_text += "<hr/>";
            if (articles[i].title) annotated_text += "<b>" + articles[i].title + "</b><br>";
            annotated_text += annotated_texts[i];
        }
    } else {
        let curr_article = articles[article_index];
        let annotations = get_annotations(article_index, benchmark);
        annotated_text = annotate_text(curr_article.text,
            annotations,
            curr_article.hyperlinks,
            [0, curr_article.text.length],
            selected_cell_category,
            highlight_mode);
    }
    textfield.html(annotated_text);
}

function get_annotations(article_index, benchmark) {
    /*
     * Generate annotations for the benchmark article.
     *
     * This method first combines the predictions outside the evaluation span (from file <experiment_id>.linked_articles.jsonl)
     * with the evaluated predictions inside the evaluation span (from file <experiment_id>.eval_cases.jsonl),
     * and then generates annotations for all of them.
     */
    let benchmark_cases = window.benchmark_cases[benchmark][article_index];

    // Build label ID to label mapping
    let label_id_to_label = {};
    for (let benchmark_case of benchmark_cases) {
        label_id_to_label[benchmark_case.groundtruth_label.id] = benchmark_case.groundtruth_label;
    }

    // Get all root labels that have child labels so they can be highlighted when the child table cell is selected
    window.root_parent_annotation_ids = {};

    // list with tooltip information for each mention
    let annotations = {};
    let annotation_count = 0;
    for (let benchmark_case of benchmark_cases) {
        // CAREFUL! Parent could be 0, so check for null or undefined with != null
        if (benchmark_case.groundtruth_label.parent != null) {
            // Do not display overlapping GT labels, only display root labels, not child labels.
            continue;
        }
        let annotation = {
            "span": benchmark_case.span,
            "mention_type": benchmark_case.mention_type.toLowerCase(),
            "entity_types": benchmark_case.types,
            "tags": benchmark_case.tags.map(function (tag) {
                return tag.toLowerCase()
            }),
            "mention_word_count": benchmark_case.mention_word_count,
            "beginning": true,
            "alternative_annotations": [],
            "entity_id": benchmark_case.groundtruth_label.entity_id,
            "entity_name": benchmark_case.groundtruth_label.name
        };
        if (benchmark_case.tags.includes("OPTIONAL")) {
            annotation.class = ANNOTATION_CLASS_OPTIONAL;
        } else if (benchmark_case.tags.includes("UNKNOWN")) {
            annotation.class = ANNOTATION_CLASS_UNKNOWN;
        } else {
            annotation.class = ANNOTATION_CLASS_NORMAL;
        }

        // Get alternative ground truth mention texts:
        if (benchmark_case.groundtruth_label.children) {
            for (let child_id of benchmark_case.groundtruth_label.children) {
                const child = label_id_to_label[child_id];
                let alt = {}
                alt.text = window.benchmark_articles[benchmark][article_index].text.substring(child.span[0], child.span[1]);
                alt.entity_id = child.entity_id;
                alt.entity_name = child.name;
                annotation.alternative_annotations.push(alt);
            }
        }

        annotation.id = article_index + "_" + annotation_count;
        annotation_count++;
        annotations[benchmark_case.span] = annotation;

        if (benchmark_case.groundtruth_label.children != null && benchmark_case.groundtruth_label.children.length > 0) {
            window.root_parent_annotation_ids[annotation.id] = true;
        }
    }

    // Sort the annotations by span start
    const keys = Object.keys(annotations);
    keys.sort((a, b) => {
        const [a1] = a.split(',').map(Number);
        const [b1] = b.split(',').map(Number);
        return a1 - b1;
    });
    let sorted_annotations = [];
    keys.forEach(key => {
        sorted_annotations.push(annotations[key]);
    });
    return sorted_annotations;
}

function generate_annotation_html(snippet, annotation, selected_cell_category, highlight_mode) {
    /*
     * Generate html snippet for a given annotation. A hyperlink is also regarded as an annotation
     * and can be identified by the property "hyperlink". Inner annotations, e.g. hyperlinks contained in
     * a mention annotation, nested mention annotations are contained given by the property "inner_annotation".
     */
    let inner_annotation = snippet;

    if ("inner_annotation" in annotation) {
        inner_annotation = generate_annotation_html(snippet, annotation.inner_annotation, selected_cell_category, highlight_mode);
    }

    if ("hyperlink" in annotation) {
        return "<a href=\"https://en.wikipedia.org/wiki/" + annotation.hyperlink + "\" target=\"_blank\">" + inner_annotation + "</a>";
    }

    // Add tooltip
    let tooltip_classes = "tooltiptext below";
    let tooltip_header_text = "";
    let tooltip_case_type_html = "";
    let tooltip_body_text = "";
    let tooltip_footer_html = "";
    if (annotation.class === ANNOTATION_CLASS_NORMAL) {
        const entity_link = get_entity_link(annotation.entity_id);
        let entity_name;
        if (annotation.entity_name != null) {
            entity_name = (["Unknown", "null"].includes(annotation.entity_name)) ? MISSING_LABEL_TEXT : annotation.entity_name;
            entity_name = entity_name + " (" + entity_link + ")";
        } else {
            entity_name = entity_link;
        }
        tooltip_header_text += entity_name;
    } else  if (annotation.class === ANNOTATION_CLASS_OPTIONAL || annotation.class === ANNOTATION_CLASS_UNKNOWN) {
        if (NO_LABEL_ENTITY_IDS.includes(annotation.entity_id)) {
            // For Datetimes, Quantities and Unknown GT entities don't display "Label (QID)"
            // instead display "[DATETIME]"/"[QUANTITY]" or "[UNKNOWN]"
            let entity_name = "[" + annotation.entity_id + "]";
            if (annotation.entity_id === UNKNOWN_ENTITY_NIL) {
                entity_name = window.NIL_TEXT;
            } else if (annotation.entity_id === UNKNOWN_ENTITY_NO_MAPPING) {
                entity_name = window.NO_MAPPING_TEXT;
            }
            tooltip_header_text += "Groundtruth: " + entity_name;
        } else {
            let entity_name = (annotation.gt_entity_name === "Unknown") ? MISSING_LABEL_TEXT : annotation.gt_entity_name;
            const entity_link = get_entity_link(annotation.entity_id);
            tooltip_header_text += "Groundtruth: " + entity_name + " (" + entity_link + ")";
        }
        if (annotation.class === ANNOTATION_CLASS_OPTIONAL) tooltip_body_text += "Note: Detection is optional<br>";
        if (annotation.class === ANNOTATION_CLASS_UNKNOWN) tooltip_body_text += "Note: Entity not found in the knowledge base<br>";
    }
    if (ANNOTATION_CLASS_UNKNOWN !== annotation.class) {
        const type_string = $.map(annotation.entity_types, function(qid){ return get_type_label(qid) }).join(", ");
        tooltip_body_text += "<b>Type(s):</b> " + type_string + "<br>";
    }
    tooltip_body_text += "<b>Mention type:</b> " + to_title_case(annotation.mention_type.replace(/_/g, " ")) + "<br>";
    // Add case type boxes and annotation case type class to tooltip
    tooltip_classes += " " + annotation.class;

    if (annotation.alternative_annotations.length > 0) {
        tooltip_body_text += "<b>Alternative annotations:</b><br>";
        for (const alt of annotation.alternative_annotations) {
            tooltip_body_text += "\"" + alt.text + "\" (" + get_entity_link(alt.entity_id) + ")<br>";
        }
    }
    // Add tags
    if (annotation.tags.length > 0) {
        for (let t = 0; t < annotation.tags.length; t += 1) {
            let tag = annotation.tags[t];
            tag = tag.replace(/_/g, " ").toLowerCase();
            if (t > 0) {
                tooltip_footer_html += " ";
            }
            tooltip_footer_html += "<span class=\"error_category_tag\">" + tag + "</span>";
        }
    }

    // Use transparent version of the color, if an error category or type is selected
    // and the current annotation does not have a corresponding error category or type label
    let lowlight_mention = true;
    const evaluation_category_tags = get_evaluation_category_tags(selected_cell_category);
    const evaluation_categories = selected_cell_category.split("|");
    const category = evaluation_categories[0];
    const subcategory = evaluation_categories[1];
    for (const tag of evaluation_category_tags) {
        if (category === "types") {
            if (annotation.entity_types.includes(tag)) {
                // The annotation has the selected entity type
                lowlight_mention = false;
                break;
            }
        } else if (category === "multi_word_statistics") {
            if (annotation.mention_word_count == tag || (annotation.mention_word_count >= 5 && tag === ">=5 words")) {
                // The annotation has the selected mention word count length
                lowlight_mention = false;
                break;
            }
        } else if (category === "tags" && subcategory === "child") {
            if (annotation.id in window.root_parent_annotation_ids) {
                // The annotation is a root parent annotation and should be highlighted
                lowlight_mention = false;
                break;
            }
        } else {
            if (annotation.tags.includes(tag) || annotation.mention_type === tag || category === "text_statistics") {
                // The annotation has the selected tag or mention type or all mentions should be highlighted
                // because the text_statistics column was selected.
                lowlight_mention = false;
                break;
            }
        }
    }

    const lowlight = (lowlight_mention) ? " lowlight" : "";

    const beginning = (annotation.beginning) ? " beginning" : "";
    // Annotation id is a class because several spans can belong to the same annotation.
    const annotation_id_class = " annotation_id_" + annotation.id;
    let replacement = "<span class=\"annotation gt " + annotation.class + lowlight + beginning + annotation_id_class + "\">";
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



/**********************************************************************************************************************
 Functions for MULTISELECT DROPDOWN
 *********************************************************************************************************************/

function set_up_benchmark_filter_multiselect() {
    /*
     * Add experiment and benchmark checkboxes to the experiment and benchmark
     * dropdown multi-select.
     */
    // Iterate over all keys from the benchmark statistics and add them to the benchmark_names set
    let benchmark_names = new Set();
    for (let benchmark in window.benchmark_statistics) {
        const benchmark_name = get_displayed_benchmark_name(benchmark);
        benchmark_names.add(benchmark_name);
    }
    benchmark_names = Array.from(benchmark_names).sort();

    for (let benchmark_name of benchmark_names) {
        const checked = (benchmark_name.search(window.internal_benchmark_filter) !== -1) ? "checked" : "";
        const option = "<li><label><input type=\"checkbox\" value='" + benchmark_name + "' " + checked + ">" + benchmark_name + "</label></li>";
        $("#benchmark_select").append(option);
    }
}


/**********************************************************************************************************************
 Functions for CREATING GRAPHS
 *********************************************************************************************************************/

function get_graph_selectable_th(table_header_clone) {
    return table_header_clone.find("table tr:nth-child(2) th:not(:eq(0))");
}

function on_graph_selectable_click(el) {
    const classes = $(el).attr('class').split(/\s+/);
    if (classes.includes("graph_selectable_col-selected")) {
        $(el).removeClass("graph_selectable_col-selected");
    } else {
        $(el).addClass("graph_selectable_col-selected");
    }
}

function show_graph() {
    /*
     * Create a graph for the current table and display it in a modal.
     */
    // Get the selected column indices
    const $table_header_clone = $("#table_header_clone");
    let selected_col_indices = [];
    $table_header_clone.find(".graph_selectable_col-selected").each(function() {
        const index = $($(this).parent().children(":not([style*=\"display: none\"])")).index(this);
        selected_col_indices.push(index);
    });

    // Remove the overlay and the fake table header
    graph_mode_off();

    // Create graph
    create_graph(selected_col_indices);

    // Display the graph modal
    $('#graph_modal').modal('show');
}

function create_graph(y_columns) {
    /*
     * Create a graph from the currently displayed table with values from the given table column.
     */
    const $warning_paragraph = $("#graph_modal .warning");
    const $canvas = $("#graph_canvas");
    const $download_button = $("#download_graph");
    const $download_tsv_button = $("#download_graph_tsv");

    // Show a warning instead of the canvas if no columns were selected
    if (y_columns.length === 0) {
        $warning_paragraph.show();
        $canvas.hide();
        $download_button.prop("disabled",true);
        $download_tsv_button.prop("disabled",true);
        $warning_paragraph.html("<b>No columns selected. Please select at least one column.</b>");
        return;
    }

    // Reset the modal components
    $canvas.show();
    $warning_paragraph.hide();
    $download_button.prop("disabled",false);
    $download_tsv_button.prop("disabled",false);

    let colors = ["gold", "crimson", "royalblue", "orange", "yellowgreen", "purple", "teal", "fuchsia", "turquoise", "indigo"];
    if ("graph_colors" in config) colors = config["graph_colors"];

    let table_contents = get_table_contents(true, false, true)
    console.log(table_contents);

    // Get the unique x-values
    let x_values = [];
    for (let y_column of y_columns) {
        console.log(y_column, table_contents[1][y_column])
        x_values.push(table_contents[1][y_column][0]);
    }
    console.log(x_values)

    // Show a warning instead of the canvas if more lines are to be drawn than colors exist.
    // This is mostly to prevent the legend from overlapping with the graph and the graph looking all weird.
    if (x_values.length > colors.length) {
        $warning_paragraph.show();
        $canvas.hide();
        $download_button.prop("disabled",true);
        $download_tsv_button.prop("disabled",true);
        $warning_paragraph.html("<b>Too many distinct benchmarks. Adjust your table by filtering out rows.</b>");
        return;
    }

    // Get the y-values and other properties for each line of the graph
    let datasets = []
    for (let i = 0; i < table_contents.length; i++) {
        // Skip the header lines
        if (i < 2) continue;

        const row = table_contents[i];
        let dict = {};
        dict["borderColor"] = colors[i];
        dict["pointBackgroundColor"] = colors[i];
        dict["pointBorderWidth"] = 4;
        dict["borderWidth"] = 4;
        dict["fill"] = false;
        dict["lineTension"] = 0;
        dict["label"] = row[0][0];
        console.log(row[0][0])
        // Get y-values
        let y_values = [];
        for (let y_column of y_columns) {
            y_values.push(parseFloat(row[y_column][0]));
        }
        console.log(y_values);
        dict["data"] = y_values;
        datasets.push(dict);
    }

    // Set the default font size for labels within the graph. This can still be changed
    // for individual items such as the legend or specific scales, see
    // https://www.chartjs.org/docs/latest/general/fonts.html
    if ("graph_font_size" in window.config) Chart.defaults.font.size = window.config["graph_font_size"];

    const y_axis_label = (table_contents[2][y_columns[0]][0].includes("%")) ? "in %" : "";
    new Chart("graph_canvas", {
        type: "line",
        data: {
            labels: x_values,
            datasets
        },
        options: {
            // maintainAspectRatio: false,
            plugins: {
                // title: {display: true, text: 'Overall F1'},
                legend: {
                    // position: 'bottom',
                    display: true,
                    labels: {
                        boxWidth: 10,
                        generateLabels: function(chart) {
                            let labels = Chart.defaults.plugins.legend.labels.generateLabels(chart);
                            for (let key in labels) {
                                labels[key].fillStyle  = labels[key].strokeStyle;
                            }
                            return labels;
                        }
                    }
                }
            },
            animation: {
                duration: 500
            },
            scales: {
                x: {
                    ticks: {
                        autoSkip: false,
                        // maxRotation: 90,
                        // minRotation: 90
                    },
                    grid: {
                        display: false,
                        drawBorder: false,
                        drawOnChartArea: false,
                        drawTicks: true,
                    }
                },
                y: {
                    min: 0,
                    max: 100,
                    title: {
                        display: true,
                        text: y_axis_label
                    }
                }
            }
        }
    });
}

/**********************************************************************************************************************
 Functions for MINI UTILS
 *********************************************************************************************************************/

function get_th_tooltip_text(key, subkey) {
    /*
     * Get the tooltip text (including html) for the table header cell specified by the
     * given evaluation results key and subkey.
     */
    if (!key) return "";
    if (key.toLowerCase() in HEADER_DESCRIPTIONS) {
        key = key.toLowerCase();
        if (!subkey) {
            // Get tooltip texts for multi-column headers
            return HEADER_DESCRIPTIONS[key][""];
        }

        if (key === "types") {
            // Get tooltip text for specific types
            const type = (subkey in window.whitelist_types) ? window.whitelist_types[subkey] : "Other";
            return "Amount of ground truth entities of type \"" + type + "\".";
        }

        subkey = subkey.toLowerCase();
        if (subkey in HEADER_DESCRIPTIONS[key]) {
            // Get tooltip text for remaining header columns
            let tooltip_text = HEADER_DESCRIPTIONS[key][subkey];
            return tooltip_text;
        }
    }
    return "";
}

function get_evaluation_category_tags(evaluation_category_string) {
    /*
     * For a given cell return the error category, entity type or mention type tag.
     */
    if (evaluation_category_string) {
        const evaluation_categories = evaluation_category_string.split("|");
        const category = evaluation_categories[0];
        const subcategory = evaluation_categories[1];
        if (category === "text_statistics") {
            return ["text_statistics"];
        } else {
            return [subcategory];
        }
    }
    return ["text_statistics"];
}

function get_displayed_benchmark_name(benchmark) {
    /*
     * Get the benchmark name that should be displayed in the benchmark table column.
     */
    benchmark = benchmark.replace(BENCHMARK_STATISTICS_EXTENSION, "");
    let metadata_benchmark_name = (benchmark in window.benchmark_metadata) ? window.benchmark_metadata[benchmark].name : null;
    return (metadata_benchmark_name) ? metadata_benchmark_name : benchmark;
}

function is_show_percentages() {
    return $("#radio_show_values_as_percentages").is(":checked");
}

function get_percentage(numerator, denominator) {
    if (denominator === 0) return 0.00;
    return (numerator / denominator * 100).toFixed(2);
}

function get_benchmark_from_row(row) {
    return $(row).find('td:nth-child(1)').data("benchmark");
}
