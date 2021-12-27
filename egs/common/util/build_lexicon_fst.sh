#!/bin/bash

set -e

work_dir=$1
lexicon_file=$2
output_prefix=$3

rename_L () {
  rm $work_dir/L.fst
  mv $work_dir/L.out.fst $work_dir/L.fst
}

print_fstinfo () {
  fstinfo $work_dir/L.fst | egrep "(of states|of arcs|of final states|of .* epsilons)" | sed 's/  */ /g'
  echo
}

if [ -z "$work_dir" ] || [ -z "$lexicon_file" ] || [ -z "$output_prefix" ] ; then
  echo "Build FST from lexicon. "
  echo "Usage: build_lexicon_fst.sh <work-dir> <input-lexicon> <output-prefix>"
  echo "    work-dir: the directory thst stores intermediate files"
  echo "    input-lexicon: input lexicon"
  echo "    output-prefix: prefix of output files, including <prefix>.fst, <prefix>.isyms.txt, <prefix>.osyms.txt"

  exit 1
fi

[ -d $work_dir ] || mkdir -p $work_dir

echo "build_lexicon_fst.sh: build lexicon FST"
python3 -m nnlp_tools build_lexicon_fst \
    -input $lexicon_file \
    -ilabel $work_dir/isyms.txt \
    -olabel $work_dir/osyms.txt \
    -fst $work_dir/L.txt \
    -output_disambig $work_dir/L.disambig.txt \
    -unknown_symbol output


echo "build_lexicon_fst.sh: convert and optimize the lexicon FST"
echo "min - FST minimize"
echo "det - FST determinize"
echo "rmd - FST remove diambig symbols"
echo "rms - FST remove epsilon symbols"
echo ""

echo "L"
fstcompile $work_dir/L.txt $work_dir/L.fst && rm $work_dir/L.txt
print_fstinfo $work_dir/L.fst

echo "det(L)"
fstdeterminize $work_dir/L.fst $work_dir/L.out.fst
rename_L
print_fstinfo $work_dir/L.fst

echo "min(det(L))"
fstminimize $work_dir/L.fst $work_dir/L.out.fst
rename_L
print_fstinfo $work_dir/L.fst

echo "rmd(min(det(L)))"
fstprint $work_dir/L.fst > $work_dir/L.txt
python3 -m nnlp_tools rm_disambig \
    -input_fst $work_dir/L.txt \
    -output $work_dir/L.rmd.txt && rm $work_dir/L.txt
fstcompile $work_dir/L.rmd.txt $work_dir/L.out.fst
rename_L
print_fstinfo $work_dir/L.fst

echo "rms(rmd(min(det(L))))"
fstrmepslocal $work_dir/L.fst $work_dir/L.out.fst
rename_L
print_fstinfo $work_dir/L.fst

echo "build_lexicon_fst.sh: remove diambig symbols in isyms.txt"
python3 -m nnlp_tools rm_disambig -input_syms $work_dir/isyms.txt -output $work_dir/isyms.rmd.txt

echo "build_lexicon_fst.sh: copy output files"
cp $work_dir/isyms.rmd.txt $output_prefix.isyms.txt
cp $work_dir/osyms.txt $output_prefix.osyms.txt
cp $work_dir/L.fst $output_prefix.fst

echo "build_lexicon_fst.sh: success!"
