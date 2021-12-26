#!/bin/bash

fst=$1
png=$2
isymbols=$3
osymbols=$4
if [[ -z $fst || -z $png ]]; then
  echo "draw FST to SVG file"
  echo "Usage: $0 <in-fst> <out-png> [<in-isymbol> <out-osymbol>]"
  exit 1
fi

symbol_cmd=''
if [[ ! -z $isymbols || ! -z $osymbols ]]; then
    symbol_cmd="--isymbols=$isymbols --osymbols=$osymbols"
fi
fstdraw $symbol_cmd $fst >  $fst.dot
dot -Tsvg -Gsize=80,105 -Grotate=0 $fst.dot > $png
