input_dir=$1
output_dir=$2

count=10  # start with double digit numbers to make sorting easier
for f in "$input_dir"benchmark_articles_conll-*.txt
do
  python3 neuralel.py --config=configs/config.ini --model_path=/data/models/CDTE.model --in_file="$f" --out_file="$output_dir"linked_articles_conll-"$count".jsonl
  count=$((count + 1))
done