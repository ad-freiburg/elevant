// Color for each type.
var type2color = { "P31": "blue", "P279": "red" };


document.addEventListener("DOMContentLoaded", function(event) { 
  console.log("At your service ...");


  // Toy graph with 5 nodes.
  var toy_graph = {
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

  // Obtain graph (QLever query + turn result into graph).
  async function getGraphFromQlever() {
    // URL for QLever query (for now: fixed subject Q937 = Albert Einstein).
    var url = "https://qlever.informatik.uni-freiburg.de/api/wikidata-types?query=PREFIX+rdfs%3A+%3Chttp%3A%2F%2Fwww.w3.org%2F2000%2F01%2Frdf-schema%23%3E%0APREFIX+wikibase%3A+%3Chttp%3A%2F%2Fwikiba.se%2Fontology%23%3E%0APREFIX+wdt%3A+%3Chttp%3A%2F%2Fwww.wikidata.org%2Fprop%2Fdirect%2F%3E%0APREFIX+wd%3A+%3Chttp%3A%2F%2Fwww.wikidata.org%2Fentity%2F%3E%0ASELECT+DISTINCT+%3Fs+%3Fp+%3Fo+%3Fs_name+%3Fo_name+%3Fs_score+%3Fo_score+WHERE+%7B%0A++%3Fs+wikibase%3Asitelinks+%3Fs_score+.%0A++%3Fo+wikibase%3Asitelinks+%3Fo_score+.%0A++%3Fs+rdfs%3Alabel+%3Fs_name+.%0A++%3Fo+rdfs%3Alabel+%3Fo_name+.%0A++%7B+VALUES+%3Fs+%7B+wd%3AQ937+%7D+VALUES+%3Fp+%7B+wdt%3AP31+%7D+%3Fs+%3Fp+%3Fo+%7D%0A++UNION%0A++%7B+wd%3AQ937+wdt%3AP31%2Fwdt%3AP279%2A+%3Fs+.+VALUES+%3Fp+%7B+wdt%3AP279+%7D+%3Fs+%3Fp+%3Fo+%7D%0A%7D%0AORDER+BY+DESC%28%3Fs_score%29";

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
      source_node = { "id": row[0], "label": row[3], "score": row[5] };
      target_node = { "id": row[2], "label": row[4], "score": row[6] };
      // Add node.
      [source_node, target_node].forEach(node => {
	node.id = node.id.replace(/<.*\/(.*)>/, "$1");
	node.label = node.label.replace(/^"(.*)"@en$/, "$1");
	node.score = +node.score.replace(/^"(\d+)".*$/g, "$1");
	nodes[node.id] = node;
      });
      // Add edge.
      edges.push({ "source": source_node.id,
	           "target": target_node.id,
	           "type": row[1].replace(/<.*\/(.*)>/, "$1") });
    });
    nodes = Object.values(nodes);
    // console.log("Nodes:", nodes);
    // console.log("Edges:", edges);
    return { "nodes": nodes, "edges": edges };
  }

  // Draw the toy graph.
  // drawGraph(data);

  getGraphFromQlever()
    .then(graph => drawGraph(graph))
    .catch(error => console.log("ERROR:", error));

});

function drawGraph(data) {

  // Show the data.
  console.log("GRAPH:", data);

  // Setup D3.
  var svg = d3.select("#graph");
  var width = +svg.attr("width");
  var height = +svg.attr("height");
  console.log("SVG dimensions:", width, "x", height);

  // NOTE: The append("g") in the following adds all selected (or newly entered)
  // elements to the same "group". TOOD: not quite sure yet what that means.

  // Draw nodes and edges (at no particular position yet = upper left corner).
  // 
  // NOTE: Edges first, so that the node circle are draw on top of the edge
  // lines (which conect the node centers).
  var edges = svg.append("g").selectAll("line")
                 .data(data.edges).enter().append("line")
                 .style("stroke", d => type2color[d.type])
                 .style("stroke-width", "3");

  // Draw the nodes (at no particular position yet = upper left corner).
  var nodes = svg.append("g").selectAll("circle")
                 .data(data.nodes).enter().append("circle")
                 .attr("r", 14).style("fill", "#EEEEEE")
                 .attr("stroke", "white").attr("stroke-width", 3)
                 .attr("cx", width / 2).attr("cy", height / 2);

  // Node labels.
  var labels = svg.append("g").selectAll("text")
                  .data(data.nodes).enter().append("text")
                  .text(d => d.label)
                  .attr("unselectable", "on");

  // Setup force simulation.
  var simulation = d3.forceSimulation(data.nodes)
      .force("link", d3.forceLink().id(d => d.id).links(data.edges))
      .force("charge", d3.forceManyBody().strength(-50))
      .force("center", d3.forceCenter(width / 2, height / 2));

  // Start simulation?
  simulation.nodes(data.nodes);

  // The "ticked" function from the "on" above.
  simulation.on("tick", () => {
    edges.attr("x1", d => d.source.x)
         .attr("y1", d => d.source.y)
         .attr("x2", d => d.target.x)
         .attr("y2", d => d.target.y);
    nodes.attr("cx", d => d.x)
         .attr("cy", d => d.y);
    labels.attr("x", d => d.x - 5)
          .attr("y", d => d.y + 5)
          .style("font-size", "10px")
          .style("fill", "black");
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
