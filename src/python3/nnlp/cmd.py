''' command line tools for nnlp '''

from __future__ import annotations

import argparse
import io
import typing
import math

from .lexicon_fst_generator import LexiconFSTGenerator
from .fst import TextFSTWriter

if typing.TYPE_CHECKING:
    from .lexicon_fst_generator import Lexicon


def build_lexicon_fst(args: list) -> None:
    ''' build lexicon fst from text file '''

    parser = argparse.ArgumentParser(
        prog="build_lexicon_fst",
        description= \
            'build lexicon fst from text file. \n' +
            'the lexicon format is "<word> <probability> <symbol1> <symbol2> ... <symbolN>\\n')
    parser.add_argument('-input', help='input text file')
    parser.add_argument('-ilabel', help='output ilabel file')
    parser.add_argument('-olabel', help='output olabel file')
    parser.add_argument('-fst', help='output text .fst file')
    cmd_args = parser.parse_args(args)

    if cmd_args.input == None or cmd_args.ilabel == None or \
       cmd_args.olabel == None or cmd_args.fst == None:
        parser.print_help()
        return

    fst_generator = LexiconFSTGenerator()

    # read lexicon
    lexicon: Lexicon = []
    with open(cmd_args.input, encoding='utf-8') as f:
        for line in f:
            row = line.strip().split()
            if len(row) < 3:
                raise Exception(f'unexpected line in {cmd_args.input}: {line.strip()}')
            word = row[0]
            weight = math.log(float(row[1]))
            symbols = row[2: ]
            lexicon.append((word, symbols, weight))

    # open output files
    with open(cmd_args.ilabel, 'w', encoding='utf-8') as f_isym, \
         open(cmd_args.olabel, 'w', encoding='utf-8') as f_osym, \
         open(cmd_args.fst, 'w', encoding='utf-8') as f_fst:
        fst_writer = TextFSTWriter(f_fst, f_isym, f_osym)
        fst_generator(lexicon, fst_writer)
