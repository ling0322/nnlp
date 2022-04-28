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

// readRef reads a reference expression from cursor
func readRef(c *cursor) (e *RefExpr, err error) {
	if c.finished() {
		err = SyntaxError(errUnexpectedEOL, c.offset)
		return
	} else if c.expr[c.offset] != '<' {
		err = SyntaxError(errUnexpectedChar, c.offset)
		return
	}

	name := ""
	c.offset++
	for {
		if c.finished() {
			err = SyntaxError(errUnexpectedEOL, c.offset)
			return
		}
		ch := c.expr[c.offset]
		if ch == '>' {
			c.offset++
			break
		} else if invalidCharset[ch] {
			log.Fatalln(ch)
			err = SyntaxError(errUnexpectedChar, c.offset)
			return
		}
		name += string(ch)
		c.offset++
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
