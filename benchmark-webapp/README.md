# Benchmark webapp

This webapp displays information about the groundtruth label types and level1 distribution on different benchmarks.

## How to start the benchmark webapp

1. Create the relevant `<benchmark_name>.types.json` and `<benchmark_name>.labels.tsv` files using the script `analyze_benchmark_entity_types.py`:
        
        analyze_benchmark_entity_types.py <benchmark_name>
        
1. Go to (this) directory:

        cd benchmark-webapp

1. Link to the benchmark directory that contains the generated `*.types.json` and `*.labels.tsv` files:

        ln -s ../benchmarks
        
1. Start a file server:

        python3 -m http.server [PORT]
1. Access the webapp at 0.0.0.0:[PORT] (default port is 8000).