from __future__ import annotations

import requests
import os
import re
import sys
import math

from os import path
from typing import TYPE_CHECKING

from nnlp_tools.mutable_fst import MutableFst

sys.path.append(path.join('..', '..', 'src', 'python3'))

from nnlp import Fst, Converter
from nnlp.symbol import escape_symbol
from nnlp.symbol import CAP_SYM, UNK_SYM
from nnlp_tools.util import lexicon_add_ilabel_selfloop
from nnlp_tools import build_lexicon_fst

if TYPE_CHECKING:
    from nnlp_tools.lexicon_fst_builder import Lexicon

REMOTE_DICT_URL = 'https://github.com/fxsjy/jieba/raw/67fa2e36e72f69d9134b8a1037b83fbb070b9775/extra_dict/'
LOCAL_DIR = 'exp'


def download_file(url: str, filename: str):
    '''
    download a file from url to filename
    Args:
        url: url of remote file
        filename: path of the local file to write
    '''
    with requests.get(url, stream=True) as res:
        res.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in res.iter_content(chunk_size=4096):
                f.write(chunk)


def prepare_env() -> None:
    ''' prepare the environment for this script '''
    os.makedirs('exp', exist_ok=True)


def download_dict(filename: str) -> None:
    ''' download the file to local '''

    if path.exists(path.join(LOCAL_DIR, filename)):
        # just skip this step if file already downloaded
        return

    try:
        remote_url = REMOTE_DICT_URL + filename
        local_path = path.join(LOCAL_DIR, filename)
        download_file(remote_url, local_path)
    except Exception as e:
        print(f'download rules failed: {e}')
        print(
            f'please download it manually from "{remote_url}" and save to "{local_path}"'
        )
        sys.exit(22)


def read_jiebadict_to_lexicon(filename: str) -> Lexicon:
    ''' read jieba dict and convert it to Lexicon
    '''
    lexicon: Lexicon = []
    freq = {}
    with open(filename, encoding='utf-8') as f:
        for line in f:
            row = line.strip().split()
            word = row[0]
            count = int(row[1])
            freq[word] = count

    total_count = sum(freq.values())
    for word, count in freq.items():
        lexicon.append((
            escape_symbol(word),
            tuple(map(escape_symbol, word)),
            -math.log(count / total_count),
        ))
    
    return lexicon

def build_breaker_fst(lexicon_fst: MutableFst) -> MutableFst:
    ''' build breaker FST according to lexicon FST. Breaker FST outputs <brk>
    symbols after any output symbol in lexicon_fst
    '''
    breaker_fst = MutableFst(isymbols=lexicon_fst._osymbols, name="B")
    
