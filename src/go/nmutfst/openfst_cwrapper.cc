#include "openfst_cwrapper.h"

#include <stdio.h>
#include <fst/arc.h>
#include <fst/fst.h>
#include <fst/vector-fst.h>
#include <fst/fst-decl.h>

void *_c_mutable_fst_new() {
  return reinterpret_cast<void *>(new fst::StdVectorFst());
}

void _c_mutable_fst_delete(void *fst) {
  if (fst) {
    delete reinterpret_cast<fst::StdVectorFst *>(fst);
  }
}

void _c_mutable_fst_set_start(void *fst_ptr, int64_t state) {
  fst::StdVectorFst *fst = reinterpret_cast<fst::StdVectorFst *>(fst_ptr);
  fst->SetStart(state);
}

int64_t _c_mutable_fst_add_state(void *fst_ptr) {
  fst::StdVectorFst *fst = reinterpret_cast<fst::StdVectorFst *>(fst_ptr);
  return fst->AddState();
}

void _c_mutable_fst_add_arc(void *fst_ptr, int64_t state, NFSTARC arc) {
  fst::StdVectorFst *fst = reinterpret_cast<fst::StdVectorFst *>(fst_ptr);
  fst->AddArc(
      state, 
      fst::StdArc(arc.ilabel, arc.olabel, arc.weight, arc.tgt_state));
}

float _c_mutable_fst_final(void *fst_ptr, int64_t state) {
  fst::StdVectorFst *fst = reinterpret_cast<fst::StdVectorFst *>(fst_ptr);
  return fst->Final(state).Value();
}

void _c_mutable_fst_set_final(void *fst_ptr, int64_t state, float weight) {
  fst::StdVectorFst *fst = reinterpret_cast<fst::StdVectorFst *>(fst_ptr);
  fst->SetFinal(state, weight);
}

int64_t _c_mutable_fst_num_states(void *fst_ptr) {
  fst::StdVectorFst *fst = reinterpret_cast<fst::StdVectorFst *>(fst_ptr);
  return fst->NumStates();
}

void *_c_arc_iterator_new(void *fst_ptr, int64_t state) {
  auto *fst = reinterpret_cast<fst::StdVectorFst *>(fst_ptr);
  auto *arc_it = new fst::ArcIterator<fst::StdVectorFst>(*fst, state);

  return arc_it;
}

void _c_arc_iterator_delete(void *arc_iter_ptr) {
  auto *arc_iter = reinterpret_cast<fst::ArcIterator<fst::StdVectorFst> *>(
      arc_iter_ptr);
  delete arc_iter;
}

int64_t _c_arc_iterator_done(void *arc_iter_ptr) {
  auto *arc_iter = reinterpret_cast<fst::ArcIterator<fst::StdVectorFst> *>(
      arc_iter_ptr);
  return arc_iter->Done();
}

void _c_arc_iterator_next(void *arc_iter_ptr) {
  auto *arc_iter = reinterpret_cast<fst::ArcIterator<fst::StdVectorFst> *>(
      arc_iter_ptr);
  return arc_iter->Next();
}

void _c_arc_iterator_value(void *arc_iter_ptr, NFSTARC *arc) {
  auto *arc_iter = reinterpret_cast<fst::ArcIterator<fst::StdVectorFst> *>(
      arc_iter_ptr);
  const fst::StdArc &fst_arc = arc_iter->Value();
  arc->tgt_state = fst_arc.nextstate;
  arc->ilabel = fst_arc.ilabel;
  arc->olabel = fst_arc.olabel;
  arc->weight = fst_arc.weight.Value();
}
