for d in evaluation-webapp/evaluation-results/*/*.jsonl ; do
    python3 evaluate_linked_entities.py "$d"
done
