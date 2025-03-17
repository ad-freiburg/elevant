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
        theme: 'light-border',
        allowHTML: true
    });

    // Set the table filter strings, radio buttons and show-deprecated/compare checkboxes according to the URL parameters
    if (window.url_param_experiment_filter) $experiment_filter.val(window.url_param_experiment_filter);
    if (window.url_param_benchmark_filter) $benchmark_filter.val(window.url_param_benchmark_filter);
    if (window.url_param_internal_experiment_filter) window.internal_experiment_filter = new RegExp(window.url_param_internal_experiment_filter, "i");
    if (window.url_param_internal_benchmark_filter) window.internal_benchmark_filter = new RegExp(window.url_param_internal_benchmark_filter, "i");
    if (window.url_param_group_by) $("#group_by input:radio[value=" + window.url_param_group_by + "]").prop("checked", true);
    if (window.url_param_highlight_mode) $("#highlight_modes input:radio[value=" + window.url_param_highlight_mode + "]").prop("checked", true);
    $("#checkbox_deprecated").prop('checked', window.url_param_show_deprecated);
    $("#checkbox_compare").prop('checked', window.url_param_compare);

    // Read the necessary data files (config, whitelist types, benchmark articles, evaluation results)
    // and build the evaluation results table.
    $("#table_loading").addClass("show");
    read_initial_data().then(function() {
        set_up_table_filter_multiselects();
        build_evaluation_results_table(true);
    });

    // Filter table rows by regex in input field (from SPARQL AC evaluation) on key up
    $experiment_filter.keyup(function() {
        update_multi_select_checkboxes(this);
        update_experiment_filter($experiment_filter.val())

        // Update current URL without refreshing the site
        const url = new URL(window.location);
        url.searchParams.set('experiment_filter', $experiment_filter.val());
        window.history.replaceState({}, '', url);
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
            if (base_category === "mention_types" || base_category === "entity_types" || cls === "all") {
                // Mark all cells in the corresponding row with the corresponding class
                $(this).closest('tr').find('.' + cls).each(function() {
                    $(this).addClass("hovered");
                });
            } else if (base_category === "error_categories") {
                $(this).addClass("hovered");
            }
        }
    });
    $evaluation_table_wrapper.on("mouseleave", "td", function() {
        if ($(this).attr('class')) {
            const cls = $(this).attr('class').split(/\s+/)[0];
            const evaluation_category = get_evaluation_category_string(this, true);
            const base_category = (evaluation_category) ? evaluation_category.split("|")[0] : null;
            if (base_category === "mention_types" || base_category === "entity_types" || cls === "all") {
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
        if ($experiment_filter.is(":focus") || $benchmark_filter.is(":focus") || $("#article_select").is(":focus")) return;
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