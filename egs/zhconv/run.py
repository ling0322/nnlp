from __future__ import annotations

import requests
import os
import re
import sys
import math

from os import path
from typing import TYPE_CHECKING

sys.path.append(path.join('..', '..', 'src', 'python3'))

from nnlp import Fst, Converter
from nnlp.symbol import CAP_SYM, UNK_SYM
from nnlp_tools.util import lexicon_add_ilabel_selfloop
from nnlp_tools import build_lexicon_fst

if TYPE_CHECKING:
    from nnlp_tools.lexicon_fst_builder import Lexicon

RULE_URL = "https://raw.githubusercontent.com/isnowfy/snownlp/6c42a24fded438e3acdb06c8fc4705809f2d2b38/snownlp/normal/zh.py"
RULE_PATH = path.join('exp', 'zh.py')

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
    os.makedirs('exp', exist_ok = True)

def download_rules() -> None:
    ''' download the Chinese Traditional to Simplified rules from SnowNLP '''

    if path.exists(RULE_PATH):
        # just skip this step if file already downloaded
        return
    
    try:
        download_file(RULE_URL, RULE_PATH)
    except Exception as e:
        print(f'download rules failed: {e}')
        print(f'please download it manually from "{RULE_URL}" and save to "{RULE_PATH}"')
        sys.exit(22)

def read_rules() -> Lexicon:
    ''' read rules from RULE_PATH and return as Lexicon '''

    with open(RULE_PATH, encoding='utf-8') as f:
        lines = list(f)
    
    lexicon: list[tuple[str, list[str], float]] = []
    re_dict = re.compile(r"\"(.*?)\": \"(.*?)\",")
    for line in lines[8: 3223]:
        line = line.strip()
        line = line.replace("'", '"')
        m = re_dict.match(line)
        assert(m)

        word_t = m.group(1)
        word_s = m.group(2)
        if word_t and word_s:
            lexicon.append((word_s, list(word_t), -math.log(0.99)))

    return lexicon

def e2e_test():
    fst = Fst.from_json('exp/zhconv_t2s.json')
    converter = Converter(fst)

    assert converter.convert_string('肯德基要點的是原始的薄皮嫩雞') == '肯德基要点的是原始的薄皮嫩鸡'
    assert converter.convert_string('一堆人吃辣的卡拉雞，那個才不是經典') == '一堆人吃辣的卡拉鸡，那个才不是经典'
    assert converter.convert_string('薄皮嫩雞裹粉多汁，好餓…') == '薄皮嫩鸡裹粉多汁，好饿…'
    assert converter.convert_string('然後漢堡王要點是薯球，其他都不行，漢堡說實在也還好') == '然后汉堡王要点是薯球，其他都不行，汉堡说实在也还好'
    assert converter.convert_string('摩斯要點的是紅茶，漢堡他經典好吃的品項都下架了') == '摩斯要点的是红茶，汉堡他经典好吃的品项都下架了'
    assert converter.convert_string('麥當勞越漲越貴，還有人說便宜，真TM笑死') == '麦当劳越涨越贵，还有人说便宜，真TM笑死'
    assert converter.convert_string('沙烏地阿拉伯或譯') == '沙特阿拉伯或译'
    assert converter.convert_string('波士尼亞赫塞哥維') == '波士尼亚赫塞哥维'


def run() -> None:
    ''' main function of run.py '''

    prepare_env()
    download_rules()
    lexicon = read_rules()
    lexicon = lexicon_add_ilabel_selfloop(lexicon)
    fst = build_lexicon_fst(lexicon)
    fst.print_info()
    fst = fst.determinize()
    fst.print_info()
    fst = fst.rmdisambig()
    fst.print_info()
    fst = fst.rmepslocal()
    fst.print_info()
    fst = fst.minimize(allow_nondet=True)
    fst.print_info()

    # add selfloop for <unk> -> <capture>
    for final_state in fst.final_states().keys():
        fst.add_arc(final_state, 0, UNK_SYM, CAP_SYM, 10)
    
    json_file = path.join('exp', 'zhconv_t2s.json')
    print(f'save to {json_file}')
    with open(json_file, 'w', encoding='utf-8') as f:
        f.write(fst.to_json())

    e2e_test()
    print(f'e2e test success')

if __name__ == '__main__':
    run()
