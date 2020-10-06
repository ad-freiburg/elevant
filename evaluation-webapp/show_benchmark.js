var articles = [];

$("document").ready(function() {
    textfield_left = document.getElementById("textfield_left");
    textfield_right = document.getElementById("textfield_right");
    article_select = document.getElementById("article");

    parse_benchmark();
});

function parse_benchmark() {
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
                        entity_representation = entity_text + " [" + entity_id + "]"
                        link = "<a href=\"" + wikidata_url + "\">" + entity_representation +"</a>"
                        labelled_text = before + link + after
                    }
                    labelled_text = labelled_text.replaceAll("\n", "<br>");
                    json.labelled_text = labelled_text;
                    articles.push(json);
                }
            }
            set_article_select_options();
            show_article();
        }
    );
}

function set_article_select_options() {
    for (ai in articles) {
        article = articles[ai];
        var option = document.createElement("option");
        option.text = article.title;
        option.value = ai;
        article_select.add(option);
    }
}

function show_article() {
    index = article_select.value;
    textfield_left.innerHTML = articles[index].labelled_text;
    textfield_right.innerHTML = articles[index].labelled_text;
}
