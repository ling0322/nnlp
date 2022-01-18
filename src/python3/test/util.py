''' utility for testing '''
from __future__ import annotations


def trim_text(text: str) -> str:
    ''' removing leading space in text'''

    return '\n'.join(map(lambda t: t.strip(), text.split('\n')))


def norm_textfst(text: str) -> str:
    ''' normalize text format of FST '''

    text = text.replace('\t', ' ')
    lines = text.split('\n')
    lines = list(map(lambda t: t.strip(), lines))
    if lines[0] == '':
        lines = lines[1:]

    return '\n'.join(lines)
