# Benchmark webapp

This webapp displays information about the groundtruth label types and level1 distribution on different benchmarks.

## How to start the benchmark webapp

1. Create the relevant `<benchmark_name>.types.json` and `<benchmark_name>.labels.tsv` files using the script
 `analyze_benchmark_entity_types.py`:
        
        python3 scripts/analyze_benchmark_entity_types.py <benchmark_name>
        
1. Go to (this) directory:

        cd benchmark-webapp

1. Link to the `benchmarks` directory that contains the generated `*.types.json` and `*.labels.tsv` files:

        ln -s ../benchmarks
        
1. Link to the `data` directory that contains the whitelist type file `whitelist_types.txt`:

        ln -s ../data
        
1. Start a file server:

        python3 -m http.server [PORT]

1. Access the webapp at 0.0.0.0:[PORT] (default port is 8000).