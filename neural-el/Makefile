BOLD := \033[1m
DIM := \033[2m
RESET := \033[0m

help:
	@echo "${BOLD}inference:${RESET}"
	@echo "		Run inference of the Gupta et al. CDTE model over all articles"
	@echo "		in the /data/articles.txt file."
	@echo "		Results are written to /results/linked_articles.jsonl"
	@echo "		time to run: ~ 8 min | required RAM: 65GB${RESET}"
	@echo "		NOTE: If you don't have enough memory available, split articles.txt into"
	@echo "			  multiple files and run neuralel.py separately for each file."


link_benchmark:
	python3 neuralel.py --config=configs/config.ini --model_path=/data/models/CDTE.model --in_file=/data/articles.txt --out_file=/results/linked_articles.jsonl
