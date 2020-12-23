# Evaluation webapp

## How to start the evaluation webapp

1. Go to (this) directory: `cd evaluation-webapp`
1. Link to the results directory *evaluation-results*. This is the directory containing subfolders with *<approach>.cases* files.<br>
   E.g. on wolga: `ln -s /local/data/prangen/src/wiki_entity_linker/evaluation-results`
1. Start a file server:<br>
   `python3 -m http.server [PORT]`
1. Access the webapp at 0.0.0.0:[PORT] (default port is 8000).