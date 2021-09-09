for benchmark in ours conll conll-dev conll-test msnbc ace newscrawl; do
	python3 analyze_benchmark_entity_types.py $benchmark;
done
