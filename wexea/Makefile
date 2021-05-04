BOLD := \033[1m
DIM := \033[2m
RESET := \033[0m

help:
	@echo "${BOLD}extract_statistics:${RESET}"
	@echo "		Extract statistics and articles from the unzipped wikipedia dump at"
	@echo "		/wikipedia-dump/enwiki-latest-pages-articles-multistream.xml"
	@echo "		Resulting dictionaries and articles are written to directory"
	@echo "		/results/"
	@echo "		NOTE: This is only needed once and only if the files don't exist in the file system yet."
	@echo "		time to run: ~ 24h | required RAM: xxGB${RESET}"
	@echo ""
	@echo "${BOLD}annotate_benchmark:${RESET}"
	@echo "		Link all articles in subdirectories of the directory"
	@echo "		/results/original_articles_benchmark/"
	@echo "		Resulting articles are written to corresponding subdirectories in directory"
	@echo "		/results/final_articles_benchmark/"
	@echo "		time to run: ~ 5 min | required RAM: ~19GB${RESET}"
	@echo ""
	@echo "${BOLD}annotate_benchmark_only_new:${RESET}"
	@echo "		Link all articles in"
	@echo "		/results/original_articles_benchmark/new/"
	@echo "		Resulting articles are written to"
	@echo "		/results/final_articles_benchmark/new/"
	@echo "		time to run: ~ 5 min | required RAM: ~19GB${RESET}"
	@echo ""
	@echo "${BOLD}annotate_wikipedia:${RESET}"
	@echo "		Link all articles in subdirectories of the directory"
	@echo "		/results/original_articles/"
	@echo "		Per default, this directory contains all Wikipedia articles."
	@echo "		Resulting articles are written to corresponding subdirectories in directory"
	@echo "		/results/final_articles/"
	@echo "		time to run: ~ xx h | required RAM: xxGB${RESET}"
	@echo ""
	@echo "${BOLD}run_server:${RESET}"
	@echo "		Run the server on port 8080 per default."
	@echo "		Shows the linked Wikipedia articles (not the annotated benchmark)."
	@echo "		time to load: < 1 min | required RAM: ~ 4GB${RESET}"

extract_statistics:
	python3 src/title2Id_redirect_parser.py
	python3 src/article_parser_1.py
	python3 src/dicts_creator.py

annotate_benchmark:
	python3 src/article_parser_1_benchmark.py  # Fixes links and appends link entities to the file
	python3 src/article_parser_2.py --benchmark
	python3 src/article_parser_3.py --benchmark
	python3 src/article_parser_4.py --benchmark
	python3 src/article_parser_5_benchmark.py  # Puts linked articles into correct output format

annotate_benchmark_only_new:
	python3 src/article_parser_1_benchmark.py --only_new
	python3 src/article_parser_2.py --benchmark --only_new
	python3 src/article_parser_3.py --benchmark --only_new
	python3 src/article_parser_4.py --benchmark --only_new
	python3 src/article_parser_5_benchmark.py --only_new

annotate_wikipedia:
	python3 src/article_parser_2.py
	python3 src/article_parser_3.py
	python3 src/article_parser_4.py

run_server:
	python3 src/server.py
