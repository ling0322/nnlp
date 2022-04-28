package nmutfst

import (
	"fmt"
	"regexp"
	"strconv"
	"strings"
)

type Symbol interface {
	MustValue() string
	Escape() string
	IsSpecial() bool
	IsDisambig() bool
	IsReserved() bool
	IsRange() bool
	MustParseRange() (begin, end rune)
	Value() (s string, err error)
}

type symbolImpl string

// epsilon symbol
const (
	EpsilonSym = symbolImpl("<eps>")
	AlphaSym   = symbolImpl("<alpha>")
	BetaSym    = symbolImpl("<beta>")
	GammaSym   = symbolImpl("<gamma>")
	DeltaSym   = symbolImpl("<delta>")
	RhoSym     = symbolImpl("<rho>")
	SigmaSym   = symbolImpl("<sigma>")
	PhiSym     = symbolImpl("<phi>")
)

var (
	regexpRangeSymbol = regexp.MustCompile("^<range:([0-9a-fA-F]+)-([0-9a-fA-F]+)>$")
)

const (
	EpsilonSymID = 0
	AlphaSymID   = iota
	BetaSymID
	GammaSymID
	DeltaSymID
	RhoSymID
	SigmaSymID
	PhiSymID
)

// NewSymbol creates a symbol from string
func NewSymbol(s string) Symbol {
	if s == "" {
		panic("unexpected empty symbol")
	}

	s = strings.Replace(s, "\\", "\\\\", -1)
	s = strings.Replace(s, "<", "\\<", -1)
	s = strings.Replace(s, ">", "\\>", -1)
	s = strings.Replace(s, "#", "\\#", -1)
	s = strings.Replace(s, "\t", "\\t", -1)
	s = strings.Replace(s, " ", "\\S", -1)
	s = strings.Replace(s, "\n", "\\n", -1)
	s = strings.Replace(s, "\r", "\\r", -1)
	return symbolImpl(s)
}

// DisambigSymbol returns a disambig symbol
func DisambigSymbol(id int) Symbol {
	return symbolImpl(fmt.Sprintf("#%d", id))
}

// RangeSymbol returns a range symbol represents [start, end]
func RangeSymbol(start, end int) Symbol {
	return symbolImpl(fmt.Sprintf("<range:%x-%x>", start, end))
}

// MustValue returns the unescaped string value of a symbol. panic if it's
// a special symbol
func (sym symbolImpl) MustValue() (s string) {
	var err error
	if s, err = sym.Value(); err != nil {
		panic(err)
	}

	return
}

// Value returns the unescaped string value of a symbol. return err if it's
// a special symbol
func (sym symbolImpl) Value() (s string, err error) {
	s = string(sym)
	if s == "" {
		err = fmt.Errorf("unexpected empty symbol")
		return
	}
	if sym.IsSpecial() {
		err = fmt.Errorf("unable to convert special symbol to string")
		return
	}

	s = strings.Replace(s, "\\<", "<", -1)
	s = strings.Replace(s, "\\>", ">", -1)
	s = strings.Replace(s, "\\#", "#", -1)
	s = strings.Replace(s, "\\S", " ", -1)
	s = strings.Replace(s, "\\t", "\t", -1)
	s = strings.Replace(s, "\\n", "\n", -1)
	s = strings.Replace(s, "\\r", "\r", -1)
	s = strings.Replace(s, "\\\\", "\\", -1)
	return
}

// Escape returns the escaped string of symbol
func (sym symbolImpl) Escape() string {
	return string(sym)
}

// IsSpecial return true if it is a special symbol like: <eps>, #1, #2, ...
func (sym symbolImpl) IsSpecial() bool {
	return sym[0] == '#' || sym[0] == '<'
}

// IsSpecial return true if it is a range symbol
func (sym symbolImpl) IsRange() bool {
	return regexpRangeSymbol.MatchString(string(sym))
}

// mustParseHex convert a hex string to int, panic if fail
func mustParseHex(s string) int64 {
	v, err := strconv.ParseInt(s, 16, 32)
	if err != nil {
		panic(err)
	}

	return v
}

// MustParseRange returns begin and end of a range symbol. panic is failed
func (sym symbolImpl) MustParseRange() (begin, end rune) {
	match := regexpRangeSymbol.FindStringSubmatch(string(sym))
	if match == nil {
		panic("invalid range symbol")
	}

	begin = rune(mustParseHex(match[1]))
	end = rune(mustParseHex(match[2]))
	return
}

// IsDisambig return true if it is a disambiguation symbol
func (sym symbolImpl) IsDisambig() bool {
	return sym[0] == '#'
}

func (sym symbolImpl) IsReserved() bool {
	return sym[0] == '<'
}
