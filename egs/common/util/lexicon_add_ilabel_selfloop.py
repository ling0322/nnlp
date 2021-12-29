#!/usr/bin/env python3

'''
add missing single input label selfloop to lexicon, for example, in lexicon
    one o n e
    two t w o
    three t h r e e
    o o
    n n
    e e
    w w
it will add missing input symbol selfloop
    h h
    r r
This modification simulates the behavior for <unk> -> <capture> in decoding, it is required for some
specific tasks like word segmentation, zhconv, ...

Usage: cat <lexicon-in> | python3 lexicon_add_ilabel_selfloop.py > <lexicon-out>
'''

import sys

from nnlp.symbol import UNK_SYM

UNK_FACTOR = 0.1

ivocab = set()
ignore_isymbols = set()
min_prob = float('inf')
for line in sys.stdin:
    try:
        row = line.strip().split()
        assert len(row) >= 3
        word = row[0]
        prob = float(row[1])
        if prob < min_prob:
            min_prob = prob

        symbols = row[2:]
        ivocab.update(symbols)

        if len(symbols) == 1:
            # ignore adding selfloop if the symbol already exists as a single input
            ignore_isymbols.add(symbols[0])
        
        sys.stdout.write(line)

    except Exception as _:
        raise Exception(f'unexpected line: {line.strip()}')

for symbol in ivocab:
    if symbol not in ignore_isymbols:
        sys.stdout.write(f'{symbol} {min_prob * UNK_FACTOR} {symbol}\n')
