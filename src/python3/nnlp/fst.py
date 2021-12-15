from __future__ import annotations

import abc
from typing import List, TextIO, Union
from operator import itemgetter
import unittest
import io

EPS_ID = 0  # symbol id for epsilon
EPS_SYM = ''  # epsilon symbol

NAN = float('nan')


class Disambig:
    ''' represent disambiguation symbol #1, #2, #3, ... in Fst
    Args:
        symbol_id: id of disambiguation symbol, 1 for #1, 2 for #2, ... '''

    _cache: dict[int, Disambig] = {}
    symbol_id: int

    def __new__(cls, symbol_id: int) -> Disambig:
        if symbol_id in cls._cache:
            return cls._cache[symbol_id]
        
        disambig = super(Disambig, cls).__new__(cls)
        disambig.symbol_id = symbol_id
        cls._cache[symbol_id] = disambig

        return disambig

    def __repr__(self) -> str:
        return f'#_disambig_{self.symbol_id}'


class FSTWriter(abc.ABC):
    r''' base class for Fst writer that supports add arc, add state and set final state '''

    @abc.abstractmethod
    def add_arc(
        self,
        src_state: int,
        dest_state: int,
        isymbol: Disambig | str,
        osymbol: str,
        weight: float = 0.0,
    ) -> None:
        r''' 
        add an arc to Fst 
            Args:
            src_state (int): source state
            dest_state (int): destination state
            isymbol (str): input symbol
            osymbol (str): output symbol
            weight (float): weight'''
        pass

    @abc.abstractmethod
    def set_final_state(self, state: int, weight: float = 0.0) -> None:
        r''' set final state '''
        pass

    @abc.abstractmethod
    def create_state(self) -> int:
        r''' create a new state in FST, returns the state id '''
        pass

    @abc.abstractmethod
    def write(self) -> None:
        r''' finished Fst building, write all data into files '''
        pass


class TextFSTWriter(FSTWriter):
    r''' fst writer for OpenFST text file format
    FST arc was using OpenFST/AT&T FSM format: src dest ilabel olabel [weight]
    Args:
        fst_stream (TextIO): stream for writing AT&T FSM format FST
        ilabel_stream (TextIO): stream for writing input symbols 
        olabel_stream (TextIO): stream for writing output symbols 
        disambig_start_idx (int): start index for disambiguation symbols '''

    def __init__(self,
                 fst_stream: TextIO,
                 ilabel_stream: TextIO,
                 olabel_stream: TextIO,
                 disambig_start_idx: int = 2000000) -> None:
        self._isymbols: dict[str, int] = {EPS_SYM: EPS_ID}
        self._osymbols: dict[str, int] = {EPS_SYM: EPS_ID}
        self._disambig_symbol_ids: set[int] = set()
        self._n_states = 1
        self._fst_stream: TextIO = fst_stream
        self._ilabel_stream: TextIO = ilabel_stream
        self._olabel_stream: TextIO = olabel_stream

        self._symbol_table_written = False
        self._disambig_start_idx = disambig_start_idx

    def create_state(self) -> int:
        r''' implements ABC FstWriter '''

        self._n_states += 1
        return self._n_states - 1

    def set_final_state(self, state: int, weight: float = 0.0) -> None:
        r''' implements ABC FstWriter '''

        # OpenFST/AT&T FSM format: state [weight]
        self._fst_stream.write(f'{state} {weight}\n')

    def add_arc(self,
                src_state: int,
                dest_state: int,
                isymbol: Disambig | str,
                osymbol: str,
                weight: float = 0.0) -> None:
        r''' implements ABC FstWriter '''

        isymbol_id = self._get_symbol_id(isymbol, self._isymbols)
        osymbol_id = self._get_symbol_id(osymbol, self._osymbols)

        # OpenFST/AT&T FSM format: src dest ilabel olabel [weight]
        self._fst_stream.write(f'{src_state} {dest_state} {isymbol_id} {osymbol_id} {weight}\n')

    def write(self) -> None:
        r''' implements ABC FstWriter '''

        if self._symbol_table_written:
            raise Exception(f'FST data already written')

        self._write_symbol_table(self._isymbols, self._ilabel_stream)
        self._write_symbol_table(self._osymbols, self._olabel_stream)

        # process disambig symbols
        if self._disambig_symbol_ids:
            disambig_symbols = self._generate_disambig_symbol_table()
            self._write_symbol_table(disambig_symbols, self._ilabel_stream)

        self._symbol_table_written = True

    def _write_symbol_table(self, symbol_table: dict[str, int], stream: TextIO) -> None:
        r''' write symbol table to a stream '''

        symbols = list(symbol_table.items())
        symbols.sort(key=itemgetter(1))

        for symbol, symbol_id in symbols:
            if symbol == '':
                symbol = '<eps>'
            stream.write(f'{symbol} {symbol_id}\n')

    def _generate_disambig_symbol_table(self) -> dict[str, int]:
        ''' generate symbol table for disambiguation symbols '''

        disambig_symbol_ids = list(self._disambig_symbol_ids)
        disambig_symbol_ids.sort()
        disambig_symbols: dict[str, int] = {}
        
        for symbol_id in disambig_symbol_ids:
            original_symbol = f'#_disambig_{symbol_id}'
            symbol = original_symbol
            symbol_suffix = 0

            # find an symbol string if the disambig symbol conflicts with self._isymbols
            while symbol in self._isymbols:
                symbol = original_symbol + f'_{symbol_suffix}'
                symbol_suffix += 1
            disambig_symbols[symbol] = self._disambig_start_idx + symbol_id
        
        return disambig_symbols

    def _get_symbol_id(self, symbol: Disambig | str, symbol_dict: dict[str, int]) -> int:
        r''' get id of a input symbol from symbol_dict, it will create a new symbol id if 
        symbol not exist in symbol_dict '''

        if isinstance(symbol, Disambig):
            self._disambig_symbol_ids.add(symbol.symbol_id)
            return self._disambig_start_idx + symbol.symbol_id

        if symbol not in symbol_dict:
            symbol_id = len(symbol_dict)
            if symbol_id == self._disambig_start_idx:
                raise Exception(f'too many input symbols (consider increase disambig_start_idx?)')

            symbol_dict[symbol] = symbol_id
            return symbol_id
        else:
            return symbol_dict[symbol]


class FstArc:
    r''' 
    arc in FST graph
    Args:
        src_state (int): source state
        dest_state (int): destination state
        isymbol (str): input symbol
        osymbol (str): output symbol
        weight (float): weight'''

    def __init__(self, src_state: int, dest_state: int, isymbol: str, osymbol: str,
                 weight: float) -> None:
        self.src_state = src_state
        self.dest_state = dest_state
        self.isymbol = isymbol
        self.osymbol = osymbol
        self.weight = weight

    def __repr__(self) -> str:
        return f'FstArc({self.src_state}, {self.dest_state}, "{self.isymbol}", "{self.osymbol}", {self.weight})'

    def __eq__(self, right) -> bool:
        if not isinstance(right, FstArc):
            return False
        return right.weight == self.weight and \
               right.src_state == self.src_state and \
               right.dest_state == self.dest_state and \
               right.isymbol == self.isymbol and \
               right.osymbol == self.osymbol


class Fst:
    r''' 
    stores the symbol and graph data of FST. 
    Usage:
        # load FST from text file
        fst = Fst.from_text(isymbol_file, osymbol_file, fst_file) '''

    def __init__(self) -> None:
        r''' create a empty FST '''

        self._arcs: list[FstArc] = []

        # graph[src_state][isymbol] -> list[FstArc]
        self._graph: dict[int, dict[str, list[FstArc]]] = {}

        # final_states[state] -> final weight
        self._final_states: dict[int, float] = {}

    @classmethod
    def from_text(cls, ilabel_input: TextIO, olabel_input: TextIO, fst_input: TextIO) -> Fst:
        r''' 
        load fst from openFST format streams
        Args:
            ilabel_input (TextIO): ilabel symbol stream
            olabel_input (TextIO): olabel symbol stream
            fst_input (TextIO): fst stream 
        Returns:
            the Fst'''

        fst = Fst()

        isymbols = fst._read_symbols(ilabel_input)
        osymbols = fst._read_symbols(olabel_input)

        for line in fst_input:
            # src dest ilabel olabel [weight]  <- arc
            # state [weight]                   <- final state
            row = line.strip().split()
            if len(row) in {4, 5}:
                src_state = int(row[0])
                dest_state = int(row[1])
                ilabel = isymbols[int(row[2])]
                olabel = osymbols[int(row[3])]
                weight: float = 0
                if len(row) == 5:
                    weight = float(row[4])

                arc = FstArc(src_state, dest_state, ilabel, olabel, weight)
                fst._arcs.append(arc)

                # add arc to graph
                if src_state not in fst._graph:
                    fst._graph[src_state] = {}
                if ilabel not in fst._graph[src_state]:
                    fst._graph[src_state][ilabel] = []
                fst._graph[src_state][ilabel].append(arc)

            elif len(row) == 2:
                # final state
                state = int(row[0])
                weight = float(row[1])
                fst._final_states[state] = weight

            else:
                raise Exception(f'invalid line in fst stream: {line.strip()}')

        return fst

    def get_arcs(self, state: int, ilabel: str) -> list[FstArc]:
        r''' get arcs by specific input label of state '''
        if state not in self._graph:
            return []
        if ilabel not in self._graph[state]:
            return []
        return self._graph[state][ilabel]

    def get_final_weight(self, state: int) -> float:
        r''' get weights for final state, return NAN if it's not a final state '''
        return self._final_states.get(state, NAN)

    @staticmethod
    def _read_symbols(symbol_stream: TextIO) -> List[str]:
        r'''
        read symbol list from symbol_stream. the symbol list format is: <symbol> <symbol-id>\n
        State 0 is reserved for epsilon, so the symbol will be changed to an empty string.
        Args:
            symbol_stream (TextIO): the text stream for symbol list
        Returns:
            the symbol list'''

        symbols: list[str] = []
        for line in symbol_stream:
            row = line.strip().split()
            if len(row) != 2:
                raise Exception(f'invalid line in symbol_stream: {line.strip()}')
            symbol = row[0]
            symbol_id = int(row[1])

            # state 0 is reserved for epsilon
            if symbol_id == 0:
                symbol = ''

            while len(symbols) <= symbol_id:
                symbols.append('')
            symbols[symbol_id] = symbol

        return symbols
