package nregex

import (
	"fmt"
	"regexp"
	"strconv"
	"unicode/utf8"

	"github.com/ling0322/nnlp/src/go/nmutfst"
)

// A closure expression
type ClosureExpr struct {
	Min   int
	Max   int
	Token AST
}

var (
	regexpClosureMN = regexp.MustCompile(`^{(\d+),(\d+)}`)
	regexpClosureMI = regexp.MustCompile(`^{(\d+),}`)
	regexpClosureM  = regexp.MustCompile(`^{(\d+)}`)
)

// atoi is a wrapper of strconv.Atoi
func atoi(s string, err error) (int, error) {
	if err != nil {
		return -1, err
	}
	i, err := strconv.Atoi(s)
	if err != nil {
		return -1, err
	}
	return i, nil
}

// atoi is a wrapper of strconv.Atoi
func checkMinMax(min, max int, err error) error {
	if err != nil {
		return err
	}
	if max >= 0 && max < min {
		return fmt.Errorf("invalid min and max")
	}
	return nil
}

// readRangeClosure reads a range closure from cursor. token will be placed into
// the ClosureExpr
func readRangeClosure(r *reader, token AST) (*ClosureExpr, error) {
	if r.EOL() || r.Rune() != '{' {
		panic(errUnexpectedChar)
	}

	s := string(r.expr[r.offset:])
	var m, n, expr string
	if match := regexpClosureMN.FindStringSubmatch(s); match != nil {
		m = match[1]
		n = match[2]
		expr = match[0]
	} else if match := regexpClosureMI.FindStringSubmatch(s); match != nil {
		m = match[1]
		n = strconv.Itoa(-1)
		expr = match[0]
	} else if match := regexpClosureM.FindStringSubmatch(s); match != nil {
		m = match[1]
		n = match[1]
		expr = match[0]
	} else {
		return nil, SyntaxError(errInvalidClosere, r)
	}

	min, err := atoi(m, nil)
	max, err := atoi(n, err)
	err = checkMinMax(min, max, err)
	if err != nil {
		return nil, SyntaxError(errInvalidClosere, r)
	}

	r.MoveForward(utf8.RuneCountInString(expr))
	return &ClosureExpr{min, max, token}, nil
}

// readClosure reads a closure expression from reader. It will take the last
// element as token in ClosureExpr
func readClosure(r *reader, expr []AST) (*ClosureExpr, error) {
	if r.EOL() {
		return nil, SyntaxError(errUnexpectedEOL, r)
	}
	if expr == nil {
		return nil, SyntaxError(errInvalidClosere, r)
	}

	token := expr[len(expr)-1]

	ch := r.Rune()
	if ch == '*' {
		r.offset++
		return &ClosureExpr{0, -1, token}, nil
	} else if ch == '+' {
		r.offset++
		return &ClosureExpr{1, -1, token}, nil
	} else if ch == '?' {
		r.offset++
		return &ClosureExpr{0, 1, token}, nil
	} else if ch == '{' {
		return readRangeClosure(r, token)
	} else {
		return nil, SyntaxError(errInvalidClosere, r)
	}
}

// AddToFst adds the closure expression to FST
func (e *ClosureExpr) AddToFst(g *Grammar, fst *MutFst, state int) int {
	// put N tokens to FST
	for i := 0; i < e.Min; i++ {
		state = e.Token.AddToFst(g, fst, state)
	}

	endState := fst.AddState()
	fst.AddArc(state, nmutfst.Arc{
		NextState:    endState,
		InputSymbol:  nmutfst.EpsilonSym,
		OutputSymbol: nmutfst.EpsilonSym,
		Weight:       0})
	if e.Max == -1 {
		// infinite closure, add a self-loop at endState
		state = e.Token.AddToFst(g, fst, endState)
		fst.AddArc(state, nmutfst.Arc{
			NextState:    endState,
			InputSymbol:  nmutfst.DisambigSymbol(1),
			OutputSymbol: nmutfst.EpsilonSym,
			Weight:       0})
		return endState
	}

	for i := e.Min; i < e.Max; i++ {
		state = e.Token.AddToFst(g, fst, state)
		fst.AddArc(state, nmutfst.Arc{
			NextState:    endState,
			InputSymbol:  nmutfst.DisambigSymbol(1),
			OutputSymbol: nmutfst.EpsilonSym,
			Weight:       0})
	}
	return endState
}

func (e *ClosureExpr) Check(g *Grammar, refStack []string) (err error) {
	return
}
