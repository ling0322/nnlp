''' command line tools for nnlp '''

from __future__ import annotations

import argparse
import io
import typing
import math

from .symbol import EPS_SYM_ID, MAX_SYMBOLS
from .lexicon_fst_generator import LexiconFSTGenerator
from .fst import TextFSTWriter

if typing.TYPE_CHECKING:
    from .lexicon_fst_generator import Lexicon, DisambigLexicon


def _read_lexicon(filename: str) -> Lexicon:
    ''' read lexicon from file, the lexicon format is:
        <word> <probability> <symbol1> <symbol2> ... <symbolN>\\n '''
    lexicon: Lexicon = []
    with open(filename, encoding='utf-8') as f:
        for line in f:
            try:
                row = line.strip().split()
                assert len(row) >= 3
                word = row[0]
                weight = -math.log(float(row[1]))
                symbols = row[2:]
                lexicon.append((word, symbols, weight))
            except Exception as _:
                raise Exception(f'unexpected line in {filename}: {line.strip()}')

    return lexicon


def _write_lexicon(lexicon: DisambigLexicon, filename: str) -> None:
    ''' write lexicon to file '''
    with open(filename, 'w', encoding='utf-8') as f:
        for word, symbols, log_weight in lexicon:
            f.write(f'{word} {math.exp(-log_weight)} {" ".join(map(str, symbols))}\n')


def build_lexicon_fst(args: list[str]) -> None:
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
    parser.add_argument('-unknown_symbol',
                        help='''
                             bahavior for unknown symbols:
                                 output: output this symbol
                                 ignore: ignore this symbol
                                 fail: do not add unknown symbol logic to FST
                             ''')
    parser.add_argument('-output_disambig',
                        help='output intermediate lexicon after adding disambigulation symbols')
    cmd_args = parser.parse_args(args)

    if cmd_args.input == None or cmd_args.ilabel == None or \
       cmd_args.olabel == None or cmd_args.fst == None:
        parser.print_help()
        return

    fst_generator = LexiconFSTGenerator()

    # read lexicon
    lexicon = _read_lexicon(cmd_args.input)

    # open output files
    with open(cmd_args.ilabel, 'w', encoding='utf-8') as f_isym, \
         open(cmd_args.olabel, 'w', encoding='utf-8') as f_osym, \
         open(cmd_args.fst, 'w', encoding='utf-8') as f_fst:
        fst_writer = TextFSTWriter(f_fst, f_isym, f_osym)
        diambig_lexicon = fst_generator(lexicon, fst_writer, unknown_symbol=cmd_args.unknown_symbol)

    # write intermediate lexicon if -disambig is set
    if cmd_args.output_disambig:
        _write_lexicon(diambig_lexicon, cmd_args.output_disambig)

def _remove_fst_disambig(input_file: str, output_file: str) -> None:
    ''' remove disambig symbols from text format FST '''

    with open(input_file, encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            row = line.strip().split()
            if len(row) in {4, 5}:
                isymbol_id = int(row[2])
                if isymbol_id > MAX_SYMBOLS:
                    isymbol_id = EPS_SYM_ID
                row[2] = str(isymbol_id)
            
            f_out.write(' '.join(row) + '\n')

def _remove_lexicon_disambig(input_file: str, output_file: str) -> None:
    ''' remove disambig symbols from text format lexicon '''

    with open(input_file, encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            row = line.strip().split()
            isymbol_id = int(row[1])
            if isymbol_id >= MAX_SYMBOLS:
                continue
            
            f_out.write(' '.join(row) + '\n')

def remove_disambig(args: list[str]) -> None:
    ''' remove disambig symbols from text format FST '''

    parser = argparse.ArgumentParser(prog="rm_disambig",
                                     description='''remove disambig symbols from either text format FST (-input_fst) or
                                                    lexicon (-input_lexicon)''')
    parser.add_argument('-input_fst', help='input text format FST file')
    parser.add_argument('-input_lexicon', help='input text format lexicon file')
    parser.add_argument('-output', help='output text format FST file')
    cmd_args = parser.parse_args(args)

    if cmd_args.output == None:
        parser.print_help()
        return

    if cmd_args.input_fst and not cmd_args.input_lexicon:
        _remove_fst_disambig(cmd_args.input_fst, cmd_args.output)
    elif not cmd_args.input_fst and cmd_args.input_lexicon:
        _remove_lexicon_disambig(cmd_args.input_lexicon, cmd_args.output)
    
