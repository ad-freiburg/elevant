# Third Party Linkers

Some linkers, like TagMe or spaCy's explosion linker can be incorporated in our framework using a single class.
Such linker classes are located in `src/linkers/`.

Other linkers require their own code base consisting of multiple files and maybe even additional data files.
If these linkers run without problems out of the box and yield output in a format that can easily be mapped to 
elevant's internal format, it is enough to write a prediction reader that converts the linker's output into
elevant's internal format. Such prediction reader's are located in `src/helpers`

If a linker's code base requires adjustments to be able to link our benchmarks or to produce output in a format
that can be mapped to elevant's internal format, we put the linker's code here and include the necessary adjustments.