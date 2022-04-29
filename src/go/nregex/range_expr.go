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
	reader       *reader
	expr         *RangeExpr
	state        int
	complemented bool
	err          error
}

// readEscapedRange reads an escaped range expression
func readEscapedRange(r *reader) (*RangeExpr, error) {
	ch := r.Rune()
	if ch != '\\' {
		panic(errUnexpectedChar)
	}
	r.NextRune()
	if r.EOL() {
		return nil, SyntaxError(errUnexpectedEOL, r)
	}

	ch = r.Rune()
	if ch == 's' {
		r.NextRune()
		return &RangeExpr{charset(" \t\r\n"), nil}, nil
	} else if ch == 'w' {
		r.NextRune()
		return &RangeExpr{
			Charset: charset("_"),
			Ranges:  []Range{{'A', 'Z'}, {'a', 'z'}, {'0', '9'}}}, nil
	} else if ch == 'd' {
		r.NextRune()
		return &RangeExpr{
			Charset: nil,
			Ranges:  []Range{{'0', '9'}}}, nil
	} else {
		return nil, SyntaxError(errUnexpectedChar, r)
	}
}

// onBegin0 reads the begin - characters from cursor. If no ^ in the begining,
// do nothing
func (s *bracketStateMachine) onBegin0() {
	// in this state, it will consumes char - only
	if s.reader.Rune() == '^' {
		s.complemented = true
		s.reader.Rune()
	}
	s.state = kBeginState
}

// onBegin reads the begin - characters from cursor. If no ^ in the begining,
// do nothing
func (s *bracketStateMachine) onBegin() {
	// in this state, it will consumes char - only
	if s.reader.Rune() == '-' {
		s.expr.Charset['-'] = true
		s.reader.NextRune()
	}
	s.state = kDefaultState
}

// onDefault reads the tokens of bracket expression from cursor.
// switch to kRangeState if '-' found after one token
// switch to kEndState if ']' found
func (s *bracketStateMachine) onDefault() {
	if s.reader.Rune() == ']' {
		s.reader.NextRune()
		s.state = kEndState
		return
	}

	if s.token, s.err = readRune(s.reader); s.err != nil {
		return
	}
	if s.reader.EOL() {
		s.err = SyntaxError(errUnexpectedEOL, s.reader)
	}
	if s.reader.Rune() == '-' {
		s.state = kRangeState
		s.reader.NextRune()
	} else {
		s.expr.Charset[s.token] = true
	}
}

// onRange reads the another token of range expression from cursor and add the
// range into expr
func (s *bracketStateMachine) onRange() {
	dashOffset := s.reader.Position() - 1
	if s.token == NoValue {
		panic(errInternalErr)
	}
	if s.reader.Rune() == ']' {
		s.err = SyntaxError(errUnexpectedChar, s.reader)
		return
	}

	var token rune
	token, s.err = readRune(s.reader)
	if s.err != nil {
		return
	}
	if s.token > token {
		s.reader.SetPosition(dashOffset)
		s.err = SyntaxError(errRangeOutOfOrder, s.reader)
		return
	}

	s.expr.Ranges = append(s.expr.Ranges, Range{s.token, token})
	s.state = kDefaultState
}

// process the reader using state machine
func (s *bracketStateMachine) process() {
	for !s.reader.EOL() {
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
func readBracketRange(r *reader) (*RangeExpr, error) {
	beginOffset := r.Position()
	ch := r.Rune()
	if ch != '[' {
		return nil, SyntaxError(errUnexpectedChar, r)
	}
	r.NextRune()

	expr := &RangeExpr{map[rune]bool{}, []Range{}}
	fsm := &bracketStateMachine{
		token:        NoValue,
		reader:       r,
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
		r.SetPosition(beginOffset)
		return nil, SyntaxError(errEmptyExpr, r)
	}

	if fsm.complemented {
		expr = getComplementRange(expr)
	}
	return expr, nil
}

// readRange reads a range expression from cursor
func readRange(r *reader) (*RangeExpr, error) {
	if r.EOL() {
		return nil, SyntaxError(errUnexpectedEOL, r)
	}

	ch := r.Rune()
	if ch == '\\' {
		return readEscapedRange(r)
	} else if ch == '[' {
		return readBracketRange(r)
	} else {
		return nil, SyntaxError(errUnexpectedChar, r)
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
