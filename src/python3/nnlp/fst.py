from __future__ import annotations

import abc
from typing import List, TextIO
from operator import itemgetter

from .symbol import EPS_SYM, EPS_SYM_ID, MAX_SYMBOLS, NUM_RESERVED_SYM, UNK_SYM, UNK_SYM_ID, Disambig, Epsilon, Symbol, Unknown

NAN = float('nan')


class FSTWriter(abc.ABC):
    r''' base class for Fst writer that supports add arc, add state and set final state '''

    @abc.abstractmethod
    def add_arc(
        self,
        src_state: int,
        dest_state: int,
        isymbol: Symbol,
        osymbol: Symbol,
        weight: float = 0.0,
    ) -> None:
        r''' 
        add an arc to Fst 
            Args:
            src_state (int): source state
            dest_state (int): destination state
            isymbol (Symbol): input symbol
            osymbol (Symbol): output symbol
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
                 olabel_stream: TextIO) -> None:
        self._isymbols: dict[str, int] = {}
        self._osymbols: dict[str, int] = {}
        self._disambig_symbol_ids: set[int] = set()
        self._n_states = 1
        self._fst_stream: TextIO = fst_stream
        self._ilabel_stream: TextIO = ilabel_stream
        self._olabel_stream: TextIO = olabel_stream

        self._symbol_table_written = False
        self._disambig_start_idx = MAX_SYMBOLS

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
                isymbol: Symbol,
                osymbol: Symbol,
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

        self._write_eps_symbol(self._ilabel_stream)
        self._write_unk_symbol(self._ilabel_stream)
        self._write_symbol_table(self._isymbols, self._ilabel_stream)
        if self._disambig_symbol_ids:
            self._write_disambig_symbols(self._ilabel_stream)

        self._write_eps_symbol(self._olabel_stream)
        self._write_unk_symbol(self._olabel_stream)
        self._write_symbol_table(self._osymbols, self._olabel_stream)

        self._symbol_table_written = True

    def _write_unk_symbol(self, stream: TextIO) -> None:
        ''' write unknown symbol to stream '''

        stream.write(f'{self._generate_name("unk")} {UNK_SYM_ID}\n')

    def _write_eps_symbol(self, stream: TextIO) -> None:
        ''' write epsilon symbol to stream '''

        stream.write(f'{self._generate_name("eps")} {EPS_SYM_ID}\n')

    def _write_symbol_table(self, symbol_table: dict[str, int], stream: TextIO) -> None:
        ''' write symbol table to a stream '''

        symbols = list(symbol_table.items())
        symbols.sort(key=itemgetter(1))

        for symbol, symbol_id in symbols:
            stream.write(f'{symbol} {symbol_id}\n')

    def _write_disambig_symbols(self, stream: TextIO) -> None:
        ''' write disambiguation symbols to stream '''

        disambig_symbol_ids = list(self._disambig_symbol_ids)
        disambig_symbol_ids.sort()

        for symbol_id in disambig_symbol_ids:
            name = f'{symbol_id}'
            symbol = self._generate_name(name)
    
            stream.write(f'{symbol} {self._disambig_start_idx + symbol_id}\n')


    def _generate_name(self, name: str) -> str:
        ''' generate a symbol name that not conflict with current input and output symbol table '''

        prefix = ''
        final_name = f'#{prefix}{name}'
        while final_name in self._osymbols or final_name in self._isymbols:
            prefix += '_'
            final_name = f'#{prefix}{name}'

        return final_name



    def _get_symbol_id(self, symbol: Symbol, symbol_dict: dict[str, int]) -> int:
        r''' get id of a input symbol from symbol_dict, it will create a new symbol id if 
        symbol not exist in symbol_dict '''

        if isinstance(symbol, Disambig):
            self._disambig_symbol_ids.add(symbol.symbol_id)
            return self._disambig_start_idx + symbol.symbol_id
        elif isinstance(symbol, Epsilon):
            return EPS_SYM_ID
        elif isinstance(symbol, Unknown):
            return UNK_SYM_ID

        if symbol == '':
            raise Exception(f'empty symbol is not supported, use EPS_SYM instead?')

        if symbol not in symbol_dict:
            symbol_id = len(symbol_dict) + NUM_RESERVED_SYM
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

    def __init__(self, src_state: int, dest_state: int, isymbol: Symbol, osymbol: Symbol,
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


    _eps_isymbol: str
    _unk_isymbol: str
    _eps_osymbol: str
    _unk_osymbol: str

    def __init__(self) -> None:
        r''' create a empty FST '''

        self._arcs: list[FstArc] = []

        # graph[src_state][isymbol] -> list[FstArc]
        self._graph: dict[int, dict[str, list[FstArc]]] = {}

        # final_states[state] -> final weight
        self._final_states: dict[int, float] = {}

        # input symbols
        self._isymbols: set[str] = set()


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

        fst._eps_isymbol = isymbols[EPS_SYM_ID]
        fst._unk_isymbol = isymbols[UNK_SYM_ID]
        fst._eps_osymbol = osymbols[EPS_SYM_ID]
        fst._unk_osymbol = osymbols[UNK_SYM_ID]

        for line in fst_input:
            # src dest ilabel olabel [weight]  <- arc
            # state [weight]                   <- final state
            row = line.strip().split()
            if len(row) in {4, 5}:
                src_state = int(row[0])
                dest_state = int(row[1])
                ilabel: str = isymbols[int(row[2])]
                olabel: str = osymbols[int(row[3])]
                weight: float = 0
                if len(row) == 5:
                    weight = float(row[4])

                isymbol: Symbol = ilabel
                if ilabel == fst._eps_isymbol:
                    isymbol = EPS_SYM
                elif ilabel == fst._unk_isymbol:
                    isymbol = UNK_SYM

                osymbol: Symbol = olabel
                if olabel == fst._eps_osymbol:
                    osymbol = EPS_SYM
                elif olabel == fst._unk_osymbol:
                    osymbol = UNK_SYM

                arc = FstArc(src_state, dest_state, isymbol, osymbol, weight)
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

    def get_arcs(self, state: int, isymbol: Symbol) -> list[FstArc]:
        r''' get arcs by specific input label of state '''

        if isinstance(isymbol, str):
            ilabel = isymbol
        elif isinstance(isymbol, Unknown):
            ilabel = self._unk_isymbol
        elif isinstance(isymbol, Epsilon):
            ilabel = self._eps_isymbol
        else:
            raise Exception(f'unexapcted isymbol: {isymbol}')

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
            symbol: str = row[0]
            symbol_id = int(row[1])

            if symbol_id > MAX_SYMBOLS:
                raise Exception('unexpceted symbol-id (forgot to remove disambig symbols?)')

            while len(symbols) <= symbol_id:
                # '' not now allowed as a symbol, we will check it later
                symbols.append('')
            symbols[symbol_id] = symbol
        
        
        if len(symbols) < 2 or symbols[1] == '' or symbols[0] == '':
            raise Exception(f'eps (0) and unk (1) should exist in symbol file')

        if symbols[0][0] != '#' or symbols[1][0] != '#':
            raise Exception(f'unexpected symbol file: 0 is reserved for epsilon and 1 is reserved for unk')


        for idx, symbol in enumerate(symbols):
            if symbol == '':
                symbols[idx] = symbols[0]

        return symbols
