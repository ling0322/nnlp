from __future__ import annotations

import abc
from typing import TYPE_CHECKING, List, Sequence, TextIO, Union
from operator import itemgetter
import json

from .util import encode_symbol
from .symbol import EPS_SYM, EPS_SYM_ID, MAX_SYMBOLS, NUM_RESERVED_SYM, UNK_SYM, UNK_SYM_ID, Disambig, Epsilon, Symbol, Unknown

NAN = float('nan')

if TYPE_CHECKING:
    FstArcTarget = tuple[int, int, float]

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

class Fst:
    r''' 
    stores the symbol and graph data of FST. 
    Usage:
        # load FST from text file
        fst = Fst.from_text(isymbol_file, osymbol_file, fst_file) '''


    def __init__(self) -> None:
        r''' create a empty FST '''

        # graph[src_state][isymbol_encoded] -> list[tuple[tgt_state, osymbol_id, weight]]
        # or 
        self._graph: list[dict[str, list[tuple[int, int, float]]]] = []

        # weights for final states
        self._final_weights: dict[int, float] = {}

        # all input string symbols
        self._isymbol_dict: dict[str, int] = {}

        # list of output symbols: osymbol = _osymbols[osymbol_id]
        self._osymbols: list[Symbol] = []


    def to_json(self, f_json: TextIO) -> None:
        ''' dump the FST to json file '''

        graph = self._graph
        final_weights = list(self._final_weights.items())
        isymbol_dict = self._isymbol_dict
        osymbols = list(map(str, self._osymbols))

        o = dict(
            version=1,
            graph=graph,
            isymbol_dict=isymbol_dict,
            osymbols=osymbols,
            final_weights=final_weights
        )
        return json.dump(o, f_json, separators=(',', ':'))

    @classmethod
    def from_json(cls, f_json: Union[TextIO, str]) -> Fst:
        ''' load FST from json file '''

        fst = Fst()
        if isinstance(f_json, str):
            with open(f_json, encoding='utf-8') as f:
                o = json.load(f)
        else:
            o = json.load(f_json)

        fst._graph = o['graph']
        fst._isymbol_dict = o['isymbol_dict']
        fst._final_weights = dict(o['final_weights'])

        fst._osymbols = o['osymbols']
        fst._osymbols[EPS_SYM_ID] = EPS_SYM
        fst._osymbols[UNK_SYM_ID] = UNK_SYM

        return fst

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

        isymbols: list[Symbol] = fst._read_symbols(ilabel_input)
        for isym_id, isymbol in enumerate(isymbols):
            if isinstance(isymbol, str):
                fst._isymbol_dict[isymbol] = isym_id
        fst._osymbols = fst._read_symbols(olabel_input)

        for line in fst_input:
            # src dest ilabel olabel [weight]  <- arc
            # state [weight]                   <- final state
            row = line.strip().split()
            if len(row) in {4, 5}:
                src_state = int(row[0])
                dest_state = int(row[1])
                isymbol_id: int = int(row[2])
                osymbol_id: int = int(row[3])
                weight: float = 0
                if len(row) == 5:
                    weight = float(row[4])

                isymbol = isymbols[isymbol_id]
                isymbol_encoded = encode_symbol(isymbol)

                # add arc to graph
                while len(fst._graph) <= src_state:
                    fst._graph.append(dict())
                if isymbol_encoded not in fst._graph[src_state]:
                    fst._graph[src_state][isymbol_encoded] = []
                fst._graph[src_state][isymbol_encoded].append((dest_state, osymbol_id, weight))

            elif len(row) in {1, 2}:
                # final state
                state = int(row[0])
                weight = 0
                if len(row) == 2:
                    weight = float(row[1])
                fst._final_weights[state] = weight

            else:
                raise Exception(f'invalid line in fst stream: {line.strip()}')

        return fst

    @property
    def isymbol_dict(self) -> dict[str, int]:
        ''' get the input symbol to input symbol id mapping dict '''

        return self._isymbol_dict

    def get_arcs(self, state: int, isymbol: Symbol) -> list[tuple[int, int, float]]:
        r''' get arcs by specific input label of state returns (dest_state, osymbol_id, weight) '''

        isymbol_encoded = encode_symbol(isymbol)

        if isymbol_encoded not in self._graph[state]:
            return []
        return self._graph[state][isymbol_encoded]

    def get_final_weight(self, state: int) -> float:
        r''' get weights for final state, return NAN if it's not a final state '''
        return self._final_weights.get(state, NAN)

    def get_osymbol(self, osymbol_id) -> Symbol:
        ''' get output symbol by id '''

        return self._osymbols[osymbol_id]

    @staticmethod
    def _read_symbols(symbol_stream: TextIO) -> list[Symbol]:
        r'''
        read symbol list from symbol_stream. the symbol list format is: <symbol> <symbol-id>\n
        It will also change EPS and UNK symbols to Epsilon() and Unknown()
        Args:
            symbol_stream (TextIO): the text stream for symbol list
        Returns:
            the dict[symbol_id: int, symbol: Symbol]'''

        symbols: dict[int, Symbol] = {}
        for line in symbol_stream:
            row = line.strip().split()
            if len(row) != 2:
                raise Exception(f'invalid line in symbol_stream: {line.strip()}')
            symbol: str = row[0]
            symbol_id = int(row[1])

            if symbol_id > MAX_SYMBOLS:
                raise Exception('unexpceted symbol-id (forgot to remove disambig symbols?)')

            symbols[symbol_id] = symbol
        
        if EPS_SYM_ID not in symbols or UNK_SYM_ID not in symbols:
            raise Exception(f'eps ({EPS_SYM_ID}) and unk ({UNK_SYM_ID}) should exist in symbol file')

        eps_sym = symbols[EPS_SYM_ID]
        unk_sym = symbols[UNK_SYM_ID]
        assert isinstance(eps_sym, str) and isinstance(unk_sym, str)
        if eps_sym[0] != '#' or unk_sym[0] != '#':
            raise Exception(f'unexpected symbol file: 0 is reserved for epsilon and 1 is reserved for unk')

        symbols[EPS_SYM_ID] = EPS_SYM
        symbols[UNK_SYM_ID] = UNK_SYM

        symbol_list: list[Symbol] = []
        for symbol_id, sym in symbols.items():
            while len(symbol_list) <= symbol_id:
                symbol_list.append(EPS_SYM)
            symbol_list[symbol_id] = sym

        return symbol_list
