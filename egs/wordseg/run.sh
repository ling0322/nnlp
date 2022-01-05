#!/bin/bash
set -e

export PYTHONPATH="$PWD/../../src/python3"
export PATH=$PATH:$PWD/../../target/nnlp_tools:$PWD/../common/util

work_dir="$PWD"

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

[ -d exp ] || mkdir exp

local_data_dir=/mnt/d/data
[ -d $local_data_dir ] || mkdir $local_data_dir


if [ ! -f ../zhconv/exp/zhconv_t2s.json ]; then
  echo "build zh-hant to zh-hans FST"
  cd ../zhconv && ./run.sh
  cd $work_dir
fi
 
if [ ! -f $local_data_dir/dict.txt.big ] || [ ! -f $local_data_dir/dict.txt.small ]; then
  echo "download jieba dict"
  bigdict_url="https://github.com/fxsjy/jieba/raw/67fa2e36e72f69d9134b8a1037b83fbb070b9775/extra_dict/dict.txt.big"
  smalldict_url="https://github.com/fxsjy/jieba/raw/67fa2e36e72f69d9134b8a1037b83fbb070b9775/extra_dict/dict.txt.small"
  wget -O - $bigdict_url > $local_data_dir/dict.txt.big
  wget -O - $smalldict_url > $local_data_dir/dict.txt.small
fi

echo "process jieba dict"
cat $local_data_dir/dict.txt.small |\
  local/jieba_dict_to_lexicon.py |\
  lexicon_add_ilabel_selfloop.py > exp/lexicon.small.txt

cat local/lexicon_additional_selfloop.txt >> exp/lexicon.small.txt

echo "done"
echo

echo "build word segmentation FST:"
echo "----------------------------"
echo "B - Breaker FST, outputs <break> symbol after each word"
echo "L - Lexicon FST, from character to word"
echo "min - fstminimize"
echo "det - fstdeterminize"
echo "rds - remove disambiguation symbols from FST"
echo "rel - fstrmepslocal (remove epsilon from FST)"
echo

echo "L"
[ -d exp/build_fst ] && rm -r exp/build_fst
mkdir exp/build_fst
python3 -m nnlp_tools buildlexfst -escaped \
    -lexicon exp/lexicon.small.txt \
    -ilabel exp/build_fst/L.isyms.txt \
    -olabel exp/build_fst/L.osyms.txt \
    -fst exp/build_fst/L.txt \
    -output_disambig exp/build_fst/L.disambig.txt
fstcompile exp/build_fst/L.txt exp/build_fst/L.fst

print_fstinfo exp/build_fst/L.fst

echo "B"
local/build_breaker_fst.py -syms_file exp/build_fst/L.osyms.txt -out_prefix exp/build_fst/B
fstcompile exp/build_fst/B.txt | fstarcsort > exp/build_fst/B.fst
print_fstinfo exp/build_fst/B.fst

echo "L o B"
fstarcsort exp/build_fst/L.fst | fstcompose - exp/build_fst/B.fst exp/build_fst/LB.fst
print_fstinfo exp/build_fst/LB.fst

echo "det(L o B)"
fstdeterminize exp/build_fst/LB.fst exp/build_fst/LB.fst
print_fstinfo exp/build_fst/LB.fst

echo "rds(det(L o B))"
mv exp/build_fst/LB.fst exp/build_fst/LB.in.fst
fstprint exp/build_fst/LB.in.fst |\
  python3 -m nnlp_tools rmdisambig fst -syms exp/build_fst/L.isyms.txt |\
  fstcompile > exp/build_fst/LB.fst
print_fstinfo exp/build_fst/LB.fst
python3 -m nnlp_tools rmdisambig sym exp/build_fst/L.isyms.txt

echo "rel(rds(det(L o B)))"
fstrmepslocal exp/build_fst/LB.fst exp/build_fst/LB.fst
print_fstinfo exp/build_fst/LB.fst

echo "min(rel(rds(det(L o B))))"
fstminimize --allow_nondet exp/build_fst/LB.fst exp/build_fst/LB.fst
print_fstinfo exp/build_fst/LB.fst

cp exp/build_fst/L.isyms.txt exp/build_fst/LB.isyms.txt
cp exp/build_fst/B.osyms.txt exp/build_fst/LB.osyms.txt

convert_fst_to_json.sh exp/fst_to_json exp/build_fst/LB exp/wordseg.json
echo "success"
echo

echo "run e2e test"
local/test_wordseg.py
echo "success"
