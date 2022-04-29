package nregex

import (
	"fmt"
	"log"
)

var invalidCharset = charset("<>?*+()[]{}|^$:;,\\~!@#$%&-=`\"'/")

// A reference expression
type RefExpr struct {
	Name string
}

// readRefToken reads a reference token <name> from cursor
func readRefToken(r *reader) (name string, err error) {
	if r.EOL() {
		err = SyntaxError(errUnexpectedEOL, r)
		return
	} else if r.Rune() != '<' {
		err = SyntaxError(errUnexpectedChar, r)
		return
	}

	name = ""
	r.NextRune()
	for {
		if r.EOL() {
			err = SyntaxError(errUnexpectedEOL, r)
			return
		}
		ch := r.Rune()
		if ch == '>' {
			r.NextRune()
			break
		} else if invalidCharset[ch] {
			log.Fatalln(ch)
			err = SyntaxError(errUnexpectedChar, r)
			return
		}
		name += string(ch)
		r.NextRune()
	}

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

// AddToFst adds the reference expression to FST
func (e *RefExpr) AddToFst(g *Grammar, fst *MutFst, state int) int {
	ast, ok := g.rules[e.Name]
	if !ok {
		// Check() ensures the e.Name always exists in rules
		panic(fmt.Sprintf(errRefClassNotExist, e.Name))
	}

	return ast.AddToFst(g, fst, state)
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
