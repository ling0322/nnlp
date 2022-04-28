package nmutfst

import (
	"fmt"

	"github.com/ling0322/nnlp/src/go/errors"
)

const (
	InputSymbolTable = iota
	OutputSymbolTable
)

type SymbolTable interface {
	// InsertOrFind find the key by symbol in the table, if symbol not exist
	// insert it then returns the id
	InsertOrFind(symbol Symbol) int

	// MustFind finds the key by symbol, panic if symbol not exist
	MustFind(symbol Symbol) int

	// Symbol get symbol by id
	Symbol(key int) (Symbol, error)

	// SymbolList returns the symbol list
	SymbolList() []Symbol

	// Count returns number of symbols in this table
	NumSymbols() int
}

type symbolTableImpl struct {
	symbolToKey map[Symbol]int
	keyToSymbol []Symbol
}

func NewSymbolTable() SymbolTable {
	var symbolIds map[Symbol]int
	var symbols []Symbol

	symbolIds = map[Symbol]int{
		EpsilonSym: EpsilonSymID,
		AlphaSym:   AlphaSymID,
		BetaSym:    BetaSymID,
		GammaSym:   GammaSymID,
		DeltaSym:   DeltaSymID,
		RhoSym:     RhoSymID,
		SigmaSym:   SigmaSymID,
		PhiSym:     PhiSymID,
	}
	symbols = []Symbol{
		EpsilonSym,
		AlphaSym,
		BetaSym,
		GammaSym,
		DeltaSym,
		RhoSym,
		SigmaSym,
		PhiSym,
	}

	return &symbolTableImpl{
		symbolToKey: symbolIds,
		keyToSymbol: symbols,
	}
}

// InsertOrFind implements interface SymbolTable
func (t *symbolTableImpl) InsertOrFind(symbol Symbol) (key int) {
	key, ok := t.symbolToKey[symbol]
	if ok {
		return
	}

	// if not exist
	key = len(t.keyToSymbol)
	t.symbolToKey[symbol] = key
	t.keyToSymbol = append(t.keyToSymbol, symbol)

	return
}

// Find finds the key by symbol, returns (key, success)
func (t *symbolTableImpl) Find(symbol Symbol) (int, bool) {
	key, ok := t.symbolToKey[symbol]
	return key, ok
}

// MustFind finds the key by symbol, panic if symbol not exist
func (t *symbolTableImpl) MustFind(symbol Symbol) int {
	key, ok := t.symbolToKey[symbol]
	if !ok {
		panic("symbol not exist")
	}

	return key
}

// Find symbol by key
func (t *symbolTableImpl) Symbol(id int) (Symbol, error) {
	if id < len(t.keyToSymbol) {
		return t.keyToSymbol[id], nil
	} else {
		return EpsilonSym, errors.KeyError(fmt.Sprintf("%d", id))
	}
}

// NumSymbols returns number of symbols in this table
func (t *symbolTableImpl) NumSymbols() int {
	return len(t.keyToSymbol)
}

// Find symbol by key
func (t *symbolTableImpl) SymbolList() []Symbol {
	return t.keyToSymbol
}
