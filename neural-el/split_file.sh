# Split the given file at every n-th line

split -d -l"$2" --additional-suffix=.txt "$1" "${1%.txt}-"
