#!/bin/bash

set -e

work_dir=$1
input_fst_prefix=$2
output_json=$3

if [ -z "$work_dir" ] || [ -z "$input_fst_prefix" ] || [ -z "$output_json" ] ; then
  echo "Convert FST to nnlp-json format. "
  echo "Usage: convert_fst_to_json.sh <work-dir> <input-fst-prefix> <output-json>"
  echo "    work-dir: the directory thst stores intermediate files"
  echo "    input-fst-prefix: prefix for the input FST, including <prefix>.fst, <prefix>.isyms.txt, <prefix>.osyms.txt"
  echo "    output-json: output nnlp-json format FST"

  exit 1
fi

[ -d $work_dir ] || mkdir -p $work_dir

echo "convert_fst_to_json.sh: convert FST to json format"
fstprint $input_fst_prefix.fst > $work_dir/fst.txt

python3 -c '
from nnlp import Fst
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-fst", help="input text format FST file")
parser.add_argument("-ilabel", help="input symbol file")
parser.add_argument("-olabel", help="output symbol file")
parser.add_argument("-output_json", help="output symbol file")
cmd_args = parser.parse_args()

with open(cmd_args.ilabel, encoding="utf-8") as f_isym, \
     open(cmd_args.olabel, encoding="utf-8") as f_osym, \
     open(cmd_args.fst, encoding="utf-8") as f_fst, \
     open(cmd_args.output_json, "w", encoding="utf-8") as f_json:
    fst = Fst.from_text(f_isym, f_osym, f_fst)
    fst.to_json(f_json)
' \
    -ilabel $input_fst_prefix.isyms.txt \
    -olabel $input_fst_prefix.osyms.txt \
    -fst $work_dir/fst.txt \
    -output_json $output_json

rm $work_dir/fst.txt
echo 'convert_fst_to_json.sh: success!'
