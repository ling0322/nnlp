''' utility for testing '''
from __future__ import annotations

def trim_text(text: str) -> str:
    ''' removing leading space in text'''

    return '\n'.join(map(lambda t: t.strip(), text.split('\n')))