''' symbols for FST '''
from __future__ import annotations

def escape_symbol(symbol: str) -> str:
    ''' escape a symbol '''

    value = symbol
    value = value.replace('\\', '\\\\')
    value = value.replace('<', '\\<')
    value = value.replace('>', '\\>')
    value = value.replace('#', '\\#')
    value = value.replace('\t', '\\t')
    value = value.replace(' ', '\\s')
    value = value.replace('\n', '\\n')
    value = value.replace('\r', '\\r')
    return value

def unescape_symbol(symbol: str) -> str:
    ''' unescape a symbol '''

    value = symbol
    value = value.replace('\\<', '<')
    value = value.replace('\\>', '>')
    value = value.replace('\\#', '#')
    value = value.replace('\\s', ' ')
    value = value.replace('\\t', '\t')
    value = value.replace('\\n', '\n')
    value = value.replace('\\r', '\r')
    value = value.replace('\\\\', '\\')
    return value

def is_special_symbol(symbol: str) -> bool:
    ''' return true if it is a special symbol like: <eps>, #1, #2, ... '''

    return symbol[0] in {'<', '#'}

def is_disambig_symbol(symbol: str) -> bool:
    ''' returns true if it is a disambig symbol '''

    return symbol[0] == '#'

def make_disambig_symbol(disambig_id: int) -> str:
    ''' returns the disambig symbol by its id '''

    return f'#{disambig_id}'

# both input and output symbol
EPS_SYM = '<eps>'

# input symbols
UNK_SYM = '<unk>'
ANY_SYM = '<any>'

# only for output symbols, <capture> and <capture_eps> are used in pair with <unk> and <any> 
# <capture> means unknwon or any matched and output the captured symbol
# <capture_eps> means unknwon or any matched but do not output anything
CAP_SYM = '<capture>'
CAP_EPS_SYM = '<capture_eps>'  

# for Segmenters
BRK_SYM = '<break>'
