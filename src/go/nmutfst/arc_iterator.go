package nmutfst

// #cgo LDFLAGS: -L ../../../openfst/lib -lfst
// #cgo CXXFLAGS: -std=c++17 -I ../../../openfst/include
/*
#include "openfst_cwrapper.h"
*/
import "C"
import "unsafe"

// ArcIterator is the interface for iteration of arcs in FST
type ArcIterator interface {
	// Done returns true if iteration is done
	Done() bool

	// Get current arc
	Value() (Arc, error)
	MustValue() Arc

	// Move to next arc
	Next()
}

type arcIteratorImpl struct {
	internalPtr unsafe.Pointer

	// the fst to iterate
	fst *MutableFst
}

// NewArcIterator creates an arc iterator of specific state from FST
func (a *arcIteratorImpl) dispose() {
	if a.internalPtr != nil {
		C._c_arc_iterator_delete(a.internalPtr)
		a.internalPtr = nil
	}
}

// Done returns true if iteration is done
func (a *arcIteratorImpl) Done() bool {
	return C._c_arc_iterator_done(a.internalPtr) != 0
}

// Next moves to next arc
func (a *arcIteratorImpl) Next() {
	C._c_arc_iterator_next(a.internalPtr)
}

// Value returns current arc, panic on failed
func (a *arcIteratorImpl) MustValue() (arc Arc) {
	var err error
	if arc, err = a.Value(); err != nil {
		panic(err)
	}

	return
}

// Value returns current arc
func (a *arcIteratorImpl) Value() (arc Arc, err error) {
	carc := C.struct_NFSTARC{}
	C._c_arc_iterator_value(a.internalPtr, &carc)

	iSym, err := a.fst.iSymbolTable.Symbol(int(carc.ilabel))
	if err != nil {
		return
	}
	oSym, err := a.fst.oSymbolTable.Symbol(int(carc.olabel))
	if err != nil {
		return
	}

	arc = Arc{
		NextState:    int(carc.tgt_state),
		InputSymbol:  iSym,
		OutputSymbol: oSym,
		Weight:       float32(carc.weight),
	}

	return
}
