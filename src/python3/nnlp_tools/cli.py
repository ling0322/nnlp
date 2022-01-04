''' command line tools for nnlp '''

from __future__ import annotations

import argparse
import typing
import math
import sys

from .fst_writer import FstWriter
from .lexicon_fst_builder import LexiconFstBuilder
from .util import read_lexicon
from .fst_util import add_selfloop, add_symbol, remove_fst_disambig, remove_syms_disambig

if typing.TYPE_CHECKING:
    from .lexicon_fst_builder import Lexicon


def _write_lexicon(lexicon: Lexicon, filename: str) -> None:
    ''' write lexicon to file '''
    with open(filename, 'w', encoding='utf-8') as f:
        for word, symbols, log_weight in lexicon:
            f.write(f'{word} {math.exp(-log_weight)} {" ".join(map(str, symbols))}\n')


def build_lexicon_fst(args: list[str]) -> None:
    ''' build lexicon fst from text file '''

    parser = argparse.ArgumentParser(
        prog="buildlexfst",
        description= \
            'build lexicon fst from text file. \n' +
            'the lexicon format is "<word> <probability> <symbol1> <symbol2> ... <symbolN>\\n')
    parser.add_argument('-lexicon', required=True, help='input text file')
    parser.add_argument('-ilabel', required=True, help='output ilabel file')
    parser.add_argument('-olabel', required=True, help='output olabel file')
    parser.add_argument('-fst', help='output text .fst file')
    parser.add_argument('-output_disambig',
                        help='output intermediate lexicon after adding disambigulation symbols')
    cmd_args = parser.parse_args(args)

    fst_generator = LexiconFstBuilder()

    # read lexicon
    lexicon = read_lexicon(cmd_args.lexicon)

    # open output files
    with open(cmd_args.ilabel, 'w', encoding='utf-8') as f_isym, \
         open(cmd_args.olabel, 'w', encoding='utf-8') as f_osym, \
         open(cmd_args.fst, 'w', encoding='utf-8') as f_fst, \
         FstWriter(f_fst, f_isym, f_osym) as fst_writer:
        diambig_lexicon = fst_generator(lexicon, fst_writer)

    # write intermediate lexicon if -disambig is set
    if cmd_args.output_disambig:
        _write_lexicon(diambig_lexicon, cmd_args.output_disambig)


def remove_disambig(args: list[str]) -> None:
    ''' remove disambig symbols from text format FST '''

    def _print_usage():
        print('Usage:')
        print('remove disambig from symbol file:')
        print('    rm_disambig sym < <in-sym> > <out-sym>')
        print('remove disambig from FST file:')
        print('    rm_disambig fst -syms <in-sym> < <in-fst> > <out-fst>')
        sys.exit(1)

    if args[0] == 'sym':
        if len(args) != 2:
            _print_usage()
        remove_syms_disambig(args[1])
    elif args[0] == 'fst':
        parser = argparse.ArgumentParser()
        parser.add_argument('-syms', help='input text format symbols file')
        cmd_args = parser.parse_args(args[1:])

        if not cmd_args.syms:
            _print_usage()

        remove_fst_disambig(sys.stdin, sys.stdout, cmd_args.syms)


def add_selfloop_cli(args: list[str]) -> None:
    ''' remove disambig symbols from text format FST '''

    parser = argparse.ArgumentParser(prog="addselfloop")
    parser.add_argument('-isyms_file', required=True, help='input symbol file')
    parser.add_argument('-osyms_file', required=True, help='output sumbol file')
    parser.add_argument('-isymbol', required=True, help='input symbol for the selfloop arc')
    parser.add_argument('-osymbol', required=True, help='output symbol for the selfloop arc')
    parser.add_argument('-weight', type=float, default=0.0, help='weight for the selfloop arc')
    cmd_args = parser.parse_args(args)

    add_selfloop(sys.stdin, sys.stdout, cmd_args.isyms_file, cmd_args.osyms_file, cmd_args.isymbol,
                 cmd_args.osymbol, cmd_args.weight)

def add_symbol_cli(args: list[str]) -> None:
    ''' add one symbol to symbol file '''

    parser = argparse.ArgumentParser(prog="addsymbol")
    parser.add_argument('-syms_file', required=True, help='symbol file')
    parser.add_argument('-symbol', required=True, help='symbol to add')
    cmd_args = parser.parse_args(args)

    add_symbol(cmd_args.symbol, cmd_args.syms_file)
