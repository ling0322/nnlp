#!/bin/bash

set -e

prefix=$1
isymbol=$2
osymbol=$3
weight=$4

if [ -z "$prefix" ] || [ -z "$isymbol" ] || [ -z "$osymbol" ] ; then
  echo "add selfloop to FST. "
  echo "Usage: add selfloop.sh <prefix> <isymbol> <osymbol> [weight]"
  echo "    prefix: prefix of output files, including <prefix>.{fst|isyms.txt|osyms.txt|info.txt}"
  echo "    isymbol: the input symbol for selfloop arc"
  echo "    osymbol: the output symbol for selfloop arc"
  echo "    weight (optional): the weight for selfloop arc"

  exit 1
fi

[ -z "$weight" ] && weight=0

echo "add selfloop ${isymbol}:${osymbol} w=${weight} to ${prefix}.fst"

python3 -m nnlp_tools addsymbol -syms_file $prefix.isyms.txt -symbol "$isymbol"
python3 -m nnlp_tools addsymbol -syms_file $prefix.osyms.txt -symbol "$osymbol"
mv $prefix.fst $prefix.original.fst
cat $prefix.original.fst | fstprint | python3 -m nnlp_tools addselfloop \
  -isyms_file $prefix.isyms.txt \
  -osyms_file $prefix.osyms.txt \
  -isymbol "$isymbol" \
  -osymbol "$osymbol" \
  -weight $weight | fstcompile > $prefix.fst
