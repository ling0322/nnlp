package openfst

// #cgo CXXFLAGS: -std=c++17 -DFST_NO_DYNAMIC_LINKING
/*
#include "wrapper.h"
*/
import "C"
import "unsafe"

// Arc type in openfst
type StdArc struct {
	TargetState, InputLabel, OutputLabel int
	Weight                               float32
}

// StdVectorFst_Create creates a new instance of StdVectorFst
func StdVectorFst_Create() unsafe.Pointer {
	return C.nf_stdvectorfst_new()
}

// DeleteStdVStdVectorFst_DestroyectorFst deletes an instance of StdVectorFst
func StdVectorFst_Destroy(fst unsafe.Pointer) {
	C.nf_stdvectorfst_delete(fst)
}

// StdVectorFst_SetStart sets the start state of an StdVectorFst
func StdVectorFst_SetStart(fst unsafe.Pointer, state int) {
	C.nf_stdvectorfst_set_start(fst, C.int64_t(state))
}

// StdVectorFst_AddState adds a new state into StdVectorFst
func StdVectorFst_AddState(fst unsafe.Pointer) int {
	return int(C.nf_stdvectorfst_add_state(fst))
}

// StdVectorFst_AddArc adds an arc starting from specific state to StdVectorFst
func StdVectorFst_AddArc(fst unsafe.Pointer, state int, arc StdArc) {
	stdArc := C.struct_FSTARC{}
	stdArc.tgt_state = C.int64_t(arc.TargetState)
	stdArc.ilabel = C.int64_t(arc.InputLabel)
	stdArc.olabel = C.int64_t(arc.OutputLabel)
	stdArc.weight = C.float(arc.Weight)
	C.nf_stdvectorfst_add_arc(fst, C.int64_t(state), stdArc)
}

// StdVectorFst_Final returns final weight of a state. +INF is it's not a final
// state
func StdVectorFst_Final(fst unsafe.Pointer, state int) float32 {
	return float32(C.nf_stdvectorfst_final(fst, C.int64_t(state)))
}

// StdVectorFst_SetFinal sets final weight of a state
func StdVectorFst_SetFinal(fst unsafe.Pointer, state int, weight float32) {
	C.nf_stdvectorfst_set_final(fst, C.int64_t(state), C.float(weight))
}

// StdVectorFst_NumStates returns number of states in StdVectorFst
func StdVectorFst_NumStates(fst unsafe.Pointer) int {
	return int(C.nf_stdvectorfst_num_states(fst))
}

// ArcIterator_Create creates an arc iterator from specific state in
// StdVectorFst
func ArcIterator_Create(fst unsafe.Pointer, state int) unsafe.Pointer {
	return C.nf_arciterator_new(fst, C.int64_t(state))
}

// ArcIterator_Destroy deletes an arc iterator
func ArcIterator_Destroy(arcIter unsafe.Pointer) {
	C.nf_arciterator_delete(arcIter)
}

// ArcIterator_Done returns true if the iteration is done
func ArcIterator_Done(arcIter unsafe.Pointer) bool {
	return C.nf_arciterator_done(arcIter) != 0
}

// ArcIterator_Next moves iterator forward to the next arc
func ArcIterator_Next(arcIter unsafe.Pointer) {
	C.nf_arciterator_next(arcIter)
}

// ArcIterator_Next moves iterator forward to the next arc
func ArcIterator_Value(arcIter unsafe.Pointer) StdArc {
	arc := C.struct_FSTARC{}
	C.nf_arciterator_value(arcIter, &arc)

	stdArc := StdArc{}
	stdArc.InputLabel = int(arc.ilabel)
	stdArc.OutputLabel = int(arc.olabel)
	stdArc.TargetState = int(arc.tgt_state)
	stdArc.Weight = float32(arc.weight)
	return stdArc
}
