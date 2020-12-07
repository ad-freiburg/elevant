BOLD := \033[1m
DIM := \033[2m
RESET := \033[0m

help:
	@echo "${BOLD}evaluate_own_system:${RESET}"
	@echo "		Evaluate our own entity linking system consisting of link-text-linker, explosion linker and entity coreference resolution."
	@echo "		The results are printed to stdout and the evaluation cases written to 'evaluated_own.cases'."
	@echo "		time to run: ~ 5 min | required RAM: ~ 24GB${RESET}"
	@echo "${BOLD}evaluate_tagme:${RESET}"
	@echo "		Evaluate Tagme."
	@echo "		The results are printed to stdout and the evaluation cases written to 'evaluated_tagme.cases'."
	@echo "		time to run: ~ 3 min | required RAM: ~ 8GB${RESET}"
	@echo "${BOLD}evaluate_baseline:${RESET}"
	@echo "		Evaluate Baseline system."
	@echo "		The results are printed to stdout and the evaluation cases written to 'evaluated_baseline.cases'."
	@echo "		time to run: ~ 6 min | required RAM: ~ 18GB${RESET}"

evaluate_own_system:
	python3 link_benchmark_entities.py evaluated_own.jsonl explosion data/linker-1M/nlp --link_linker link-text-linker -coref entity
	python3 evaluate_linked_entities.py evaluated_own.jsonl

evaluate_tagme:
	python3 link_benchmark_entities.py evaluated_tagme.jsonl tagme 0.2
	python3 evaluate_linked_entities.py evaluated_tagme.jsonl

evaluate_baseline:
	python3 link_benchmark_entities.py evaluated_baseline.jsonl baseline links-all
	python3 evaluate_linked_entities.py evaluated_baseline.jsonl
