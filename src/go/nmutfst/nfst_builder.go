// build n-fst format binary FST file from mutable FST
package nmutfst

import (
	"fmt"
	"math"
	"math/bits"

	"github.com/ling0322/nnlp/src/go/errors"
	"github.com/ling0322/nnlp/src/go/nfst"
)

// TODO: int32 overflow check

// blockInfo represents the information of a area of consecutive arcs in the
// slice
type blockInfo struct {
	id       int
	freeArcs int
}

// Compress the FST into linear array format, input symbol look-up could have
// O(1) time complexity
// it's very similiar to the method in "Table-Compression Methods" section of
// Aho, A. V., Sethi, R., Ullman, J. D. Compilers : Principles, Techniques,
// and Tools. Addison-Wesley. 1985.
type nfstBuilder struct {
	nfst.Fst
	freeBlocks        []*blockInfo
	inputSymbolTable  SymbolTable
	outputSymbolTable SymbolTable
	blockSize         int
}

func newFstBuilder() *nfstBuilder {
	builder := &nfstBuilder{
		Fst: nfst.Fst{
			States:        []nfst.State{},
			Arcs:          []nfst.Arc{},
			EpsilonArcs:   []nfst.Arc{},
			RangeArcs:     []nfst.RangeArc{},
			InputSymbols:  map[string]int{},
			OutputSymbols: []string{},
		},
		freeBlocks:        []*blockInfo{},
		inputSymbolTable:  NewSymbolTable(),
		outputSymbolTable: NewSymbolTable(),
		blockSize:         -1,
	}

	return builder
}

// initialize the Array FST
func (f *nfstBuilder) initializeStates(numStates int) {
	f.States = make([]nfst.State, numStates)
	for i := range f.States {
		f.States[i].Base = -1
		f.States[i].EpsilonBase = -1
		f.States[i].RangeBase = -1
		f.States[i].Final = float32(math.Inf(1))
	}
}

// addBlock adds a new block into nFstBuilder, returns the index of created
// block
func (b *nfstBuilder) addBlock() int {
	block := make([]nfst.Arc, b.blockSize)
	for i := range block {
		block[i].Check = -1
		block[i].TargetState = -1
	}

	numBlocks := len(b.Arcs) / b.blockSize

	b.Arcs = append(b.Arcs, block...)
	b.freeBlocks = append(b.freeBlocks, &blockInfo{
		id:       numBlocks,
		freeArcs: b.blockSize,
	})

	return numBlocks
}

// findBase finds a base in arcs to put all isyms
func (b *nfstBuilder) findBase(iSyms []int) int {
	if len(iSyms) == 0 {
		panic("findBase: iSyms is empty")
	}

	for _, block := range b.freeBlocks {
		if block.freeArcs >= len(iSyms) {
			// This node has adequate free slots for isymbols. Then check
			// whether all nodes could be placed well
			base := b.findBaseInBlock(block, iSyms)
			if base >= 0 {
				return base
			}
		}
	}

	// No block is suitable for iSyms, needs to create a new block.
	// Since the new added block is an empty block, we can use the first slot
	// in this block directly
	blockID := b.addBlock()
	return blockID * b.blockSize
}

// findBaseInBlock finds if any base in block could store iSyms. On success,
// returns the index. On failed, return -1
func (b *nfstBuilder) findBaseInBlock(block *blockInfo, iSyms []int) int {
	beginState := block.id * b.blockSize
	endState := (block.id + 1) * b.blockSize
	for base := beginState; base < endState; base++ {
		success := true
		for _, iSym := range iSyms {
			s := base ^ int(iSym)
			if !b.Arcs[s].Empty() {
				// If arcs[s] already have value
				success = false
				break
			}
		}
		if success {
			return base
		}
	}

	return -1
}

// getInputSymsFromState gets list of input symbols from a state in FST
func (b *nfstBuilder) getInputSymsFromState(fst *MutableFst, state int) []int {
	iSyms := []int{}
	for arcIter := fst.Arcs(state); !arcIter.Done(); arcIter.Next() {
		arc := arcIter.MustValue()

		// ignore epsilon arcs
		if arc.InputSymbol == EpsilonSym {
			continue
		}

		iSym := b.inputSymbolTable.MustFind(arc.InputSymbol)
		iSyms = append(iSyms, iSym)
	}

	return iSyms
}

// putStateToBase puts all outgoing arcs from state to the base index at
// b.arcs
func (b *nfstBuilder) addArcsOfStateToBase(fst *MutableFst, state, base int) {
	for arcIter := fst.Arcs(state); !arcIter.Done(); arcIter.Next() {
		// already checked in checkGetArc
		arc := arcIter.MustValue()

		// ignore epsilon arcs
		if arc.InputSymbol == EpsilonSym {
			continue
		}

		iSym := b.inputSymbolTable.MustFind(arc.InputSymbol)
		arcIdx := base ^ iSym
		if !b.Arcs[arcIdx].Empty() {
			panic("putStateToBase: invalid base")
		}

		// get output symbol id
		oSym := b.outputSymbolTable.MustFind(arc.OutputSymbol)

		b.Arcs[arcIdx].Check = int32(state)
		b.Arcs[arcIdx].OutputSymbol = int32(oSym)
		b.Arcs[arcIdx].TargetState = int32(arc.NextState)
		b.Arcs[arcIdx].Weight = arc.Weight
	}
}

// updateBlock updates block information after added arcs into it
func (b *nfstBuilder) updateBlock(base, numArcs int) {
	blockID := base / b.blockSize
	blockIdx := -1
	for i, block := range b.freeBlocks {
		if block.id == blockID {
			blockIdx = i
			break
		}
	}
	if blockIdx == -1 {
		panic("updateBlock: block not exist")
	}

	block := b.freeBlocks[blockIdx]
	block.freeArcs -= numArcs
	if block.freeArcs < 0 {
		panic("updateBlock: invalid block.freeArcs")
	}
	if block.freeArcs == 0 {
		// remove this block from freeBlocks
		b.freeBlocks = append(b.freeBlocks[:blockIdx], b.freeBlocks[blockIdx+1:]...)
	}
}

// addState add all outgoing arcs from state to FST
func (b *nfstBuilder) addArcsOfState(fst *MutableFst, state int) {
	// Add a new block when didn't have free blocks
	if len(b.freeBlocks) == 0 {
		b.addBlock()
	}

	// arcs -> iSyms
	iSyms := b.getInputSymsFromState(fst, state)
	if len(iSyms) == 0 {
		// no non-epsilon arcs in this state
		return
	}

	base := b.findBase(iSyms)
	b.addArcsOfStateToBase(fst, state, base)
	b.updateBlock(base, len(iSyms))

	b.States[state].Base = int32(base)
}

// initializeSymbolTable initializes the symbols tables used in builder
func (b *nfstBuilder) initializeSymbolTable(fst *MutableFst) {
	for state := 0; state < fst.NumStates(); state++ {
		var arc Arc
		for arcIter := fst.Arcs(state); !arcIter.Done(); arcIter.Next() {
			arc = arcIter.MustValue()
			b.inputSymbolTable.InsertOrFind(arc.InputSymbol)
			b.outputSymbolTable.InsertOrFind(arc.OutputSymbol)
		}
	}
}

// checkSymbol checks if a symbol is valid
func (b *nfstBuilder) checkSymbol(symbol Symbol) (err error) {
	var s string

	if symbol == EpsilonSym || symbol.IsRange() || symbol.IsReserved() {
		// ignore <eps> and reserved symbols
		return
	}
	if s, err = symbol.Value(); err != nil {
		// besides <eps> and reserved symbols, special symbols are not allowed
		// in the fst
		return
	}
	if len(s) > 255 {
		err = fmt.Errorf("input symbol too long: %s", symbol)
		return
	}

	return
}

// checkArc check if an arc is valid
func (b *nfstBuilder) checkArc(arc Arc, err error) error {
	if err != nil {
		return err
	}
	if err = b.checkSymbol(arc.InputSymbol); err != nil {
		return err
	}
	if err = b.checkSymbol(arc.OutputSymbol); err != nil {
		return err
	}

	return nil
}

// checkFst checks if the fst in valid for n-fst conversion/\
// requirements
//   1) both in-/out-symbols should not be special symbols
//   2) each input and output symbol, its utf-8 bytes should < 255
//   3) one non-epsilon input symbol from a state should have only one out-going
//      arc corresponded to it
// if checkSymArc is false, ignore checking of 3)
func (b *nfstBuilder) checkFst(fst *MutableFst, checkSymArc bool) error {
	if b.blockSize > 65536 {
		return errors.Unexpected("too many input symbols in FST (less than 65536 expected)")
	}

	for state := 0; state < fst.NumStates(); state++ {
		symbolSet := map[string]bool{}
		for arcIter := fst.Arcs(state); !arcIter.Done(); arcIter.Next() {
			arc, err := arcIter.Value()
			if err = b.checkArc(arc, err); err != nil {
				return err
			}

			// ignore on <eps>, range symbol or checkSymArc == false
			iSym := arc.InputSymbol
			if iSym == EpsilonSym || iSym.IsRange() || !checkSymArc {
				continue
			}

			iSymVal := arc.InputSymbol.MustValue()
			if _, ok := symbolSet[iSymVal]; ok {
				return errors.Unexpected(fmt.Sprintf(
					"multiple arcs with same isymbol in state %d",
					state,
				))
			}
			symbolSet[iSymVal] = true
		}
	}

	return nil
}

// addArcs adds all non-epsilon arcs from FST to the arcs array
func (b *nfstBuilder) addArcs(fst *MutableFst) {
	for state := 0; state < fst.NumStates(); state++ {
		b.addArcsOfState(fst, state)
	}
}

// addArcs adds all epsilon arcs from FST to the arcs array
func (b *nfstBuilder) addEpsilonArcs(fst *MutableFst) {
	for state := 0; state < fst.NumStates(); state++ {
		epsilonBase := len(b.EpsilonArcs)
		hasEpsArcs := false
		for arcIter := fst.Arcs(state); !arcIter.Done(); arcIter.Next() {
			// we ignore err handling here since it already checked by checkFst
			fstArc := arcIter.MustValue()

			if fstArc.InputSymbol != EpsilonSym {
				continue
			}
			hasEpsArcs = true

			arc := nfst.Arc{
				Check:        int32(state),
				OutputSymbol: int32(b.outputSymbolTable.MustFind(fstArc.OutputSymbol)),
				Weight:       fstArc.Weight,
				TargetState:  int32(fstArc.NextState),
			}
			b.EpsilonArcs = append(b.EpsilonArcs, arc)
		}

		// once state has epsilon arcs, it will set the epsilonBase, otherwise
		// leave epsilonBase = -1
		if hasEpsArcs {
			b.States[state].EpsilonBase = int32(epsilonBase)
		}
	}
}

// addRangeArcs adds all range arcs from FST to the rangeArcs array
func (b *nfstBuilder) addRangeArcs(fst *MutableFst) {
	for state := 0; state < fst.NumStates(); state++ {
		rangeBase := len(b.RangeArcs)
		hasRangeArcs := false
		for arcIter := fst.Arcs(state); !arcIter.Done(); arcIter.Next() {
			// we ignore err handling here since it already checked by checkFst
			fstArc := arcIter.MustValue()

			if !fstArc.InputSymbol.IsRange() {
				continue
			}
			hasRangeArcs = true
			begin, end := fstArc.InputSymbol.MustParseRange()

			arc := nfst.RangeArc{
				Begin:        begin,
				End:          end,
				Check:        int32(state),
				OutputSymbol: int32(b.outputSymbolTable.MustFind(fstArc.OutputSymbol)),
				Weight:       fstArc.Weight,
				TargetState:  int32(fstArc.NextState),
			}
			b.RangeArcs = append(b.RangeArcs, arc)
		}

		// once state has range arcs, it will set the epsilonBase, otherwise
		// leave epsilonBase = -1
		if hasRangeArcs {
			b.States[state].RangeBase = int32(rangeBase)
		}
	}
}

// computeBlockSize computes the block size according to the size of input
// symbol table
func (b *nfstBuilder) computeBlockSize(fst *MutableFst) {
	bitsRequired := bits.Len(uint(fst.NumInputSymbols())) + 1
	blockSize := 1 << bitsRequired
	if blockSize < 256 {
		// minimal is 256
		blockSize = 256
	}

	b.blockSize = blockSize
}

// buildSymbolList builds the i-/o-symbols from their symbol table
func (b *nfstBuilder) buildSymbolList() {
	// place osymbols
	symbols := b.outputSymbolTable.SymbolList()
	b.OutputSymbols = []string{}
	for id, sym := range symbols {
		var s string
		if id == EpsilonSymID {
			s = "<eps>"
		} else if sym.IsReserved() {
			s = sym.Escape()
		} else {
			s = sym.MustValue()
		}
		b.OutputSymbols = append(b.OutputSymbols, s)
	}

	// place isymbols
	symbols = b.inputSymbolTable.SymbolList()
	b.InputSymbols = map[string]int{}
	for id, sym := range symbols {
		var s string
		if id == EpsilonSymID {
			s = "<eps>"
		} else if sym.IsReserved() {
			s = sym.Escape()
		} else {
			s = sym.MustValue()
		}
		b.InputSymbols[s] = id
	}
}

// getInputSymArcsMap gets the map of inputSym:Arc from an arc iterator
func (b *nfstBuilder) getInputSymArcsMap(arcIter ArcIterator) map[Symbol][]Arc {
	m := map[Symbol][]Arc{}
	for ; !arcIter.Done(); arcIter.Next() {
		arc := arcIter.MustValue()
		if _, ok := m[arc.InputSymbol]; !ok {
			m[arc.InputSymbol] = []Arc{}
		}
		m[arc.InputSymbol] = append(m[arc.InputSymbol], arc)
	}

	return m
}

// normalizeFst normalizes the input fst to make sure it could be converted to
// n-fst format. n-fst requirements
//     one non-epsilon input symbol from a state should have only one out-going
//     arc corresponded to it
func (b *nfstBuilder) normalizeFst(fst *MutableFst) (outFst *MutableFst) {
	outFst = NewMutableFst()

	// states
	// s = 0 is the start state which is already added into FST
	for {
		s := outFst.AddState()
		final := fst.Final(s)
		if !math.IsInf(float64(final), 1) {
			outFst.SetFinal(s, final)
		}
		if s >= fst.NumStates()-1 {
			break
		}
	}

	// arcs
	for state := 0; state < fst.NumStates(); state++ {
		iSymArcs := b.getInputSymArcsMap(fst.Arcs(state))
		for inputSymbol, arcs := range iSymArcs {
			if inputSymbol == EpsilonSym {
				// <eps> symbol is allowed to have multiple out-going arcs
				for _, arc := range arcs {
					outFst.AddArc(state, arc)
				}
				continue
			} else if len(arcs) == 1 {
				// good, this symbol have only one arc
				outFst.AddArc(state, arcs[0])
				continue
			}

			// process arcs which have the same inputSymbol
			midState := outFst.AddState()
			outFst.AddArc(state, Arc{midState, inputSymbol, EpsilonSym, 0})
			for _, arc := range arcs {
				arc.InputSymbol = EpsilonSym
				outFst.AddArc(midState, arc)
			}
		}
	}

	// check the outFst again
	if err := b.checkFst(outFst, true); err != nil {
		panic(err)
	}

	return outFst
}

func (b *nfstBuilder) build(fst *MutableFst) error {
	if err := b.checkFst(fst, false); err != nil {
		return err
	}
	fst = b.normalizeFst(fst)

	b.computeBlockSize(fst)

	// initialize the symbol table
	b.initializeSymbolTable(fst)

	// initialize the nFstImpl
	b.initializeStates(fst.NumStates())

	// add non-epsilon arcs
	b.addArcs(fst)

	// add epsilon arcs
	b.addEpsilonArcs(fst)

	// add range arcs
	b.addRangeArcs(fst)

	// build the symbol list for n-fst
	b.buildSymbolList()

	// update final weights
	for s := 0; s < fst.NumStates(); s++ {
		b.States[s].Final = fst.Final(s)
	}

	b.DebugPrint()

	return nil
}

// ConvertFst converts mutable FST to n-fst
func ConvertFst(mutFst *MutableFst) (fst *nfst.Fst, err error) {
	builder := newFstBuilder()
	if err = builder.build(mutFst); err != nil {
		return
	}

	fst = &builder.Fst
	return
}
