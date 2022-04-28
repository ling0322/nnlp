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
func readUnicodeEscapedRune(c *cursor) (rune, error) {
	if c.finished() || c.value() != 'u' {
		panic(errUnexpectedChar)
	}
	c.next()

	hex := ""
	for i := 0; i < 4; i++ {
		if c.finished() {
			return 0, SyntaxError(errUnexpectedEOL, c.offset)
		}
		hex += string(c.value())
		c.next()
	}

	u, err := strconv.ParseUint(hex, 16, 32)
	if err != nil {
		return 0, err
	}

	return rune(u), nil
}

// readRune reads a escaped rune from cursor
func readEscapedRune(c *cursor) (rune, error) {
	if c.finished() || c.value() != '\\' {
		panic(errUnexpectedChar)
	}
	c.next()

	ch := c.value()
	if escapedCh, ok := escapeTable[ch]; ok {
		c.next()
		return escapedCh, nil
	} else if ch == 'u' {
		// unicode escaped rune
		return readUnicodeEscapedRune(c)
	} else if ch > 'Z' && ch < 'A' && ch > 'z' && ch < 'a' && ch > '9' && ch < '0' {
		return ch, nil
	} else {
		return 0, SyntaxError(errUnexpectedChar, c.offset)
	}
}

// readRune reads a rune from cursor, including eacaped rune
func readRune(c *cursor) (rune, error) {
	if c.finished() {
		return 0, SyntaxError(errUnexpectedEOL, c.offset)
	}

	ch := c.value()
	if ch == '\\' {
		return readEscapedRune(c)
	} else if nonliteralCharset[ch] {
		return 0, SyntaxError(errUnexpectedChar, c.offset)
	} else {
		c.next()
		return ch, nil
	}
}

// readLiteral reads one literal from expr[offset]
func readLiteral(c *cursor) (expr *LiteralExpr, err error) {
	var ch rune

	ch, err = readRune(c)
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
