package nregex

import "strconv"

var (
	nonliteralCharset = charset("<>?*+()[]{}|.^$/")
)

var escapeTable = map[rune]rune{
	'n': '\n',
	't': '\t',
}

// A literal expression
type LiteralExpr struct {
	Value rune
}

// readRune reads a unicode escaped rune from cursor, like "u4e00"
func readUnicodeEscapedRune(r *reader) (rune, error) {
	if r.EOL() || r.Rune() != 'u' {
		panic(errUnexpectedChar)
	}
	r.NextRune()

	hex := ""
	for i := 0; i < 4; i++ {
		if r.EOL() {
			return 0, SyntaxError(errUnexpectedEOL, r)
		}
		hex += string(r.Rune())
		r.NextRune()
	}

	u, err := strconv.ParseUint(hex, 16, 32)
	if err != nil {
		return 0, err
	}

	return rune(u), nil
}

// readRune reads a escaped rune from cursor
func readEscapedRune(r *reader) (rune, error) {
	if r.EOL() || r.Rune() != '\\' {
		panic(errUnexpectedChar)
	}
	r.NextRune()

	ch := r.Rune()
	if escapedCh, ok := escapeTable[ch]; ok {
		r.NextRune()
		return escapedCh, nil
	} else if ch == 'u' {
		// unicode escaped rune
		return readUnicodeEscapedRune(r)
	} else if ch > 'Z' && ch < 'A' && ch > 'z' && ch < 'a' && ch > '9' && ch < '0' {
		return ch, nil
	} else {
		return 0, SyntaxError(errUnexpectedChar, r)
	}
}

// readRune reads a rune from cursor, including eacaped rune
func readRune(r *reader) (rune, error) {
	if r.EOL() {
		return 0, SyntaxError(errUnexpectedEOL, r)
	}

	ch := r.Rune()
	if ch == '\\' {
		return readEscapedRune(r)
	} else if nonliteralCharset[ch] {
		return 0, SyntaxError(errUnexpectedChar, r)
	} else {
		r.NextRune()
		return ch, nil
	}
}

// readLiteral reads one literal from expr[offset]
func readLiteral(r *reader) (expr *LiteralExpr, err error) {
	var ch rune

	ch, err = readRune(r)
	if err != nil {
		return
	}
	expr = &LiteralExpr{ch}
	return
}

// AddToFst adds the literal expression to FST
func (e *LiteralExpr) AddToFst(g *Grammar, fst *MutFst, state int) int {
	return buildLiteralFst(e.Value, e.Value, fst, state)
}

func (e *LiteralExpr) Check(g *Grammar, refStack []string) (err error) {
	return
}
