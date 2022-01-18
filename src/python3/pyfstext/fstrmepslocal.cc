#include "remove-eps-local.h"
#include "fst/script/fst-class.h"

namespace nnlp {
namespace fstext {

using namespace fst;

fst::script::MutableFstClass *RemoveEpsLocal(fst::script::MutableFstClass *f) {
  try {
    MutableFst<StdArc> *internal_fst = f->GetMutableFst<StdArc>();
    RemoveEpsLocal(internal_fst);
    return f;
  } catch(const std::exception &e) {
    std::cerr << e.what();
    return nullptr;
  }
} 

}  // namespave fstext
}  // namespace nnlp
