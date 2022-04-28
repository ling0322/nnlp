package nregex

import "fmt"

const noValue = -1

type cursor struct {
	expr   []rune
	offset int
}

// finished returns true if end of expression reached
func (p *cursor) finished() bool {
	return p.offset >= len(p.expr)
}

// value returns the current rune
func (p *cursor) value() rune {
	if p.finished() {
		panic(errUnexpectedEOL)
	}
	return p.expr[p.offset]
}

// next moves forward the cursor
func (p *cursor) next() {
	if p.finished() {
		panic(errUnexpectedEOL)
	}
	p.offset++
}

// lookForward returns the character at offset+1. If no more charactes, return
// noValue
func (p *cursor) lookForward() rune {
	if p.finished() {
		panic(errUnexpectedEOL)
	}
	if p.offset == len(p.expr)-1 {
		return noValue
	}
	return p.expr[p.offset]
}

func SyntaxError(message string, offset int) error {
	return fmt.Errorf("SyntaxError: %s at offset %d", message, offset)
}
func Parse(expr string) (AST, error) {
	c := &cursor{
		expr:   []rune(expr),
		offset: 0,
	}

	return parseExpr(c, nil)
}
