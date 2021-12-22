''' symbols for FST '''
from __future__ import annotations
from typing import Any, Optional, Union

class Epsilon:
    ''' represents an epsilon symbol in fst '''

    def __str__(self) -> str:
        return f'#eps'

    def __eq__(self, o: Any) -> bool:
        return isinstance(o, Epsilon)

class Unknown:
    ''' represents an unknown symbol in fst
    Args:
        symbol_id: id of unknown symbol '''

    def __init__(self, symbol_id: int = 0) -> None:
        self.symbol_id = symbol_id

    def __str__(self) -> str:
        if self.symbol_id == 0:
            return f'#unk'
        else:
            return f'#unk_{self.symbol_id}'

    def __eq__(self, o: Any) -> bool:
        return isinstance(o, Unknown) and self.symbol_id == o.symbol_id

class Disambig:
    ''' represent disambiguation symbol #1, #2, #3, ... in Fst
    Args:
        symbol_id: id of disambiguation symbol, 1 for #1, 2 for #2, ... '''

    def __init__(self, symbol_id: int) -> None:
        self.symbol_id = symbol_id

    def __str__(self) -> str:
        return f'#{self.symbol_id}'

    def __eq__(self, o: Any) -> bool:
        return isinstance(o, Disambig) and self.symbol_id == o.symbol_id

EPS_SYM = Epsilon()
EPS_SYM_ID = 0
UNK_SYM = Unknown()
UNK_SYM_ID = 1

NUM_RESERVED_SYM = 2
MAX_SYMBOLS = 10000000

Symbol = Union[str, Epsilon, Unknown, Disambig]
