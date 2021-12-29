''' command line tools for nnlp '''

from __future__ import annotations

import argparse
from typing import Optional
import typing
import math
import sys

from nnlp.symbol import EPS_SYM, is_disambig_symbol
from nnlp.fst import Fst

from .fst_writer import TextFSTWriter
from .lexicon_fst_generator import LexiconFSTGenerator
from .util import read_lexicon

if typing.TYPE_CHECKING:
    from .lexicon_fst_generator import Lexicon


def _write_lexicon(lexicon: Lexicon, filename: str) -> None:
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
    lexicon = read_lexicon(cmd_args.input)

    # open output files
    with open(cmd_args.ilabel, 'w', encoding='utf-8') as f_isym, \
         open(cmd_args.olabel, 'w', encoding='utf-8') as f_osym, \
         open(cmd_args.fst, 'w', encoding='utf-8') as f_fst:
        fst_writer = TextFSTWriter(f_fst, f_isym, f_osym)
        diambig_lexicon = fst_generator(lexicon, fst_writer, unknown_symbol=cmd_args.unknown_symbol)

    # write intermediate lexicon if -disambig is set
    if cmd_args.output_disambig:
        _write_lexicon(diambig_lexicon, cmd_args.output_disambig)


def _remove_fst_disambig(input_sym: str) -> None:
    ''' remove disambig symbols from text format FST '''

    # get disambig symbols set and eps symbol id from symbol file
    disambig_isymbol_ids = set()
    eps_isymbol_id: Optional[int] = None

    with open(input_sym, encoding='utf-8') as f_sym:
        isymbols = Fst._read_symbols(f_sym)

    for symbol_id, symbol in enumerate(isymbols):
        if is_disambig_symbol(symbol):
            disambig_isymbol_ids.add(symbol_id)
        if symbol == EPS_SYM:
            eps_isymbol_id = symbol_id
    if eps_isymbol_id == None:
        raise Exception(f'unable to find id for <eps>')
    assert isinstance(eps_isymbol_id, int)

    # change diambig symbols to eps
    for line in sys.stdin:
        row = line.strip().split()
        if len(row) in {4, 5}:
            isymbol_id = int(row[2])
            if isymbol_id in disambig_isymbol_ids:
                isymbol_id = eps_isymbol_id
            row[2] = str(isymbol_id)

        sys.stdout.write(' '.join(row) + '\n')


def _remove_syms_disambig() -> None:
    ''' remove disambig symbols from symbol file stdin and write output to stdout '''

    for line in sys.stdin:
        row = line.strip().split()
        symbol = row[0]
        if is_disambig_symbol(symbol):
            continue

        sys.stdout.write(' '.join(row) + '\n')


def remove_disambig(args: list[str]) -> None:
    ''' remove disambig symbols from text format FST '''

    if not args:
        print('Usage:')
        print('    remove disambig from symbol file: cat <in-sym> | rm_disambig sym > <out-sym>')
        print('    remove disambig from FST file: cat <in-fst> | rm_disambig fst -syms <in-sym> > <out-fst>')
        return
    
    if args[0] == 'sym':
        _remove_syms_disambig()
    elif args[0] == 'fst':
        parser = argparse.ArgumentParser()
        parser.add_argument('-syms', help='input text format symbols file')
        cmd_args = parser.parse_args(args[1: ])

        if not cmd_args.syms:
            print('-syms not specified')
            return

        _remove_fst_disambig(cmd_args.syms)
