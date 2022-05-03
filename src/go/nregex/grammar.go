package nregex

import (
	"fmt"

	"github.com/ling0322/nnlp/src/go/nfst"
	"github.com/ling0322/nnlp/src/go/nmutfst"
)

// grammar is a collection of n-regex rules with its class name
type Grammar struct {
	rules    map[string]AST
	captures map[string]bool
}

func GrammarError(message string, refStack []string) error {
	return fmt.Errorf("GrammarError: %s at class <%s>", message, refStack[len(refStack)-1])
}

// readDefLeft reads left part of the define statement, including ::=
func (g *Grammar) readDefLeft(r *reader) (name string, err error) {
	name, err = readRefToken(r)
	err = readSpaces(r, err)
	err = readAndCheckString(r, "::=", err)
	if err != nil {
		return
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

// readCaptures reads the capture list ($captures = <name1> <name2> ...) from
// grammar file
func (g *Grammar) readCaptures(r *reader) error {
	for !r.EOL() {
		name, err := readRefToken(r)
		err = readSpaces(r, err)
		if err != nil {
			return err
		}
		g.captures[name] = true
	}

	return nil
}

// readArgs read arguments from grammar file
func (g *Grammar) readArgs(r *reader) error {
	beginPos := r.Position()
	err := readAndCheckString(r, "$", nil)
	name, err := readName(r, charset(" ="), err)
	err = readSpaces(r, err)
	err = readAndCheckString(r, "=", err)
	err = readSpaces(r, err)
	if err != nil {
		return err
	}

	if name == "capture" {
		err = g.readCaptures(r)
	} else {
		r.SetPosition(beginPos)
		err = SyntaxError(errUnexpectedArgName, r)
	}

	return err
}

// read reads and parse the grammar from grammar reader. entry of the grammar
// parsing methods
func (g *Grammar) read(r *reader) error {
	var err error
	for r.Scan() {
		if r.EOL() {
			// empty line
			continue
		}

		ch := r.Rune()
		if ch == '$' {
			err = g.readArgs(r)
		} else {
			err = g.readDef(r)
		}
		if err != nil {
			return err
		}
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
		rules:    map[string]AST{},
		captures: map[string]bool{},
	}

	if err = grammar.read(reader); err != nil {
		return
	}

	return
}
