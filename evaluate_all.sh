for d in evaluation_results/*/*.jsonl ; do
    echo "$d"
    if [ "${d: -15}" != "newscrawl.jsonl" ] && [ "${d: -9}" != "ace.jsonl" ] && [ "${d: -11}" != "msnbc.jsonl" ] && [ "${d: -16}" != "conll-test.jsonl" ] && [ "${d: -15}" != "conll-dev.jsonl" ] && [ "${d: -11}" != "conll.jsonl" ]; then
       # This is not an else branch to make it easier to only execute this branch.
       python3 evaluate_linked_entities.py "$d" -b ours
    elif [ "${d: -15}" == "newscrawl.jsonl" ]; then
        python3 evaluate_linked_entities.py "$d" -b newscrawl
    elif [ "${d: -9}" == "ace.jsonl" ]; then
        python3 evaluate_linked_entities.py "$d" -b ace --no-unknowns
    elif [ "${d: -11}" == "msnbc.jsonl" ]; then
        python3 evaluate_linked_entities.py "$d" -b msnbc --no-unknowns
    elif [ "${d: -16}" == "conll-test.jsonl" ]; then
        python3 evaluate_linked_entities.py "$d" -b conll-test
    elif [ "${d: -15}" == "conll-dev.jsonl" ]; then
        python3 evaluate_linked_entities.py "$d" -b conll-dev
    fi
done
