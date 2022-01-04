#!/bin/bash
set -e

export PYTHONPATH="$PWD/../../src/python3"
export PATH=$PATH:$PWD/../../target/nnlp_tools:$PWD/../common/util

print_fstinfo () {
  fstinfo $1 | egrep "(of states|of arcs|of final states|of .* epsilons)" | sed 's/  */ /g'

  # exit when FST is empty
  num_arcs=$(fstinfo $1 | grep "# of arcs" | sed 's/# of arcs *//g')
  if [ $num_arcs -le 0 ]; then
    echo "failed: FST is empty"
    exit 1
  fi

  echo
}


# test the nnlp module
python3 -c "import nnlp"

[[ -d exp ]] || mkdir exp


local_data_dir=/mnt/d/data
[ -d $local_data_dir ] || mkdir $local_data_dir

if [ ! -f $local_data_dir/t2s_lexicon.txt ]; then
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
  ' | lexicon_add_ilabel_selfloop.py > $local_data_dir/t2s_lexicon.txt
fi

echo "build chinese t2s FST:"
echo "----------------------------"
echo "L - Lexicon FST, from CHT to CHS"
echo "min - fstminimize"
echo "det - fstdeterminize"
echo "rds - remove disambiguation symbols from FST"
echo "rel - fstrmepslocal (remove epsilon from FST)"
echo

echo "L"
[ -d exp/build_fst ] && rm -r exp/build_fst
mkdir exp/build_fst
python3 -m nnlp_tools buildlexfst \
    -lexicon $local_data_dir/t2s_lexicon.txt \
    -ilabel exp/build_fst/L.isyms.txt \
    -olabel exp/build_fst/L.osyms.txt \
    -fst exp/build_fst/L.txt \
    -output_disambig exp/build_fst/L.disambig.txt
fstcompile exp/build_fst/L.txt exp/build_fst/L.fst
print_fstinfo exp/build_fst/L.fst

echo "det(L)"
fstdeterminize exp/build_fst/L.fst exp/build_fst/L.fst
print_fstinfo exp/build_fst/L.fst

echo "rds(det(L))"
mv exp/build_fst/L.fst exp/build_fst/L.in.fst
fstprint exp/build_fst/L.in.fst |\
  python3 -m nnlp_tools rmdisambig fst -syms exp/build_fst/L.isyms.txt |\
  fstcompile > exp/build_fst/L.fst
python3 -m nnlp_tools rmdisambig sym exp/build_fst/L.isyms.txt
print_fstinfo exp/build_fst/L.fst

echo "rel(rds(det(L)))"
fstrmepslocal exp/build_fst/L.fst exp/build_fst/L.fst
print_fstinfo exp/build_fst/L.fst

echo "min(rel(rds(det(L))))"
fstminimize --allow_nondet exp/build_fst/L.fst exp/build_fst/L.fst

# handle unknown symbol
add_selfloop.sh exp/build_fst/L "<unk>" "<capture>" 
print_fstinfo exp/build_fst/L.fst

convert_fst_to_json.sh exp/fst_to_json exp/build_fst/L exp/zhconv_t2s.json

echo "run e2e tests"
python3 local/test_t2s.py
echo "success"
