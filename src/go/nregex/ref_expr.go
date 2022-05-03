package nregex

import (
	"fmt"

	"github.com/ling0322/nnlp/src/go/nmutfst"
)

// A reference expression
type RefExpr struct {
	Name string
}

// readRefToken reads a reference token <name> from cursor
func readRefToken(r *reader) (name string, err error) {
	err = readAndCheckString(r, "<", nil)
	name, err = readName(r, charset(">"), err)
	err = readAndCheckString(r, ">", err)

	return
}

// readRef reads a reference expression from cursor
func readRef(r *reader) (e *RefExpr, err error) {
	name, err := readRefToken(r)
	if err != nil {
		return
	}

	e = &RefExpr{
		Name: name,
	}
	return
}

// tagStartSymbol returns the start-tag symbol from name
func tagStartSymbol(name string) nmutfst.Symbol {
	if len(name) == 0 {
		panic(errUnexpectedArgName)
	}
	return nmutfst.NewSymbol(fmt.Sprintf("<%s>", name))
}

// tagEndSymbol returns the end-tag symbol from name
func tagEndSymbol(name string) nmutfst.Symbol {
	if len(name) == 0 {
		panic(errUnexpectedArgName)
	}
	return nmutfst.NewSymbol(fmt.Sprintf("</%s>", name))
}

// AddToFst adds the reference expression to FST
func (e *RefExpr) AddToFst(g *Grammar, fst *MutFst, state int) int {
	ast, ok := g.rules[e.Name]
	if !ok {
		// Check() ensures the e.Name always exists in rules
		panic(fmt.Sprintf(errRefClassNotExist, e.Name))
	}

	// we need to emit the tag symbols for capture items
	if g.captures[e.Name] {
		nextState := fst.AddState()
		fst.AddArc(state, nmutfst.Arc{
			NextState:    nextState,
			InputSymbol:  nmutfst.EpsilonSym,
			OutputSymbol: tagStartSymbol(e.Name),
		})
		state = nextState
	}

	state = ast.AddToFst(g, fst, state)

	// we need to emit the tag symbols for capture items
	if g.captures[e.Name] {
		nextState := fst.AddState()
		fst.AddArc(state, nmutfst.Arc{
			NextState:    nextState,
			InputSymbol:  nmutfst.EpsilonSym,
			OutputSymbol: tagEndSymbol(e.Name),
		})
		state = nextState
	}

	return state
}

func (e *RefExpr) Check(g *Grammar, refStack []string) (err error) {
	ast, ok := g.rules[e.Name]
	if !ok {
		err = GrammarError(fmt.Sprintf(errRefClassNotExist, e.Name), refStack)
		return
	}
	refStack = append(refStack, e.Name)
	if err = ast.Check(g, refStack); err != nil {
		return
	}

	return
}
