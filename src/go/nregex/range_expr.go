package nregex

import (
	"sort"
	"unicode/utf8"

	"github.com/ling0322/nnlp/src/go/nmutfst"
)

var (
	rangeCharset = charset("wds")
)

const (
	kDefaultState = iota
	kBeginState0
	kBeginState
	kRangeState
	kEndState
)

// Rune range
type Range struct {
	Begin rune
	End   rune
}

// A parallel expression
type RangeExpr struct {
	Charset map[rune]bool
	Ranges  []Range
}

// Stores the state of reading bracket range expression
type bracketStateMachine struct {
	token        rune
	cursor       *cursor
	expr         *RangeExpr
	state        int
	complemented bool
	err          error
}

// readEscapedRange reads an escaped range expression
func readEscapedRange(c *cursor) (*RangeExpr, error) {
	ch := c.value()
	if ch != '\\' {
		panic(errUnexpectedChar)
	}
	c.next()
	if c.finished() {
		return nil, SyntaxError(errUnexpectedEOL, c.offset)
	}

	ch = c.value()
	if ch == 's' {
		c.next()
		return &RangeExpr{charset(" \t\r\n"), nil}, nil
	} else if ch == 'w' {
		c.next()
		return &RangeExpr{
			Charset: charset("_"),
			Ranges:  []Range{{'A', 'Z'}, {'a', 'z'}, {'0', '9'}}}, nil
	} else if ch == 'd' {
		c.next()
		return &RangeExpr{
			Charset: nil,
			Ranges:  []Range{{'0', '9'}}}, nil
	} else {
		return nil, SyntaxError(errUnexpectedChar, c.offset)
	}
}

// onBegin0 reads the begin - characters from cursor. If no ^ in the begining,
// do nothing
func (s *bracketStateMachine) onBegin0() {
	// in this state, it will consumes char - only
	if s.cursor.value() == '^' {
		s.complemented = true
		s.cursor.next()
	}
	s.state = kBeginState
}

// onBegin reads the begin - characters from cursor. If no ^ in the begining,
// do nothing
func (s *bracketStateMachine) onBegin() {
	// in this state, it will consumes char - only
	if s.cursor.value() == '-' {
		s.expr.Charset['-'] = true
		s.cursor.next()
	}
	s.state = kDefaultState
}

// onDefault reads the tokens of bracket expression from cursor.
// switch to kRangeState if '-' found after one token
// switch to kEndState if ']' found
func (s *bracketStateMachine) onDefault() {
	if s.cursor.value() == ']' {
		s.cursor.next()
		s.state = kEndState
		return
	}

	if s.token, s.err = readRune(s.cursor); s.err != nil {
		return
	}
	if s.cursor.finished() {
		s.err = SyntaxError(errUnexpectedEOL, s.cursor.offset)
	}
	if s.cursor.value() == '-' {
		s.state = kRangeState
		s.cursor.next()
	} else {
		s.expr.Charset[s.token] = true
	}
}

// onRange reads the another token of range expression from cursor and add the
// range into expr
func (s *bracketStateMachine) onRange() {
	dashOffset := s.cursor.offset - 1
	if s.token == noValue {
		panic(errInternalErr)
	}
	if s.cursor.value() == ']' {
		s.err = SyntaxError(errUnexpectedChar, s.cursor.offset)
		return
	}

	var token rune
	token, s.err = readRune(s.cursor)
	if s.err != nil {
		return
	}
	if s.token > token {
		s.err = SyntaxError(errRangeOutOfOrder, dashOffset)
		return
	}

	s.expr.Ranges = append(s.expr.Ranges, Range{s.token, token})
	s.state = kDefaultState
}

// process the reader using state machine
func (s *bracketStateMachine) process() {
	for !s.cursor.finished() {
		if s.state == kBeginState0 {
			s.onBegin0()
		} else if s.state == kBeginState {
			s.onBegin()
		} else if s.state == kDefaultState {
			s.onDefault()
		} else if s.state == kRangeState {
			s.onRange()
		} else if s.state == kEndState {
			break
		} else {
			panic(errInvalidState)
		}

		if s.err != nil {
			return
		}
	}
}

// getComplementRange gets the complemented range from expr
func getComplementRange(expr *RangeExpr) (complExpr *RangeExpr) {
	var ranges []Range
	ranges = append(ranges, expr.Ranges...)
	for ch := range expr.Charset {
		ranges = append(ranges, Range{ch, ch})
	}

	// sort thr range
	sort.Slice(ranges, func(i, j int) bool {
		return ranges[i].Begin < ranges[j].Begin
	})

	complExpr = &RangeExpr{map[rune]bool{}, []Range{}}

	var ch rune
	for _, r := range ranges {
		if ch < r.Begin-1 {
			complExpr.Ranges = append(complExpr.Ranges, Range{ch, r.Begin - 1})
			ch = r.End + 1
		} else if ch == r.Begin-1 {
			complExpr.Charset[ch] = true
			ch = r.End + 1
		} else if ch >= r.Begin && ch <= r.End {
			ch = r.End + 1
		}
		// do nothing if ch > r.End
	}
	complExpr.Ranges = append(complExpr.Ranges, Range{ch, utf8.MaxRune})

	return
}

// readBracketRange reads a square bracket range expression
func readBracketRange(c *cursor) (*RangeExpr, error) {
	beginOffset := c.offset
	ch := c.value()
	if ch != '[' {
		return nil, SyntaxError(errUnexpectedChar, c.offset)
	}
	c.next()

	expr := &RangeExpr{map[rune]bool{}, []Range{}}
	fsm := &bracketStateMachine{
		token:        noValue,
		cursor:       c,
		expr:         expr,
		state:        kBeginState0,
		complemented: false,
		err:          nil,
	}

	fsm.process()
	if fsm.err != nil {
		return nil, fsm.err
	}

	if len(expr.Charset) == 0 && len(expr.Ranges) == 0 {
		return nil, SyntaxError(errEmptyExpr, beginOffset)
	}

	if fsm.complemented {
		expr = getComplementRange(expr)
	}
	return expr, nil
}

// readRange reads a range expression from cursor
func readRange(c *cursor) (*RangeExpr, error) {
	if c.finished() {
		return nil, SyntaxError(errUnexpectedEOL, c.offset)
	}

	ch := c.expr[c.offset]
	if ch == '\\' {
		return readEscapedRange(c)
	} else if ch == '[' {
		return readBracketRange(c)
	} else {
		return nil, SyntaxError(errUnexpectedChar, c.offset)
	}
}

// AddToFst adds the literal expression to FST
func (e *RangeExpr) AddToFst(g *Grammar, fst *MutFst, state int) int {
	endState := fst.AddState()
	for ch := range e.Charset {
		symbol := nmutfst.NewSymbol(string(ch))
		fst.AddArc(state, nmutfst.Arc{
			NextState:    endState,
			InputSymbol:  symbol,
			OutputSymbol: symbol,
			Weight:       0})
	}

	for _, r := range e.Ranges {
		rSym := nmutfst.RangeSymbol(int(r.Begin), int(r.End))
		fst.AddArc(state, nmutfst.Arc{
			NextState:    endState,
			InputSymbol:  rSym,
			OutputSymbol: nmutfst.AlphaSym,
			Weight:       0})
	}

	return endState
}

func (e *RangeExpr) Check(g *Grammar, refStack []string) (err error) {
	return
}
