package nregex

import (
	"github.com/ling0322/nnlp/src/go/nmutfst"
)

type MutFst = nmutfst.MutableFst

// error messages
const (
	errUnexpectedEOL    = "unexpected end of expression"
	errUnexpectedChar   = "unexpected token"
	errEmptyExpr        = "expression is empty"
	errInvalidClosere   = "invalid closure expression"
	errInternalErr      = "internal error"
	errInvalidState     = "invalid state"
	errRangeOutOfOrder  = "range out of order"
	errRefClassNotExist = "reference class <%s> not exist"
)

// listStringToSymbol converts list of strings to list of symbols
//lint:ignore U1000 For future use
func listStringToSymbol(inputs []string) []nmutfst.Symbol {
	if inputs == nil {
		return []nmutfst.Symbol{}
	}

	symbols := []nmutfst.Symbol{}
	for _, s := range inputs {
		symbols = append(symbols, nmutfst.NewSymbol(s))
	}

	return symbols
}

// alignSymbolList make two symbol the same size by appending <eps> at the end
// of short one
//lint:ignore U1000 For future use
func alignSymbolList(a, b []nmutfst.Symbol) (retA, retB []nmutfst.Symbol) {
	if len(a) > len(b) {
		n := len(a) - len(b)
		for i := 0; i < n; i++ {
			b = append(b, nmutfst.EpsilonSym)
		}
	} else if len(a) < len(b) {
		n := len(b) - len(a)
		for i := 0; i < n; i++ {
			a = append(a, nmutfst.EpsilonSym)
		}
	}

	if len(a) != len(b) {
		panic("len(a) != len(b)")
	}

	retA = a
	retB = b
	return
}

// addOutputArcs adds a sequence of output arcs in FST starting from
// specific state
//lint:ignore U1000 For future use
func addOutputArcs(
	fst *nmutfst.MutableFst, state int, outputs []string,
) (endState int) {
	if outputs == nil {
		return state
	}

	for _, output := range outputs {
		sym := nmutfst.NewSymbol(output)
		nextState := fst.AddState()
		fst.AddArc(state, nmutfst.Arc{
			NextState:    nextState,
			InputSymbol:  nmutfst.EpsilonSym,
			OutputSymbol: sym,
			Weight:       0,
		})
		state = nextState
	}

	endState = state
	return
}

// charset returns a set contains all chars in s
func charset(s string) map[rune]bool {
	set := map[rune]bool{}
	for _, ch := range s {
		set[ch] = true
	}

	return set
}

// buildLiteralFst builds the FST for literal input and output symbols, returns
// the endState
func buildLiteralFst(input, output rune, fst *MutFst, state int) int {
	iSymbol := nmutfst.NewSymbol(string(input))
	oSymbol := nmutfst.NewSymbol(string(output))

	nextState := fst.AddState()
	fst.AddArc(state, nmutfst.Arc{
		NextState:    nextState,
		InputSymbol:  iSymbol,
		OutputSymbol: oSymbol,
		Weight:       0,
	})

	return nextState
}
