package nmutfst

import (
	"unsafe"

	"github.com/ling0322/nnlp/src/go/openfst"
)

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
		openfst.ArcIterator_Destroy(a.internalPtr)
		a.internalPtr = nil
	}
}

// Done returns true if iteration is done
func (a *arcIteratorImpl) Done() bool {
	return openfst.ArcIterator_Done(a.internalPtr)
}

// Next moves to next arc
func (a *arcIteratorImpl) Next() {
	openfst.ArcIterator_Next(a.internalPtr)
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
	stdArc := openfst.ArcIterator_Value(a.internalPtr)

	iSym, err := a.fst.iSymbolTable.Symbol(stdArc.InputLabel)
	if err != nil {
		return
	}
	oSym, err := a.fst.oSymbolTable.Symbol(stdArc.OutputLabel)
	if err != nil {
		return
	}

	arc = Arc{
		NextState:    stdArc.TargetState,
		InputSymbol:  iSym,
		OutputSymbol: oSym,
		Weight:       stdArc.Weight,
	}

	return
}
