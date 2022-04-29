package nregex

import (
	"bufio"
	"strings"
)

// Options for Reader
type readerOptions struct {
	TrimSpace bool
}

// A scanner with filename and line number informatoion
type reader struct {
	filename string
	ln       int
	expr     []rune
	offset   int
	eof      bool

	scannar *bufio.Scanner
	options readerOptions
}

// newStringReader creates a reader of string
func newStringReader(text string, options readerOptions) *reader {
	r := strings.NewReader(text)
	return &reader{
		filename: "<inline-string>",
		ln:       0,
		expr:     nil,
		offset:   0,
		scannar:  bufio.NewScanner(r),
		options:  options,
	}
}

// The same as scanner.Scan
func (r *reader) Scan() bool {
	ok := r.scannar.Scan()
	if ok {
		r.ln++
		s := r.scannar.Text()
		if r.options.TrimSpace {
			s = strings.TrimSpace(s)
		}
		r.expr = []rune(s)
		r.offset = 0
	} else {
		r.eof = true
	}

	return ok
}

// The same as scanner.Err
func (r *reader) Err() error {
	return r.scannar.Err()
}

// EOL returns true if end of line reached
func (r *reader) EOL() bool {
	return r.offset >= len(r.expr)
}

// value returns the current rune
func (r *reader) Rune() rune {
	if r.EOL() {
		panic(errUnexpectedEOL)
	}
	return r.expr[r.offset]
}

// String returns the string starting from current position
func (r *reader) String() string {
	return string(r.expr[r.offset])
}

// next moves forward the cursor
func (r *reader) NextRune() {
	if r.EOL() {
		panic(errUnexpectedEOL)
	}
	r.offset++
}

// MoveForward moves the cursor forward n runes
func (r *reader) MoveForward(n int) {
	if r.EOL() {
		panic(errUnexpectedEOL)
	}
	r.offset += n
}

// Cursor returns current position in line
func (r *reader) Position() int {
	return r.offset
}

// SetCursor move the line position of reader to offset
func (r *reader) SetPosition(offset int) {
	r.offset = offset
}

// LookForward returns the character at offset+1. If no more charactes, return
// noValue
func (r *reader) LookForward() rune {
	if r.EOL() {
		panic(errUnexpectedEOL)
	}
	if r.offset == len(r.expr)-1 {
		return NoValue
	}
	return r.expr[r.offset]
}

// Close the reader
func (f *reader) Close() {
}
