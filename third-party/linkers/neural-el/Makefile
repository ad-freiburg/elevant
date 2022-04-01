BOLD := \033[1m
DIM := \033[2m
RESET := \033[0m

help:
	@echo "${BOLD}link_benchmark:${RESET}"
	@echo "		Link all articles in the /data/articles.txt file using Gupta et al.'s CDTE model."
	@echo "		Results are written to /results/linked_articles.jsonl"
	@echo "		Time to run: ~ 5 min | required RAM: 65GB${RESET}"
	@echo "		NOTE: If you don't have enough memory available, split articles.txt into"
	@echo "			  multiple files and run neuralel.py separately for each file."
	@echo ""
	@echo "${BOLD}link_conll_benchmark:${RESET}"
	@echo "		Link all articles in the directory /data/benchmark_articles_conll_split/"
	@echo "		using Gupta et al.'s CDTE model."
	@echo "		Results are written to /results/linked_articles_conll_split/"
	@echo "		Time to run: ~ 4h | required RAM: ~40GB${RESET}"

link_benchmark:
	python3 neuralel.py --config=configs/config.ini --model_path=/data/models/CDTE.model --in_file=/data/articles.txt --out_file=/results/linked_articles.jsonl

link_ner_articles:
	python3 neuralel.py --config=configs/config.ini --model_path=/data/models/CDTE.model --in_file=/data/benchmark_articles_ner.txt --out_file=/results/linked_articles_ner.jsonl --contains_ner=True

link_conll_benchmark:
	./link_conll_files.sh /data/benchmark_articles_conll-test_split/ /results/linked_articles_conll-test_split/
