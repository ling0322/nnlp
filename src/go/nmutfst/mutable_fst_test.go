package nmutfst

import (
	"testing"
)

// TestBuildFst tests basic FST build function
func TestBuildFst(t *testing.T) {
	fst := NewMutableFst()
	s1 := fst.AddState()
	s2 := fst.AddState()

	fst.AddArc(0, Arc{s1, NewSymbol("#unk"), NewSymbol("#0"), 1})
	fst.AddArc(s1, Arc{s2, DisambigSymbol(1), EpsilonSym, 0})
	fst.SetFinal(s2, 0)

	if fst.String() != NormalizeFstText(`
		0 1 \#unk \#0 1
		1 2 #1 <eps>
		2 0
	`) {
		t.Fail()
	}
}
