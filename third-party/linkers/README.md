# Third Party Linkers

When evaluating the performance of a linking system with Elevant, we distinguish between three classes of linkers:
1. Some linkers can be incorporated into our framework without writing much code, e.g. by accessing an external
 linker API. The code needed for such linkers is located in `src/linkers/`. The following linkers belong to this class:
    - TagMe
    - DBPedia Spotlight
    - Spacy
    - Explosion
    - Our baselines

2. For some linkers, an entire code base is needed to produce linking results and this code base does not run
 out of the box or does not produce output in a format that can be mapped to Elevant's internal format, e.g. because
 important information such as the mention span is missing. We put those linker's code here into
 `third-party/linkers/` and include the necessary adjustments. The following linkers belong to this class:
    - Neural EL (by Gupta et al.)
    - Wikifier
    - GENRE
    - Efficient EL

3. For linkers where an entire code base is needed which can be run without bigger problems out of the box and yields
 output in a format that can easily be mapped to Elevant's internal format, it is enough to write a prediction reader
 that converts the linker's output into Elevant's internal format. Such prediction reader's are located in
 `src/prediction_readers/`. The following linkers are examples for this class:
    - Ambiverse
