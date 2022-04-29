package nregex

import (
	"fmt"
	"unicode"

	"github.com/ling0322/nnlp/src/go/nfst"
	"github.com/ling0322/nnlp/src/go/nmutfst"
)

// grammar is a collection of n-regex rules with its class name
type Grammar struct {
	rules map[string]AST
}

func GrammarError(message string, refStack []string) error {
	return fmt.Errorf("GrammarError: %s at class <%s>", message, refStack[len(refStack)-1])
}

// readSpaces reads spaces from reader, return error if EOL reached
func readSpaces(r *reader, err error) error {
	if err != nil {
		return err
	}

	for (!r.EOL()) && unicode.IsSpace(r.Rune()) {
		r.NextRune()
	}
	if r.EOL() {
		return SyntaxError(errUnexpectedEOL, r)
	}

	return nil
}

// readStringN reads a string of n runes from reade
func readStringN(r *reader, n int) (s string, err error) {
	for i := 0; i < n; i++ {
		if r.EOL() {
			return "", SyntaxError(errUnexpectedEOL, r)
		}
		s += string(r.Rune())
		r.NextRune()
	}

	return s, nil
}

// readDefLeft reads left part of the define statement, including ::=
func (g *Grammar) readDefLeft(r *reader) (name string, err error) {
	name, err = readRefToken(r)
	err = readSpaces(r, err)
	if err != nil {
		return
	}

	beginOffset := r.Position()
	s, err := readStringN(r, 3)
	if err != nil {
		return
	}
	if s != "::=" {
		r.SetPosition(beginOffset)
		return "", SyntaxError(errUnexpectedChar, r)
	}

	return
}

// readDefRightInline reads right part of the inline define statement
func (g *Grammar) readDefRightInline(r *reader) (ast AST, err error) {
	if ast, err = readExpr(r, nil); err != nil {
		return
	}
	return
}

// readDefRightMultiLine reads right part of the multi-line define statement
func (g *Grammar) readDefRightMultiLine(r *reader) (expr AST, err error) {
	if r.EOL() {
		err = SyntaxError(errUnexpectedEOL, r)
		return
	}
	if r.Rune() != '(' {
		err = SyntaxError(errUnexpectedChar, r)
		return
	}
	r.NextRune()
	if !r.EOL() {
		err = SyntaxError(errUnexpectedChar, r)
		return
	}

	var ast AST
	asts := []AST{}
	weights := []float32{}
	finished := false
	for r.Scan() {
		if r.Rune() == ')' && r.LookForward() == NoValue {
			// end of multi-line define expression
			finished = true
			break
		}
		ast, err = readExpr(r, nil)
		if err != nil {
			return
		}

		asts = append(asts, ast)
		weights = append(weights, 1)
	}
	if r.Err() != nil {
		err = r.Err()
		return
	}
	if !finished {
		err = SyntaxError(errUnexpectedEOF, r)
		return
	}
	if len(asts) == 0 {
		err = SyntaxError(errEmptyExpr, r)
		return
	}

	if len(asts) == 1 {
		return asts[0], nil
	} else {
		return &ParallelExpr{asts, weights}, nil
	}
}

// readDef reads the definition statement
func (g *Grammar) readDef(r *reader) error {
	// reads the left part of define expression
	name, err := g.readDefLeft(r)
	err = readSpaces(r, err)
	if err != nil {
		return err
	}
	if r.EOL() {
		return SyntaxError(errUnexpectedEOL, r)
	}

	// read the right part
	var ast AST
	if r.Rune() == '(' && r.LookForward() == NoValue {
		ast, err = g.readDefRightMultiLine(r)
	} else {
		ast, err = g.readDefRightInline(r)
	}
	if err != nil {
		return err
	}

	g.rules[name] = ast
	return nil
}

// read reads and parse the grammar from grammar reader. entry of the grammar
// parsing methods
func (g *Grammar) read(r *reader) error {
	for r.Scan() {
		if r.EOL() {
			// empty line
			continue
		}

		g.readDef(r)
	}

	if r.Err() != nil {
		return r.Err()
	} else {
		return nil
	}
}

// BuildFst build the FST for specific rule in grammar
func (g *Grammar) BuildFst(name string) (fst *nfst.Fst, err error) {
	mutFst := nmutfst.NewMutableFst()
	ast, ok := g.rules[name]
	if !ok {
		err = fmt.Errorf("rule %s not exist", name)
		return
	}

	endState := ast.AddToFst(g, mutFst, 0)
	mutFst.SetFinal(endState, 0)

	// rmdisambig
	mutFst = mutFst.MustRmDisambig()
	fmt.Println(mutFst.String())

	// convert to n-fst
	fst, err = nmutfst.ConvertFst(mutFst)
	return
}

// FromString builds the FST from n-regex string expression
func FromString(expr string) (grammar *Grammar, err error) {
	reader := newStringReader(expr, readerOptions{TrimSpace: true})
	grammar = &Grammar{
		rules: map[string]AST{},
	}

	if err = grammar.read(reader); err != nil {
		return
	}

	return
}
