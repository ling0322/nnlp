package nmutfst

import (
	"fmt"
	"math"
	"runtime"
	"strings"
	"unsafe"

	"github.com/ling0322/nnlp/src/go/openfst"
)

type MutableFst struct {
	internalPtr  unsafe.Pointer
	iSymbolTable SymbolTable
	oSymbolTable SymbolTable
}

func NewMutableFst() *MutableFst {
	mutableFst := &MutableFst{
		internalPtr:  openfst.StdVectorFst_Create(),
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
	openfst.StdVectorFst_SetStart(mutableFst.internalPtr, 0)

	return mutableFst
}

// Dispose releases all resource of MutableFst
func (f *MutableFst) dispose() {
	if f.internalPtr != nil {
		openfst.StdVectorFst_Destroy(f.internalPtr)
		f.internalPtr = nil
	}
}

// AddState adds a state in FST and returns the state-id
func (f *MutableFst) AddState() int {
	state := openfst.StdVectorFst_AddState(f.internalPtr)
	return int(state)
}

// AddArc adds an arc to FST
func (f *MutableFst) AddArc(state int, arc Arc) {
	ilabel := f.iSymbolTable.InsertOrFind(arc.InputSymbol)
	olabel := f.oSymbolTable.InsertOrFind(arc.OutputSymbol)

	openfst.StdVectorFst_AddArc(f.internalPtr, state, openfst.StdArc{
		TargetState: arc.NextState,
		InputLabel:  ilabel,
		OutputLabel: olabel,
		Weight:      arc.Weight,
	})

}

// Arcs returns an arcIterator of all arcs from the state
func (f *MutableFst) Arcs(state int) ArcIterator {
	arcIter := &arcIteratorImpl{
		internalPtr: openfst.ArcIterator_Create(f.internalPtr, state),
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
	return openfst.StdVectorFst_Final(f.internalPtr, state)
}

// SetFinal set weight for final state
func (f *MutableFst) SetFinal(state int, weight float32) {
	openfst.StdVectorFst_SetFinal(f.internalPtr, state, weight)
}

// NumStates gets number of states in FST
func (f *MutableFst) NumStates() int {
	return openfst.StdVectorFst_NumStates(f.internalPtr)
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
