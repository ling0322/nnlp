package nregex

// A expression that contain a sequence of ASTs
type Expr struct {
	Tokens []AST
}

var closureCharset = charset("*+?{")

// parseExpr reads an expression from expr[offset] until some specific characters
// occured or end-of-expression reached
func parseExpr(c *cursor, endChars map[rune]bool) (exprAst AST, err error) {
	asts := []AST{}
	var ast AST
	for !c.finished() {
		ch := c.value()
		ch2 := c.lookForward()
		if endChars != nil && endChars[ch] {
			break
		} else if ch == '(' {
			ast, err = readParallel(c)
		} else if ch == '<' {
			ast, err = readRef(c)
		} else if closureCharset[ch] {
			ast, err = readClosure(c, asts)
			// closure expression will always take last token in asts
			asts = asts[:len(asts)-1]
		} else if ch == '[' || ch == '\\' && rangeCharset[ch2] {
			ast, err = readRange(c)
		} else {
			ast, err = readLiteral(c)
		}

		if err != nil {
			return
		}
		asts = append(asts, ast)
	}

	if len(asts) == 0 {
		err = SyntaxError(errEmptyExpr, c.offset)
	} else if len(asts) == 1 {
		exprAst = asts[0]
	} else {
		exprAst = &Expr{
			Tokens: asts,
		}
	}
	return
}

// AddToFst adds the expression to FST
func (e *Expr) AddToFst(g *Grammar, fst *MutFst, state int) int {
	for _, ast := range e.Tokens {
		state = ast.AddToFst(g, fst, state)
	}

	return state
}

func (e *Expr) Check(g *Grammar, refStack []string) (err error) {
	for _, ast := range e.Tokens {
		if err = ast.Check(g, refStack); err != nil {
			return
		}
	}
	return
}
