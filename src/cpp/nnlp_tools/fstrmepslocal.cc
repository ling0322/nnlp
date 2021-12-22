// fstbin/fstrmepslocal.cc

// Copyright 2009-2011  Microsoft Corporation

// See ../../COPYING for clarification regarding multiple authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//  http://www.apache.org/licenses/LICENSE-2.0
//
// THIS CODE IS PROVIDED *AS IS* BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION ANY IMPLIED
// WARRANTIES OR CONDITIONS OF TITLE, FITNESS FOR A PARTICULAR PURPOSE,
// MERCHANTABLITY OR NON-INFRINGEMENT.
// See the Apache 2 License for the specific language governing permissions and
// limitations under the License.


#include "remove-eps-local.h"


/*
 A test example:
 ( echo "0 1 1 0"; echo "1 2 0 2"; echo "2 0"; ) | fstcompile | fstrmepslocal | fstprint
# prints:
# 0     1    1    2
# 1
 ( echo "0 1 0 0"; echo "0 0"; echo "1 0" ) | fstcompile | fstrmepslocal | fstprint
# 0
  ( echo "0 1 0 0"; echo "0 0"; echo "1 0" ) | fstcompile | fstrmepslocal | fstprint
  ( echo "0 1 0 0"; echo "0 0"; echo "1 0" ) | fstcompile | fstrmepslocal --use-log=true | fstprint
#  0    -0.693147182
*/

int main(int argc, char *argv[]) {
  try {
    using namespace fst;

    const char *usage =
        "Removes some (but not all) epsilons in an algorithm that will always reduce the number of\n"
        "arcs+states.  Option to preserves equivalence in tropical or log semiring, and\n"
        "if in tropical, stochasticit in either log or tropical.\n"
        "\n"
        "Usage:  fstrmepslocal  in.fst out.fst\n";

    if (argc != 3) {
      puts(usage);
      exit(1);
    }

    std::string fst_in_filename = argv[1],
        fst_out_filename = argv[2];

    VectorFst<StdArc> *fst = VectorFst<StdArc>::Read(fst_in_filename);
    RemoveEpsLocal(fst);
    fst->Write(fst_out_filename);

    delete fst;
    return 0;
  } catch(const std::exception &e) {
    std::cerr << e.what();
    return -1;
  }
}
