BOLD := \033[1m
DIM := \033[2m
RESET := \033[0m

INPUT_DIR = input_articles
OUTPUT_DIR = output_articles

help:
	@echo "${BOLD}link_benchmarks:${RESET}"
	@echo "		Link all articles in the /home/input_articles/*/ directories using Wikifier."
	@echo "		Results are written to /home/output_articles/*/ directories"
	@echo "		Time to run: ~ 10 min | required RAM: ~12GB${RESET}"
	@echo ""

link_benchmarks:
	@for subdir in $(shell ls ${INPUT_DIR}); do \
		echo $${subdir}; \
		mkdir ${OUTPUT_DIR}/$${subdir}; \
		chmod a+rw ${OUTPUT_DIR}/$${subdir}; \
		java -Xmx10G -jar dist/wikifier-3.0-jar-with-dependencies.jar -annotateData ${INPUT_DIR}/$${subdir}/ ${OUTPUT_DIR}/$${subdir}/ false configs/STAND_ALONE_NO_INFERENCE.xml; \
	done
