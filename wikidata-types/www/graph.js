// URL of the SPARQL endpoint (used to obtain graph data as well as for
// autocompletion).
var sparql_endpoint_url = "https://qlever.informatik.uni-freiburg.de/api/wikidata-types";

document.addEventListener("DOMContentLoaded", function(event) { 
  console.log("At your service ...");

  // Autocompletion to Wikidata entities (toy version).
  autocomplete(document.getElementById("entity_input"));

  // If URL with #..., interpret hash as entity IRI and build graph for that.
  if (window.location.hash) {
    const entity_iri = "wd:" + window.location.hash.substr(1);
    buildGraph(entity_iri);
  }

});


// Get graph from QLever and build it.
async function buildGraph(entity_iri) {
  console.log("Building graph for entity:", entity_iri);
  document.querySelector("#title").innerHTML =
    "Show Wikidata Types subgraph for " + entity_iri;
  getGraphFromQlever(entity_iri)
    .then(graph => drawGraph(graph))
    .catch(error => console.log("ERROR:", error));
}


// Obtain graph for given IRI (QLever query + turn result into graph).
async function getGraphFromQlever(entity_iri) {
  // URL for QLever query (for now: fixed subject Q937 = Albert Einstein).
  const subclass_only = false;
  var predicate_path = subclass_only ? "wdt:P279+" : "wdt:P31/wdt:P279*"; 
  var first_predicate = subclass_only ? "wdt:P279" : "wdt:P31";
  var sparql_query = 
    "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>" +
    "PREFIX wikibase: <http://wikiba.se/ontology#>" +
    "PREFIX wdt: <http://www.wikidata.org/prop/direct/>" +
    "PREFIX wd: <http://www.wikidata.org/entity/>" +
    "SELECT DISTINCT ?s ?p ?o ?s_name ?o_name ?s_score ?o_score WHERE {" +
    "  ?s wikibase:sitelinks ?s_score ." +
    "  ?o wikibase:sitelinks ?o_score ." +
    "  ?s rdfs:label ?s_name ." +
    "  ?o rdfs:label ?o_name ." +
    "  { VALUES ?s { " + entity_iri + " } VALUES ?p { " + first_predicate + " } ?s ?p ?o }" +
    "  UNION" +
    "  { " + entity_iri + " " + predicate_path + " ?s . VALUES ?p { wdt:P279 } ?s ?p ?o }" +
    "}" +
    "ORDER BY DESC(?s_score)";
  var url = sparql_endpoint_url + "?query=" + encodeURIComponent(sparql_query);

  console.log(url);

  // Get result JSON from QLever
  const response = await fetch(url);
  const result = await response.json();

  // Turn JSON into an object with "nodes", "edges", and "labels" like in the
  // toy example.
  // console.log(qlever_result);
  console.log("QLever result size:", result.resultsize);
  var nodes = {};
  var edges = [];
  result.res.forEach(row => {
    var source_node = { "id": row[0], "label": row[3], "score": row[5] };
    var target_node = { "id": row[2], "label": row[4], "score": row[6] };
    var edge_type = row[1].replace(/<.*\/(.*)>/, "$1");
    // Add node.
    [source_node, target_node].forEach((node, i) => {
      node.id = node.id.replace(/<.*\/(.*)>/, "$1");
      node.label = node.label.replace(/^"(.*)"@en$/, "$1");
      node.score = +node.score.replace(/^"(\d+)".*$/g, "$1");
      node.type = (i == 0 && edge_type == "P31" ? "source" : "other");
      nodes[node.id] = node;
    });
    // Add edge.
    edges.push({ "source": source_node.id,
                 "target": target_node.id,
                 "target_score": target_node.score,
                 "type": edge_type });
  });
  nodes = Object.values(nodes);
  // console.log("Nodes:", nodes);
  // console.log("Edges:", edges);
  return { "nodes": nodes, "edges": edges };
}

function drawGraph(data) {

  // Show the data.
  console.log("GRAPH:", data);
  var div_style = window.getComputedStyle(document.getElementById("graph_div"));
  // var div_width = div_style.getPropertyValue("width");
  // var div_height = div_style.getPropertyValue("height");
  var div_width = document.getElementById("graph_div").offsetWidth;
  var div_height = document.getElementById("graph_div").offsetHeight;
  console.log("DIV dimensions:", div_width, "x", div_height);

  // Setup D3 (remove all from previous).
  var svg = d3.select("#graph");
  svg.selectAll("*").remove();
  svg.attr("width", div_width);
  svg.attr("height", div_height);
  var width = +svg.attr("width");
  var height = +svg.attr("height");
  console.log("SVG dimensions:", width, "x", height);

  // Setup zoom (which includes panning).
  // Learned from https://www.d3indepth.com/zoom-and-pan
  var zoom = d3.zoom()
               // .scaleExtent([1, 3])
               // .translateExtent([[-0.5 * width, -0.5 * height],
	       // 	           [+1.5 * width, +1.5 * height]])
               .on("zoom", event => svg.selectAll("g").attr("transform", event.transform));
  svg.call(zoom);

  // Clipping.
  // svg.append("defs").append("clipPath").attr("id", "clip")
  //    .append("rect").attr("x", 0).attr("y", 0)
  //                   .attr("width", width).attr("height", height);
  // svg.append("g").attr("clip-path", "url(#clip)");

  // Style configuration.
  var node_radius = score => 7 + Math.log(1 + score);
  var node_border = 3;
  var node_density = Math.sqrt(data.nodes.length / (width * height));
  var node_charge = -0.9 / node_density;  // For force-based graph layout.
  var node_dist = 50;
  var edge_width = 1;
  var label_font_size = 12;
  var label_color = "black";
  var label_max_length = 20;
  var node_width = label_max_length * label_font_size / 2;
  var node_height = 1.2 * label_font_size;
  var edge_color = { "P31": "darkred", "P279": "darkblue" };
  var node_color = { "source": "darkred", "other": "orange" };

  // Arrow head style. In the path command, 20 is the length, 10 is the width,
  // and 5 is half of the width.
  var arrow_head_length = 12;
  var arrow_head_width = 6;
  var arrow_head_path = "M 0 0"
    + " " + arrow_head_width / 2  + "  " + arrow_head_width / 2
    + " 0 " + arrow_head_width
    + " " + arrow_head_length + " " + arrow_head_width / 2;
  // var arrow_head_path = "M 0 0 5 5 0 10 20 5";

  // Add arrowhead to SVG and return URL for use in "line" with
  // .attr("marker-end", <string returned by this function>)
  //
  // Here is an explanation of how the arrow head is drawn:
  //
  // 1. We are using this as the end marker of a line. For the following
  // comments, assume that the line goes horizontally from left to right.
  //
  // 2. The end marker is a box positioned to the right and downwards of
  // the right endpoint of the line. In absolute coordinates, we should
  // therefore draw an arrow pointing right.
  //
  // 3. A positive refX value moves the marker towards the left (inside
  // of the line). A positive refY value moves the marker upwards. That is, the
  // ref values are oriented in exactly the opposite direction as the marker
  // box.
  //
  // TODO: What is the relevance of markerWidth and markerHeight?
  // TODO: What is the relevance of viewBox
  // TODO: What is the relevant of xoverflow visible?
  function arrow_head(color, target_node_radius) {
    // console.log("ARROW HEAD:", color, target_node_radius);
    // Id for this marker.
    var marker_id = "arrowhead_" + color.replace(/^#/, "")
                                 + "_" + target_node_radius.toString();
    // Add marker.
    svg.append("defs").append("marker")
      .attr("id", marker_id)
      .attr("refX", target_node_radius + arrow_head_length)
      .attr("refY", arrow_head_width / 2)
      .attr("markerWidth", 50)
      .attr("markerHeight", 50)
      .attr("orient", "auto")
      .append("path")
      // .attr("viewBox", "-0 -5 10 10")
      // .attr("xoverflow", "visible")
      .attr("d", arrow_head_path)
      .style("fill", color)
      .style("stroke-width", "0");
    return "url(#" + marker_id + ")";
  }

  // NOTE: The append("g") in the following adds all selected (or newly entered)
  // elements to the same "group". TOOD: not quite sure yet what that means.

  // Draw nodes and edges (at no particular position yet = upper left corner).
  // 
  // NOTE: Edges first, so that the node circle are draw on top of the edge
  // lines (which conect the node centers).
  var edges = svg.append("g").selectAll("line")
                 .data(data.edges).enter().append("line")
                 .style("stroke", d => edge_color[d.type])
                 .style("stroke-width", edge_width)
                 .attr("marker-end", d => 
		   arrow_head(edge_color[d.type], node_radius(d.target_score)));
  // var nodes = svg.append("g").selectAll("rect")
  //                .data(data.nodes).enter().append("rect")
  //                .attr("width", node_width)
  //                .attr("height", node_height)
  //                .style("fill", node_color)
  //                .attr("stroke", "white").attr("stroke-width", node_border);
  var nodes = svg.append("g").selectAll("circle")
                 .data(data.nodes).enter().append("circle")
                 .attr("r", d => node_radius(d.score))
                 .style("fill", d => node_color[d.type])
                 .attr("stroke", "white").attr("stroke-width", node_border)
                 .attr("cx", width / 2).attr("cy", height / 2);

  // Node labels.
  var labels = svg.append("g").selectAll("text")
                  .data(data.nodes).enter().append("text")
                  .text(d => abbrv(d.label))
                  .attr("class", "node_label")
                  .style("text-anchor", "left") // "middle"
                  .on("click", (event, d) =>
		    window.open("https://www.wikidata.org/wiki/" + d.id, "_blank"));
  nodes.append("title").text(d => d.score);  // Tooltip with score.
  labels.append("title").text(d => d.label + " (" + d.id + ")");  // Tooltip with full name and id.

  // Abbreviation function
  function abbrv(label) {
    return label.length <= label_max_length
      ? label : label.substring(0, label_max_length - 3) + "...";
  }

  // Setup force simulation.
  var simulation = d3.forceSimulation(data.nodes)
      .force("link", d3.forceLink().distance(node_dist)
	               .id(d => d.id).links(data.edges))
      .force("charge", d3.forceManyBody().strength(node_charge))
      .force("center", d3.forceCenter(width / 2, height / 2));

  // Start simulation?
  simulation.nodes(data.nodes);

  // The "ticked" function from the "on" above.
  simulation.on("tick", () => {
    edges.attr("x1", d => d.source.x)
         .attr("y1", d => d.source.y)
         .attr("x2", d => d.target.x)
         .attr("y2", d => d.target.y);
    // nodes.attr("x", d => d.x - node_width / 2)
    //      .attr("y", d => d.y - node_height / 2);
    nodes.attr("cx", d => d.x)
         .attr("cy", d => d.y);
    labels.attr("x", d => d.x + node_radius(d.score) + node_border)
          .attr("y", d => d.y + label_font_size * 0.3)
          .style("font-size", label_font_size)
          .style("fill", label_color);
  });

  // Dragging.
  nodes.call(d3.drag()
    .on("start", (event, d) => {
      if (!event.active) simulation.alphaTarget(0.3).restart(); 
      d.fx = d.x; d.fy = d.y; })
    .on("drag", (event, d) => {
      d.fx = event.x; d.fy = event.y; })
    .on("end", (event, d) => {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null; d.fy = null; })
  );

}

// Tiny graph with 2 nodes and 1 edge (for testing).
function get_example_graph_1() {
  return {
    "nodes": [ { "id": "1", "label": "A" },
               { "id": "2", "label": "B" } ],
    "edges": [ { "source": "1", "target": "2", "type": "P31" } ]
  };
}

// Toy graph with 5 nodes and 5 edges (for testing).
function get_example_graph_2() {
  return {
    "nodes": [ { "id": "1", "label": "A" },
               { "id": "2", "label": "B" },
               { "id": "3", "label": "C" },
               { "id": "4", "label": "D" },
               { "id": "5", "label": "E" } ],
    "edges": [ { "source": "1", "target": "2", "type": "P31" },
               { "source": "2", "target": "3", "type": "P279" },
               { "source": "3", "target": "4", "type": "P279" },
               { "source": "4", "target": "5", "type": "P31" },
               { "source": "5", "target": "1", "type": "P279" } ]
  };
}



// Get ranked list of entities matching given prefix via QLever.
async function get_completions(prefix) {
  // QLever AC query.
  const sparql_query = 
    "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>" +
    "PREFIX wikibase: <http://wikiba.se/ontology#>" +
    "SELECT ?item ?label ?sitelinks WHERE {" +
    "  ?item wikibase:sitelinks ?sitelinks ." +
    "  ?item rdfs:label ?label ." +
    "  FILTER REGEX(?label, \"^\\\"" + prefix + "\")" +
    "} ORDER BY DESC(?sitelinks) LIMIT 7";
  const url = sparql_endpoint_url + "?query=" + encodeURIComponent(sparql_query);

  // Get result from QLever.
  const response = await fetch(url);
  const result = await response.json();
  
  completions = result.res.map(row =>
    row[1].replace(/^"(.*)"@en$/, "$1") +
    " (" + row[0].replace(/^<.*\/([^\/]+)>/, "$1") + ")"
  );
  return completions;
}


// Autocompletion functionality from https://www.w3schools.com/howto/howto_js_autocomplete.asp
function autocomplete(input_field) {
  /*the autocomplete function takes two arguments,
  the text field element and an array of possible autocompleted values:*/
  var currentFocus;
  /*execute a function when someone writes in the text field:*/
  input_field.addEventListener("input", function(e) {
    var a, b, i, val = this.value;
    /*close any already open lists of autocompleted values*/
    closeAllLists();
    if (!val) { return false;}
    currentFocus = -1;
    /*create a DIV element that will contain the items (values):*/
    a = document.createElement("DIV");
    a.setAttribute("id", this.id + "autocomplete-list");
    a.setAttribute("class", "autocomplete-items");
    /*append the DIV element as a child of the autocomplete container:*/
    this.parentNode.appendChild(a);

    // /*for each item in the array...*/
    // for (i = 0; i < arr.length; i++) {
    //   /*check if the item starts with the same letters as the text field value:*/
    //   var label = arr[i];
    //   if (label.substr(0, val.length).toUpperCase() == val.toUpperCase()) {

    // Get completions from Wikidata service.
    //
    // NOTE: Did not work because Wikidata does not send a CORS header. Why does
    // it work for https://angryloki.github.io/wikidata-graph-builder ?
    // var search_url = "https://www.wikidata.org/w/api.php" 
    //                    + "?action=wbsearchentities"
    //                    + "&language=en"
    //                    + "&format=json"
    //                    + "&type=item"
    //                    + "&continue=0"
    //                    + "&search=" + val;
    // console.log("Asking Wikidata search API", search_url);
    // fetch(search_url, { mode: "cors", headers: { "Origin": "*" } })
    //   .then(response => response.json())
    //   .then(json => {
    //      console.log(json);

    // Get completions from QLever.
    get_completions(val)
      .then(completions => {
	completions.forEach(completion => {
	  var label = completion;
          // Create a DIV element for each matching element.
          b = document.createElement("div");
          // Make the matching letters bold.
          b.innerHTML = "<strong>" + label.substr(0, val.length) + "</strong>";
          b.innerHTML += label.substr(val.length);
          // Insert an input field that holds this completion.
          b.innerHTML += "<input type=\"hidden\" value=\"" + label + "\">";
          // When someone clicks on this DIV, get the completion.
          b.addEventListener("click", function(e) {
            // Insert the value for the autocomplete text field.
            input_field.value = this.getElementsByTagName("input")[0].value;
	    // Close the list of autocompleted values, or any other open lists
	    // of autocompleted values.
	    closeAllLists();
	    // Extract entity IRI and call graph builder.
	    const entity_id = input_field.value.match(/\((Q\d+)\)/)[1];
	    const entity_iri = "wd:" + entity_id;
	    window.location.hash = "#" + entity_id;
	    buildGraph(entity_iri);
          });
          a.appendChild(b);
        });
      });
  });

  // Handle cursos UP and DOWN, we well as RETURN.
  input_field.addEventListener("keydown", function(e) {
      var x = document.getElementById(this.id + "autocomplete-list");
      if (x) x = x.getElementsByTagName("div");
      if (e.keyCode == 40) {
        /*If the arrow DOWN key is pressed,
        increase the currentFocus variable:*/
        currentFocus++;
        /*and and make the current item more visible:*/
        addActive(x);
      } else if (e.keyCode == 38) { //up
        /*If the arrow UP key is pressed,
        decrease the currentFocus variable:*/
        currentFocus--;
        /*and and make the current item more visible:*/
        addActive(x);
      } else if (e.keyCode == 13) {
        /*If the ENTER key is pressed, prevent the form from being submitted,*/
        e.preventDefault();
        if (currentFocus > -1) {
          /*and simulate a click on the "active" item:*/
          if (x) x[currentFocus].click();
        }
      }
  });

  function addActive(x) {
    /*a function to classify an item as "active":*/
    if (!x) return false;
    /*start by removing the "active" class on all items:*/
    removeActive(x);
    if (currentFocus >= x.length) currentFocus = 0;
    if (currentFocus < 0) currentFocus = (x.length - 1);
    /*add class "autocomplete-active":*/
    x[currentFocus].classList.add("autocomplete-active");
  }

  function removeActive(x) {
    /*a function to remove the "active" class from all autocomplete items:*/
    for (var i = 0; i < x.length; i++) {
      x[i].classList.remove("autocomplete-active");
    }
  }

  function closeAllLists(elmnt) {
    /*close all autocomplete lists in the document,
    except the one passed as an argument:*/
    var x = document.getElementsByClassName("autocomplete-items");
    for (var i = 0; i < x.length; i++) {
      if (elmnt != x[i] && elmnt != input_field) {
      x[i].parentNode.removeChild(x[i]);
    }
  }
}

/*execute a function when someone clicks in the document:*/
document.addEventListener("click", function (e) {
    closeAllLists(e.target);
});

}
