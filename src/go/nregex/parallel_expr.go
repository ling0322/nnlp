package nregex

import (
	"math"

	"github.com/ling0322/nnlp/src/go/nmutfst"
)

// A parallel expression
type ParallelExpr struct {
	Expressions []AST
	Weights     []float32
}

// readParallel reads a parallel expression from expr[offset]
func readParallel(r *reader) (exprAst AST, err error) {
	parallelAsts := []AST{}
	ch := r.Rune()
	if ch != '(' {
		err = SyntaxError(errUnexpectedChar, r)
		return
	}

	r.NextRune()
	var ast AST
	endChars := map[rune]bool{')': true, '|': true}
	for {
		ast, err = readExpr(r, endChars)
		if err != nil {
			return
		}

		if r.EOL() || !endChars[r.Rune()] {
			err = SyntaxError(errUnexpectedEOL, r)
			return
		}

		parallelAsts = append(parallelAsts, ast)
		if r.Rune() == ')' {
			r.NextRune()
			break
		} else if r.Rune() == '|' {
			r.NextRune()
		} else {
			err = SyntaxError(errUnexpectedChar, r)
			return
		}
	}

	// inline parallel expression do not have weights
	weights := []float32{}
	for range parallelAsts {
		weights = append(weights, 1)
	}

	if len(parallelAsts) == 0 {
		err = SyntaxError(errEmptyExpr, r)
	} else if len(parallelAsts) == 1 {
		exprAst = parallelAsts[0]
	} else {
		exprAst = &ParallelExpr{
			Expressions: parallelAsts,
			Weights:     weights,
		}
	}
	return
}

// AddToFst adds the parallel expression to FST
func (e *ParallelExpr) AddToFst(g *Grammar, fst *MutFst, state int) int {
	endState := fst.AddState()

	// compute sum of weights to normalize
	var sumWeight float32
	for _, weight := range e.Weights {
		sumWeight += weight
	}

	for i, expr := range e.Expressions {
		state := expr.AddToFst(g, fst, state)

		weight := e.Weights[i]
		cost := float32(-math.Log(float64(weight / sumWeight)))

		// an dismbig arc to endState
		fst.AddArc(state, nmutfst.Arc{
			NextState:    endState,
			InputSymbol:  nmutfst.DisambigSymbol(i + 1),
			OutputSymbol: nmutfst.EpsilonSym,
			Weight:       cost,
		})
	}

	// this node will clear prefix
	return endState
}

func (e *ParallelExpr) Check(g *Grammar, refStack []string) (err error) {
	if len(e.Expressions) != len(e.Weights) {
		err = GrammarError(errInternalErr, refStack)
		return
	}

	for _, ast := range e.Expressions {
		if err = ast.Check(g, refStack); err != nil {
			return
		}
	}
	return
}
