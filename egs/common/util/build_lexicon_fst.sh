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

  # exit when FST is empty
  num_arcs=$(fstinfo $work_dir/L.fst | grep "# of arcs" | sed 's/# of arcs *//g')
  [[ $num_arcs -le 0 ]] && exit 1

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
echo "rds - FST remove diambig symbols"
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
fstprint $work_dir/L.fst |\
  python3 -m nnlp_tools rm_disambig fst -syms $work_dir/isyms.txt |\
  fstcompile > $work_dir/L.out.fst
rename_L
print_fstinfo $work_dir/L.fst

echo "rms(rds(min(det(L))))"
fstrmepslocal $work_dir/L.fst $work_dir/L.out.fst
rename_L
print_fstinfo $work_dir/L.fst

echo "build_lexicon_fst.sh: remove diambig symbols in isyms.txt"
cat $work_dir/isyms.txt |\
  python3 -m nnlp_tools rm_disambig sym > $work_dir/isyms.rmd.txt

echo "build_lexicon_fst.sh: copy output files"
cp $work_dir/isyms.rmd.txt $output_prefix.isyms.txt
cp $work_dir/osyms.txt $output_prefix.osyms.txt
cp $work_dir/L.fst $output_prefix.fst

echo "build_lexicon_fst.sh: success!"
