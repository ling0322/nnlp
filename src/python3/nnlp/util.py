from __future__ import annotations

from typing import TYPE_CHECKING
from .symbol import EPS_SYM, UNK_SYM, Disambig, Epsilon, Unknown

if TYPE_CHECKING:
    from nnlp.symbol import Symbol

def encode_symbol(symbol: Symbol) -> str:
    ''' encode the symbol to string '''
    
    if isinstance(symbol, Disambig):
        return str(symbol)
    elif isinstance(symbol, Unknown):
        return str(UNK_SYM)
    elif isinstance(symbol, Epsilon):
        return str(EPS_SYM)
    elif isinstance(symbol, str):
        symbol = symbol.replace('\\', '\\\\')
        symbol = symbol.replace('#', '\\#')
        return symbol
    else:
        raise Exception('unexpected symbol type')
