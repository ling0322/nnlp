#include "wrapper.h"

#include <stdio.h>
#include "fst/arc.h"
#include "fst/fst.h"
#include "fst/vector-fst.h"
#include "fst/fst-decl.h"

void *nf_stdvectorfst_new() {
  return reinterpret_cast<void *>(new fst::StdVectorFst());
}

void nf_stdvectorfst_delete(void *fst) {
  if (fst) {
    delete reinterpret_cast<fst::StdVectorFst *>(fst);
  }
}

void nf_stdvectorfst_set_start(void *fst, int64_t state) {
  fst::StdVectorFst *fst_impl = reinterpret_cast<fst::StdVectorFst *>(fst);
  fst_impl->SetStart(state);
}

int64_t nf_stdvectorfst_add_state(void *fst) {
  fst::StdVectorFst *fst_impl = reinterpret_cast<fst::StdVectorFst *>(fst);
  return fst_impl->AddState();
}

void nf_stdvectorfst_add_arc(void *fst, int64_t state, FSTARC arc) {
  fst::StdVectorFst *fst_impl = reinterpret_cast<fst::StdVectorFst *>(fst);
  fst_impl->AddArc(
      state,
      fst::StdArc(arc.ilabel, arc.olabel, arc.weight, arc.tgt_state));
}

float nf_stdvectorfst_final(void *fst, int64_t state) {
  fst::StdVectorFst *fst_impl = reinterpret_cast<fst::StdVectorFst *>(fst);
  return fst_impl->Final(state).Value();
}

void nf_stdvectorfst_set_final(void *fst, int64_t state, float weight) {
  fst::StdVectorFst *fst_impl = reinterpret_cast<fst::StdVectorFst *>(fst);
  fst_impl->SetFinal(state, weight);
}

int64_t nf_stdvectorfst_num_states(void *fst) {
  fst::StdVectorFst *fst_impl = reinterpret_cast<fst::StdVectorFst *>(fst);
  return fst_impl->NumStates();
}

void *nf_arciterator_new(void *fst, int64_t state) {
  auto *fst_impl = reinterpret_cast<fst::StdVectorFst *>(fst);
  auto *arc_it = new fst::ArcIterator<fst::StdVectorFst>(*fst_impl, state);

  return arc_it;
}

void nf_arciterator_delete(void *it) {
  auto *arc_iter = reinterpret_cast<fst::ArcIterator<fst::StdVectorFst> *>(it);
  delete arc_iter;
}

int64_t nf_arciterator_done(void *it) {
  auto *arc_iter = reinterpret_cast<fst::ArcIterator<fst::StdVectorFst> *>(it);
  return arc_iter->Done();
}

void nf_arciterator_next(void *it) {
  auto *arc_iter = reinterpret_cast<fst::ArcIterator<fst::StdVectorFst> *>(it);
  return arc_iter->Next();
}

void nf_arciterator_value(void *it, FSTARC *arc) {
  auto *arc_iter = reinterpret_cast<fst::ArcIterator<fst::StdVectorFst> *>(it);
  const fst::StdArc &fst_arc = arc_iter->Value();
  arc->tgt_state = fst_arc.nextstate;
  arc->ilabel = fst_arc.ilabel;
  arc->olabel = fst_arc.olabel;
  arc->weight = fst_arc.weight.Value();
}
