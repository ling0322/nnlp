from __future__ import annotations
from telnetlib import BRK

import requests
import os
import re
import sys
import math

from os import path
from typing import TYPE_CHECKING


sys.path.append(path.join('..', '..', 'src', 'python3'))

from nnlp import Fst, Segmenter
from nnlp.symbol import BRK_SYM, EPS_SYM, escape_symbol, is_special_symbol
from nnlp.symbol import CAP_SYM, UNK_SYM
from nnlp_tools.util import lexicon_add_ilabel_selfloop
from nnlp_tools import build_lexicon_fst
from nnlp_tools.mutable_fst import MutableFst

if TYPE_CHECKING:
    from nnlp_tools.lexicon_fst_builder import Lexicon

REMOTE_DICT_URL = 'https://github.com/fxsjy/jieba/raw/67fa2e36e72f69d9134b8a1037b83fbb070b9775/extra_dict/'
LOCAL_DIR = 'exp'
UNK_WEIGHT = 10

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
    state_1 = breaker_fst.create_state()
    for _, symbol in lexicon_fst._osymbols:
        if not is_special_symbol(symbol):
            breaker_fst.add_arc(0, state_1, symbol, symbol)
    
    breaker_fst.add_arc(state_1, 0, EPS_SYM, BRK_SYM)
    breaker_fst.set_final_state(0)

    return breaker_fst

def postprocess_fst(fst: MutableFst):
    ''' postprocesses the wordseg FST, adding rules for handling English words
    and numbers
    '''
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_."
    state_c1 = fst.create_state()
    for ch in alphabet:
        fst.add_arc(0, state_c1, ch, ch, UNK_WEIGHT)
        fst.add_arc(state_c1, state_c1, ch, ch)
    fst.add_arc(state_c1, 0, EPS_SYM, BRK_SYM)

    for sym in [r'\s', r'\t', r'\r', r'\n']:
        fst.add_arc(0, 0, sym, BRK_SYM)


def e2e_test():
    fst = Fst.from_json('exp/wordseg.json')
    segmenter = Segmenter(fst)

    assert segmenter.segment_string('南京市长江大桥') == ['南京市', '长江大桥']
    assert segmenter.segment_string('研究生命的起源') == ['研究', '生命', '的', '起源']
    assert segmenter.segment_string('女朋友很重要吗') == ['女朋友', '很', '重要', '吗']
    assert segmenter.segment_string('北京大学生前来应聘') == ['北京', '大学生', '前来', '应聘']
    assert segmenter.segment_string('长春市长春药店') == ['长春市', '长春', '药店']
    assert segmenter.segment_string('你好hello你好现在是北京时间早上8点20左右') == ['你好', 'hello', '你好', '现在', '是', '北京', '时间', '早上', '8', '点', '20', '左右']
    assert segmenter.segment_string('嗨hello你好 world\t1.0a\tiPhone10\n\n\r22\n') == ['嗨', 'hello', '你好', 'world', '1.0a', 'iPhone10', '22']
    assert segmenter.segment_string('"233" hello-world i_0,AAC ') == ['"', '233', '"', 'hello-world', 'i_0', ',', 'AAC']


def run():
    ''' main function of run.py
    '''
    prepare_env()
    download_dict('dict.txt.small')
    print('read dict.txt.small')
    lexicon = read_jiebadict_to_lexicon(path.join(LOCAL_DIR, 'dict.txt.small'))
    lexicon = lexicon_add_ilabel_selfloop(lexicon)
    fst = build_lexicon_fst(lexicon)
    fst.print_info()

    fst_B = build_breaker_fst(fst)
    fst_B.print_info()

    fst = fst.compose(fst_B)
    fst.print_info()

    fst = fst.determinize()
    fst.print_info()
    fst = fst.rmdisambig()
    fst.print_info()
    fst = fst.rmepslocal()
    fst.print_info()
    fst = fst.minimize(allow_nondet=True)
    fst.print_info()

    # add rules for numbers, English words and spaces
    print(f'postprocess {fst.name}')
    postprocess_fst(fst)
    fst.print_info()

    # add selfloop for <unk> -> <capture> <brk>
    state_u1 = fst.create_state()
    for final_state in fst.final_states().keys():
        fst.add_arc(final_state, state_u1, UNK_SYM, CAP_SYM, 10)
    fst.add_arc(state_u1, 0, EPS_SYM, BRK_SYM)
    
    json_file = path.join(LOCAL_DIR, 'wordseg.json')
    print(f'save to {json_file}')
    with open(json_file, 'w', encoding='utf-8') as f:
        f.write(fst.to_json())
    
    print('start e2e test')
    e2e_test()
    print('success')

if __name__ == '__main__':
    run()

