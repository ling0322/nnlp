#!/usr/bin/env python3

''' build Breaker FST that outputs <break> symbol after each symbol '''

import sys
import argparse

from nnlp.symbol import CAP_SYM, EPS_SYM, BRK_SYM, UNK_SYM, is_special_symbol
from nnlp_tools.fst_writer import FstWriter
from nnlp_tools.util import read_symbol_table

parser = argparse.ArgumentParser(prog="build_break_outputter_fst.py")
parser.add_argument('-syms_file', required=True, help='symbol file')
parser.add_argument('-out_prefix', required=True, help='prefix for output FST')
cmd_args = parser.parse_args()

prefix = cmd_args.out_prefix

isymbols = read_symbol_table(cmd_args.syms_file)

concat_set = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_."

with open(f'{prefix}.txt', 'w') as f_fst, \
     open(f'{prefix}.isyms.txt', 'w') as f_isyms, \
     open(f'{prefix}.osyms.txt', 'w') as f_osyms, \
     open(f'{prefix}.info.txt', 'w') as f_info, \
     FstWriter(f_fst, cmd_args.syms_file, f_osyms) as fst_writer:
    state_1 = fst_writer.create_state()
    for symbol in isymbols.keys():
        if  symbol not in concat_set and not is_special_symbol(symbol):
            if symbol in {r'\s', r'\t', r'\r', r'\n'}:
                fst_writer.add_arc(0, state_1, symbol, EPS_SYM)
            else:
                fst_writer.add_arc(0, state_1, symbol, symbol)
    
    # handle unknown symbols
    state_2 = fst_writer.create_state()
    fst_writer.add_arc(0, state_2, UNK_SYM, CAP_SYM, 10)
    fst_writer.add_arc(state_2, 0, EPS_SYM, BRK_SYM)

    # handle concat set
    state_3 = fst_writer.create_state()
    for symbol in concat_set:
        fst_writer.add_arc(0, state_3, symbol, symbol, 10)
        fst_writer.add_arc(state_3, state_3, symbol, symbol)
    fst_writer.add_arc(state_3, 0, EPS_SYM, BRK_SYM)

    # output the break symbol
    fst_writer.add_arc(state_1, 0, EPS_SYM, BRK_SYM)
    fst_writer.set_final_state(0)

    # copy cmd_args.syms_file to {prefix}.isyms.txt
    FstWriter._write_symbol_table(isymbols, f_isyms)

    # write informartion
    f_info.write('Breaker\n')
