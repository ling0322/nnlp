''' symbols for FST '''
from __future__ import annotations
from typing import Any, Optional, Union

class Epsilon:
    ''' represents an epsilon symbol in fst '''
    _inst: Optional[Epsilon] = None

    def __new__(cls) -> Epsilon:
        if cls._inst:
            return cls._inst
        eps = super(Epsilon, cls).__new__(cls)
        cls._inst = eps

        return eps

    def __str__(self) -> str:
        return f'<eps>'

    def __repe__(self) -> str:
        return f'Epsilon()'

class Unknown:
    ''' represents an unknown symbol in fst '''

    _inst: Optional[Unknown] = None

    def __new__(cls) -> Unknown:
        if cls._inst:
            return cls._inst
        unk = super(Unknown, cls).__new__(cls)
        cls._inst = unk

        return unk

    def __str__(self) -> str:
        return f'#_unk'

    def __repe__(self) -> str:
        return f'Unknown()'

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

    def __str__(self) -> str:
        return f'#_disambig_{self.symbol_id}'

    def __repr__(self) -> str:
        return f'Disambig({self.symbol_id})'

EPS_SYM = Epsilon()
EPS_SYM_ID = 0
UNK_SYM = Unknown()
UNK_SYM_ID = 1

NUM_RESERVED_SYM = 2
MAX_SYMBOLS = 10000000

Symbol = Union[str, Epsilon, Unknown, Disambig]
