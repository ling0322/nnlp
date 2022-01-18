#ifndef NNLP_FSTEXT_FSTRMEPSLOCAL_
#define NNLP_FSTEXT_FSTRMEPSLOCAL_

#include "fst/script/fst-class.h"

namespace nnlp {
namespace fstext {

using namespace fst;

// remove epsilon using kaldi::RemoveEpsLocal(MutableFst<Arc> *fst)
fst::script::MutableFstClass *RemoveEpsLocal(fst::script::MutableFstClass *f);

}  // namespave fstext
}  // namespace nnlp


#endif