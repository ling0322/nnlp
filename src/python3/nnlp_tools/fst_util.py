''' utility functions for FST '''
from __future__ import annotations

import sys
from typing import TextIO, Optional

from nnlp.symbol import EPS_SYM, is_disambig_symbol
from nnlp.fst import Fst

from .fst_writer import FstWriter
from .util import read_symbol_table

def remove_fst_disambig(input_stream: TextIO, output_stream: TextIO, isyms_file: str) -> None:
    '''
    remove disambig symbols from text format FST
    Args:
        input_stream (TextIO): input FST stream
        output_stream (TextIO): output FST stream
        isyms_file (str): input symbols file '''

    # get disambig symbols set and eps symbol id from symbol file
    disambig_isymbol_ids = set()
    eps_isymbol_id: Optional[int] = None

    with open(isyms_file, encoding='utf-8') as f_sym:
        isymbols = Fst._read_symbols(f_sym)

    for symbol_id, symbol in enumerate(isymbols):
        if is_disambig_symbol(symbol):
            disambig_isymbol_ids.add(symbol_id)
        if symbol == EPS_SYM:
            eps_isymbol_id = symbol_id
    if eps_isymbol_id != 0:
        raise Exception(f'unexpected symbol id for <eps>')
    assert isinstance(eps_isymbol_id, int)

    # change diambig symbols to eps
    for line in input_stream:
        row = line.strip().split()
        if len(row) in {4, 5}:
            isymbol_id = int(row[2])
            if isymbol_id in disambig_isymbol_ids:
                isymbol_id = eps_isymbol_id
            row[2] = str(isymbol_id)

        output_stream.write(' '.join(row) + '\n')


def remove_syms_disambig(syms_file: str) -> None:
    '''
    remove disambig symbols from FST
    Args:
        syms_file (str): the symbol file to remove disambig '''

    symbol_table = read_symbol_table(syms_file)
    symbols = list(symbol_table.keys())
    for symbol in symbols:
        if is_disambig_symbol(symbol):
            del symbol_table[symbol]
    
    with open(syms_file, 'w', encoding='utf-8') as f:
        FstWriter._write_symbol_table(symbol_table, f)

def add_symbol(symbol: str, symbols_file: str) -> None:
    ''' add symbol to file if not exist '''

    symbol_table = read_symbol_table(symbols_file)

    max_symbol_id = max(symbol_table.values())
    if symbol not in symbol_table:
        symbol_table[symbol] = max_symbol_id + 1

    with open(symbols_file, 'w', encoding='utf-8') as f:
        FstWriter._write_symbol_table(symbol_table, f)


def add_selfloop(input_stream: TextIO, output_stream: TextIO, isyms_file: str, osyms_file: str,
                 isymbol: str, osymbol: str, weight: float) -> None:
    '''
    add selfloop to a fst stream
    Args:
        input_stream (TextIO): input FST stream
        output_stream (TextIO): output FST stream
        isyms_file (str): input symbols file
        osyms_file (str): output symbols file
        isymbol (str): input symbol for the selfloop arc
        osymbol (str): output symbol for the selfloop arc
        weight (float): weight for the selfloop arc '''
    
    isymbols = read_symbol_table(isyms_file)
    if isymbol not in isymbols:
        raise Exception(f'symbol "{isymbol}" not exist in {isyms_file}')
    osymbols = read_symbol_table(osyms_file)
    if osymbol not in osymbols:
        raise Exception(f'symbol "{osymbol}" not exist in {osyms_file}')

    isymbol_id = isymbols[isymbol]
    osymbol_id = osymbols[osymbol]

    final_states: set[int] = set()
    for line in input_stream:
        # src dest ilabel olabel [weight]  <- arc
        # state [weight]                   <- final state
        row = line.strip().split()
        if len(row) in {1, 2}:
            # final state
            state = int(row[0])
            final_states.add(state)
        
        output_stream.write(line)
    
    # append selfloop arcs to FST stream
    for final_state in final_states:
        output_stream.write(f'{final_state} 0 {isymbol_id} {osymbol_id} {weight}\n')
