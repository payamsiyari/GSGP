# GSGP
The Generalized Smallest Grammar Problem

This is the implementation of the GSGP framework presented in [1].

## Requirements
* The code uses a slightly modified (in terms of I/O) version of the suffix library, proposed in [2].

## Installation
* Make sure to compile the code in repeats1 directory by simply running ```make```.

## Usage
```python
./python Post-g1fix-irr.py [-a (p | f) | -t (c | i | s) | -p (i) | -q | -r (r | mr | lmr | smr) | -c (r | mr | lmr | smr) | -s (c | e | g) | -f (c | r) | -m | -l | -g] <filename>
    [-a]: specifies the algorithm flags
        p - if set, the algorithm enforces a repeat reduction after identifying each context-reduction
        f - if set along with p flag, only reduces the fixed-gap contexts
    [-t]: choosing between character sequence, integer sequence or space-separated sequence
        c - character sequence
        i - integer sequence
        s - space-separated sequence
    [-p]: specifies grammar printing option
        i - prints the grammar in integer sequence format
    [-q]: disables logging
    [-r]: repeat type (for normal repeat replacements)
        r - repeat
        mr - maximal repeat (default)
        lmr - largest-maximal repeat
        smr - super-maximal repeat
    [-c]: repeat type (for context replacements)
        r - repeat
        mr - maximal repeat (default)
        lmr - largest-maximal repeat
        smr - super-maximal repeat
    [-s]: variable-length context pairs search method
        c - constant maximum length (is set hardcoded)
        e - exhausive (default), searches over all pairs
        g - greedy , selects pairs greedily so that maximum number of consistent pairs are selected
    [-f]: cost function to be optimized
        c - concatenation cost
        r - rule cost (default)
    [-m]: consider each line as a separate string
    [-l]: load a grammar file (will override -r -c -t -m options)
            (as of now, only straight-line grammars are supported)
    [-g]: amount of gap in fixed-gap context-detection mode
```
The output of the code is the final grammar, plus the detailed log of the code. You can remove the log using ```-q``` option.

## References
* [1] P. Siyari, M. Gallé. "The Generalized Smallest Grammar Problem", Proceedings of International Conference on Grammatical Inference (ICGI), 2016.
* [2] M. Gallé. ''Searching for compact hierarchical structures in DNA by means of the Smallest Grammar Problem'', PhD thesis, Université Rennes 1, 2011.