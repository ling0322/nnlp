#!/bin/bash
set -e

export PYTHONPATH="$PWD/../../src/python3"
export PATH=$PATH:$PWD/../../target/nnlp_tools

stage=2


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

echo "build t2s FST"
python3 -m nnlp build_lexicon_fst -input exp/t2s_lexicon.txt \
                                  -ilabel exp/ilabel.txt \
                                  -olabel exp/olabel.txt \
                                  -fst exp/lexicon.fst.txt \
                                  -output_disambig exp/t2s_lexicon.disambig.txt \
                                  -unknown_symbol output


echo "optimize t2s FST"
echo "Lexicon"
fstcompile exp/lexicon.fst.txt exp/lexicon.fst
print_fstinfo exp/lexicon.fst
rm exp/lexicon.fst.txt
echo $'Done!\n'

echo "det(Lexicon)"
fstdeterminize exp/lexicon.fst exp/lexicon.det.fst
print_fstinfo exp/lexicon.det.fst
rm exp/lexicon.fst
echo $'Done!\n'

echo "min(det(Lexicon))"
fstminimize exp/lexicon.det.fst exp/lexicon.det.min.fst
print_fstinfo exp/lexicon.det.min.fst
rm exp/lexicon.det.fst
echo $'Done!\n'

echo "rmd(min(det(Lexicon)))"
fstprint exp/lexicon.det.min.fst > exp/lexicon.det.min.fst.txt
python3 -m nnlp rm_disambig -input_fst exp/lexicon.det.min.fst.txt -output exp/lexicon.det.min.rmd.fst.txt
fstcompile exp/lexicon.det.min.rmd.fst.txt exp/lexicon.det.min.rmd.fst
print_fstinfo exp/lexicon.det.min.rmd.fst
rm exp/lexicon.det.min.fst.txt exp/lexicon.det.min.rmd.fst.txt
echo $'Done!\n'

echo "rms(rmd(min(det(Lexicon))))"
fstrmepslocal exp/lexicon.det.min.rmd.fst exp/lexicon.det.min.rmd.rms.fst
print_fstinfo exp/lexicon.det.min.rmd.rms.fst
rm exp/lexicon.det.min.rmd.fst
echo $'Done!\n'

echo "save FST as json format"
fstprint exp/lexicon.det.min.rmd.rms.fst > exp/lexicon.det.min.rmd.rms.fst.txt

python3 -m nnlp rm_disambig -input_lexicon exp/ilabel.txt -output exp/ilabel.rmd.txt
python3 local/convert_fst_to_json.py -ilabel exp/ilabel.rmd.txt \
                                     -olabel exp/olabel.txt \
                                     -fst exp/lexicon.det.min.rmd.rms.fst.txt \
                                     -output_json exp/zh_t2s.json
rm exp/lexicon.det.min.rmd.rms.fst.txt
mv exp/lexicon.det.min.rmd.rms.fst exp/lexicon.optim.fst
echo $'Done!\n'

echo "run e2e tests"
python3 local/test_t2s.py
echo $'Done!\n'
