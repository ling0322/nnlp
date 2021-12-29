from __future__ import annotations

from typing import TYPE_CHECKING, TextIO, Union
import json

from .symbol import EPS_SYM, UNK_SYM

NAN = float('nan')

if TYPE_CHECKING:
    FstArcTarget = tuple[int, int, float]

class Fst:
    r''' 
    stores the symbol and graph data of FST. 
    Usage:
        # load FST from text file
        fst = Fst.from_text(isymbol_file, osymbol_file, fst_file) '''


    def __init__(self) -> None:
        r''' create a empty FST '''

        # graph[src_state][isymbol_encoded] -> list[tuple[tgt_state, osymbol, weight]]
        # or 
        self._graph: list[dict[str, list[tuple[int, str, float]]]] = []

        # weights for final states
        self._final_weights: dict[int, float] = {}

        # all input string symbols
        self._isymbol_dict: dict[str, int] = {}


    def to_json(self, f_json: TextIO) -> None:
        ''' dump the FST to json file '''

        graph = self._graph
        final_weights = list(self._final_weights.items())
        isymbol_dict = self._isymbol_dict

        o = dict(
            version=1,
            graph=graph,
            isymbol_dict=isymbol_dict,
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

        isymbols: list[str] = fst._read_symbols(ilabel_input)
        for isym_id, isymbol in enumerate(isymbols):
            fst._isymbol_dict[isymbol] = isym_id
        osymbols = fst._read_symbols(olabel_input)

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
                
                # we assuming the symbols is already escaped
                isymbol = isymbols[isymbol_id]
                osymbol = osymbols[osymbol_id]

                # add arc to graph
                while len(fst._graph) <= src_state:
                    fst._graph.append(dict())
                if isymbol not in fst._graph[src_state]:
                    fst._graph[src_state][isymbol] = []
                fst._graph[src_state][isymbol].append((dest_state, osymbol, weight))

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

    def get_arcs(self, state: int, isymbol: str) -> list[tuple[int, str, float]]:
        r''' get arcs by specific input label of state returns (dest_state, osymbol, weight) '''

        if isymbol not in self._graph[state]:
            return []
        return self._graph[state][isymbol]

    def get_final_weight(self, state: int) -> float:
        r''' get weights for final state, return NAN if it's not a final state '''
        return self._final_weights.get(state, NAN)

    @staticmethod
    def _read_symbols(symbol_stream: TextIO) -> list[str]:
        r'''
        read symbol list from symbol_stream. the symbol list format is: <symbol> <symbol-id>\n
        Args:
            symbol_stream (TextIO): the text stream for symbol list
        Returns:
            the list from symbol-id to symbol'''

        symbols: dict[int, str] = {}
        for line in symbol_stream:
            row = line.strip().split()
            if len(row) != 2:
                raise Exception(f'invalid line in symbol_stream: {line.strip()}')
            symbol: str = row[0]
            symbol_id = int(row[1])

            symbols[symbol_id] = symbol

        symbol_list: list[str] = []
        for symbol_id, sym in symbols.items():
            while len(symbol_list) <= symbol_id:
                symbol_list.append(EPS_SYM)
            symbol_list[symbol_id] = sym

        return symbol_list
