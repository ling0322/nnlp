package nmutfst

import (
	"fmt"
	"math"
	"runtime"
	"strings"
	"unsafe"
)

// #cgo LDFLAGS: -L ../../../openfst/lib -lfst
// #cgo CXXFLAGS: -std=c++17 -I ../../../openfst/include
/*
#include "openfst_cwrapper.h"
*/
import "C"

type MutableFst struct {
	internalPtr  unsafe.Pointer
	iSymbolTable SymbolTable
	oSymbolTable SymbolTable
}

func NewMutableFst() *MutableFst {
	mutableFst := &MutableFst{
		internalPtr:  C._c_mutable_fst_new(),
		iSymbolTable: NewSymbolTable(),
		oSymbolTable: NewSymbolTable(),
	}
	runtime.SetFinalizer(mutableFst, func(f *MutableFst) {
		f.dispose()
	})

	// set the start state
	stateZero := mutableFst.AddState()
	if stateZero != 0 {
		panic("invalid start state")
	}
	C._c_mutable_fst_set_start(mutableFst.internalPtr, 0)

	return mutableFst
}

// Dispose releases all resource of MutableFst
func (f *MutableFst) dispose() {
	if f.internalPtr != nil {
		C._c_mutable_fst_delete(f.internalPtr)
		f.internalPtr = nil
	}
}

// AddState adds a state in FST and returns the state-id
func (f *MutableFst) AddState() int {
	state := C._c_mutable_fst_add_state(f.internalPtr)
	return int(state)
}

// AddArc adds an arc to FST
func (f *MutableFst) AddArc(state int, arc Arc) {
	iSymId := f.iSymbolTable.InsertOrFind(arc.InputSymbol)
	oSymId := f.oSymbolTable.InsertOrFind(arc.OutputSymbol)

	cArc := C.struct_NFSTARC{
		tgt_state: C.int64_t(arc.NextState),
		ilabel:    C.int64_t(iSymId),
		olabel:    C.int64_t(oSymId),
		weight:    C.float(arc.Weight),
	}

	C._c_mutable_fst_add_arc(f.internalPtr, C.int64_t(state), cArc)
}

// Arcs returns an arcIterator of all arcs from the state
func (f *MutableFst) Arcs(state int) ArcIterator {
	arcIter := &arcIteratorImpl{
		internalPtr: C._c_arc_iterator_new(f.internalPtr, C.int64_t(state)),
		fst:         f,
	}
	runtime.SetFinalizer(arcIter, func(a *arcIteratorImpl) {
		a.dispose()
	})

	return arcIter
}

// Final returns the weight for final state. If state is not a final state,
// return NAN
func (f *MutableFst) Final(state int) float32 {
	return float32(C._c_mutable_fst_final(f.internalPtr, C.int64_t(state)))
}

// SetFinal set weight for final state
func (f *MutableFst) SetFinal(state int, weight float32) {
	C._c_mutable_fst_set_final(f.internalPtr, C.int64_t(state), C.float(weight))
}

// NumStates gets number of states in FST
func (f *MutableFst) NumStates() int {
	return int(C._c_mutable_fst_num_states(f.internalPtr))
}

// NumStates gets number of states in FST
func (f *MutableFst) NumInputSymbols() int {
	return f.iSymbolTable.NumSymbols()
}

// NumStates gets number of states in FST
func (f *MutableFst) NumOutputSymbols() int {
	return f.oSymbolTable.NumSymbols()
}

// MustRmDisambig is the Must version of RmDisambig
func (f *MutableFst) MustRmDisambig() *MutableFst {
	fst, err := f.RmDisambig()
	if err != nil {
		panic(err)
	}

	return fst
}

// RmDisambig crates a new mutable FST the same as current one. Except that
// all input disambig symbols are replaced by <eps>
func (f *MutableFst) RmDisambig() (*MutableFst, error) {
	rdsFst := NewMutableFst()

	// states
	// s = 0 is the start state which is already added into FST
	for {
		s := rdsFst.AddState()
		final := f.Final(s)
		if !math.IsInf(float64(final), 1) {
			rdsFst.SetFinal(s, final)
		}
		if s >= f.NumStates()-1 {
			break
		}
	}

	// arcs
	for state := 0; state < f.NumStates(); state++ {
		for arcIter := f.Arcs(state); !arcIter.Done(); arcIter.Next() {
			arc, err := arcIter.Value()
			if err != nil {
				return nil, fmt.Errorf("<!invalid FST: %v>", err)
			}

			if arc.InputSymbol.IsDisambig() {
				arc.InputSymbol = EpsilonSym
			}

			rdsFst.AddArc(state, arc)
		}
	}

	return rdsFst, nil
}

func (f *MutableFst) String() string {
	lines := []string{}
	for state := 0; state < f.NumStates(); state++ {
		for arcIter := f.Arcs(state); !arcIter.Done(); arcIter.Next() {
			arc, err := arcIter.Value()
			if err != nil {
				return fmt.Sprintf("<!invalid FST: %v>", err)
			}

			line := fmt.Sprintf(
				"%d %d %s %s",
				state,
				arc.NextState,
				arc.InputSymbol.Escape(),
				arc.OutputSymbol.Escape())
			if arc.Weight != 0 {
				line += fmt.Sprintf(" %g", arc.Weight)
			}
			lines = append(lines, line)
		}

		if !math.IsInf(float64(f.Final(state)), 0) {
			lines = append(lines, fmt.Sprintf("%d %g", state, float64(f.Final(state))))
		}
	}

	return strings.Join(lines, "\n") + "\n"
}
