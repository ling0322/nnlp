#!/bin/bash

set -e

if [ ! -d openfst ]; then
  [ -f openfst-1.8.2.tar.gz ] || wget https://www.openfst.org/twiki/pub/FST/FstDownload/openfst-1.8.2.tar.gz
  tar xzf openfst-1.8.2.tar.gz 
  rm openfst-1.8.2.tar.gz 
  mv openfst-1.8.2 openfst  
fi

cd openfst
./configure CXXFLAGS="-D_USE_MATH_DEFINES -DFST_NO_DYNAMIC_LINKING -O2 -fPIC" --disable-shared --enable-bin=no --prefix $PWD
make clean
make -j 
make install
 
