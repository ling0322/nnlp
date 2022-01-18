from __future__ import annotations

from typing import TYPE_CHECKING, TextIO, Union
import json

from .symbol import EPS_SYM, UNK_SYM

NAN = float('nan')

if TYPE_CHECKING:
    FstArcTarget = tuple[int, int, float]

class Fst:
    r''' 
    stores the symbol and graph data of a const FST. 
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
