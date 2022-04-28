package nfst

import (
	"fmt"
)

const (
	EpsilonSymbol = 0
	AlphaSymbol   = 1
	MagicNumber   = 0x55aa
	HeaderText    = "[nfst]  "
)

type State struct {
	Base        int32
	EpsilonBase int32
	RangeBase   int32
	Final       float32
}

type Arc struct {
	TargetState  int32
	OutputSymbol int32
	Weight       float32
	Check        int32
}

type RangeArc struct {
	Begin        rune
	End          rune
	TargetState  int32
	OutputSymbol int32
	Weight       float32
	Check        int32
}

// Fst implementation in nnlp
type Fst struct {
	States        []State
	Arcs          []Arc
	EpsilonArcs   []Arc
	RangeArcs     []RangeArc
	OutputSymbols []string
	InputSymbols  map[string]int
	Header        *Header
}

// Header for n-fst
type Header struct {
	Name             [8]byte
	Version          int32
	NumStates        int32
	NumArcs          int32
	NumEpsilonArcs   int32
	NumRangeArcs     int32
	NumOutputSymbols int32
	NumInputSymbols  int32
}

// DebugPrint prints the n-fst to stdout
func (f *Fst) DebugPrint() {
	fmt.Println("-------------------- N-Fst ----------------------")
	fmt.Printf("nStates = %d\n", len(f.States))
	fmt.Printf("nArcs = %d\n", len(f.Arcs))
	fmt.Printf("nEpsilonArcs = %d\n", len(f.EpsilonArcs))
	fmt.Println("------------------- States ----------------------")
	fmt.Println("StateID   Base      EpsBase   RngBase   FinalW   ")
	fmt.Println("-------------------------------------------------")
	for id, s := range f.States {
		fmt.Printf(
			"%-10d%-10d%-10d%-10d%-10f\n",
			id, s.Base, s.EpsilonBase, s.RangeBase, s.Final)
	}
	fmt.Println("")
	fmt.Println("---------------- InputSymbols -------------------")
	fmt.Println("SymbolID  Symbol                                 ")
	fmt.Println("-------------------------------------------------")
	for sym, id := range f.InputSymbols {
		fmt.Printf("%-10d%s\n", id, sym)
	}
	fmt.Println("")
	fmt.Println("-------------------- Arcs -----------------------")
	fmt.Println("Index     TgtState  Check     OutputSymbol       ")
	fmt.Println("-------------------------------------------------")
	for id, arc := range f.Arcs {
		fmt.Printf(
			"%-10d%-10d%-10d%s\n",
			id, arc.TargetState, arc.Check, f.OutputSymbols[arc.OutputSymbol])
	}
	fmt.Println("")
	fmt.Println("------------------ EpsilonArcs ------------------")
	fmt.Println("Index     TgtState  Check     OutputSymbol       ")
	fmt.Println("-------------------------------------------------")
	for id, arc := range f.EpsilonArcs {
		fmt.Printf(
			"%-10d%-10d%-10d%s\n",
			id, arc.TargetState, arc.Check, f.OutputSymbols[arc.OutputSymbol])
	}
	fmt.Println("")
	fmt.Println("------------------- RangeArcs -------------------")
	fmt.Println("Index   Range  TgtState  Check     OutputSymbol  ")
	fmt.Println("-------------------------------------------------")
	for id, arc := range f.RangeArcs {
		fmt.Printf(
			"%-8d%c-%c    %-10d%-10d%s\n", id, arc.Begin, arc.End,
			arc.TargetState, arc.Check, f.OutputSymbols[arc.OutputSymbol])
	}
	fmt.Println("")
}

func (a *Arc) Empty() bool {
	return a.Check == -1
}
