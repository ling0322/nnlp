#!/bin/bash
set -e

export PYTHONPATH="$PWD/../../src/python3"
export PATH=$PATH:$PWD/../../target/nnlp_tools:$PWD/../common/util

print_fstinfo () {
  fstinfo $1 | egrep "(of states|of arcs|of final states|of .* epsilons)" | sed 's/  */ /g'
}

# test the nnlp module
python3 -c "import nnlp"

[[ -d exp ]] || mkdir exp

echo "download the zh-hant to zh-hans mapping table from snownlp"
data_url="https://raw.githubusercontent.com/isnowfy/snownlp/6c42a24fded438e3acdb06c8fc4705809f2d2b38/snownlp/normal/zh.py"
wget -O - $data_url | sed -n '8,3223p' | sed "s/'/\"/g"  | python3 -c '
import sys
import re

re_dict = re.compile(r"\s*\"(.*?)\": \"(.*?)\",\s*")

for line in sys.stdin:
    m = re_dict.match(line)
    symbols = " ".join(m.group(1))
    if m.group(2) == "" or m.group(1) == "":
        continue
    print(f"{m.group(2)} 0.99 {symbols}")
' > exp/t2s_lexicon.txt

build_lexicon_fst.sh exp/build_l exp/t2s_lexicon.txt exp/zhconv

convert_fst_to_json.sh exp/fst_to_json exp/zhconv exp/zhconv_t2s.json

echo "run e2e tests"
python3 local/test_t2s.py
echo "success"
