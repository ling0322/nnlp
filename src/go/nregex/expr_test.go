package nregex

import (
	"reflect"
	"strings"
	"testing"

	"github.com/ling0322/nnlp/src/go/nfst"
	"github.com/ling0322/nnlp/src/go/nnlp"
)

// assertOk calls t.Error is err is not nil
func assertOk(t *testing.T, err error) {
	if err != nil {
		t.Log(err)
		t.FailNow()
	}
}

// assertErr calls t.Error is err is nil
func assertErr(t *testing.T, err error) {
	if err == nil {
		t.Log("err != nil expected")
		t.FailNow()
	}
}

// assertOk calls t.Error is err is not nil
func assertEqual(t *testing.T, a, b any) {
	if !reflect.DeepEqual(a, b) {
		t.Logf("not equal: %v != %v", a, b)
		t.FailNow()
	}
}

// assertBuildFst builds the fst and assert it should success
func assertBuildFst(t *testing.T, expr, name string) *nfst.Fst {
	grammar, err := FromString(expr)
	assertOk(t, err)

	fst, err := grammar.BuildFst(name)
	assertOk(t, err)

	return fst
}

// assertDecode decodes input using decoder and assert that decoderOutput equals
// output
func assertDecode(t *testing.T, decoder *nnlp.Decoder, input, output string) {
	res, err := decoder.DecodeString(input)
	assertOk(t, err)

	assertEqual(t, strings.Join(res, ""), output)
}

// assertDecodeFail decodes input using decoder and assert that decode will fail
func assertDecodeFail(t *testing.T, decoder *nnlp.Decoder, input string) {
	_, err := decoder.DecodeString(input)
	assertErr(t, err)
}

// TestExpr tests basic n-regex parsing, FST generation and decoding
func TestExpr(t *testing.T) {
	fst := assertBuildFst(t, "<weather> ::= weather in seattle", "weather")
	decoder := nnlp.NewDecoder(fst, 8)

	assertDecode(t, decoder, "weather in seattle", "weather in seattle")
}

// TestParallelExpr tests literal n-regex expression
func TestLiteralExpr(t *testing.T) {
	fst := assertBuildFst(t, "<weather> ::= hi\\tseattle", "weather")
	decoder := nnlp.NewDecoder(fst, 8)
	assertDecode(t, decoder, "hi\tseattle", "hi\tseattle")

	fst = assertBuildFst(t, "<hello> ::= hello \u4e16界", "hello")
	decoder = nnlp.NewDecoder(fst, 8)
	assertDecode(t, decoder, "hello 世界", "hello 世界")
}

// TestParallelExpr tests parallel n-regex expression
func TestParallelExpr(t *testing.T) {
	fst := assertBuildFst(t, "<weather> ::= weather (in|of) seattle", "weather")
	decoder := nnlp.NewDecoder(fst, 8)

	assertDecode(t, decoder, "weather in seattle", "weather in seattle")
}

var refExprA = `
<weather> ::= <city> weather
<city> ::= (seattle|bellevue|redmond)
`

func TestRefExpr(t *testing.T) {
	fst := assertBuildFst(t, refExprA, "weather")
	decoder := nnlp.NewDecoder(fst, 8)

	assertDecode(t, decoder, "seattle weather", "seattle weather")
	assertDecode(t, decoder, "bellevue weather", "bellevue weather")
	assertDecode(t, decoder, "redmond weather", "redmond weather")
	assertDecodeFail(t, decoder, "suzhou weather")
}

func TestClosureExpr(t *testing.T) {
	fst := assertBuildFst(t, "<hello> ::= he*llo", "hello")
	decoder := nnlp.NewDecoder(fst, 8)
	assertDecode(t, decoder, "hllo", "hllo")
	assertDecode(t, decoder, "hello", "hello")
	assertDecode(t, decoder, "heello", "heello")
	assertDecode(t, decoder, "heeello", "heeello")
	assertDecodeFail(t, decoder, "helllo")

	fst = assertBuildFst(t, "<hello> ::= he+llo", "hello")
	decoder = nnlp.NewDecoder(fst, 8)
	assertDecode(t, decoder, "hello", "hello")
	assertDecode(t, decoder, "heello", "heello")
	assertDecode(t, decoder, "heeello", "heeello")
	assertDecodeFail(t, decoder, "hllo")

	fst = assertBuildFst(t, "<hello> ::= he?llo", "hello")
	decoder = nnlp.NewDecoder(fst, 8)
	assertDecode(t, decoder, "hllo", "hllo")
	assertDecode(t, decoder, "hello", "hello")
	assertDecodeFail(t, decoder, "heello")
	assertDecodeFail(t, decoder, "heeello")

	fst = assertBuildFst(t, "<hello> ::= he{3}llo", "hello")
	decoder = nnlp.NewDecoder(fst, 8)
	assertDecode(t, decoder, "heeello", "heeello")
	assertDecodeFail(t, decoder, "hello")
	assertDecodeFail(t, decoder, "heeeello")

	fst = assertBuildFst(t, "<hello> ::= he{3,}llo", "hello")
	decoder = nnlp.NewDecoder(fst, 8)
	assertDecode(t, decoder, "heeello", "heeello")
	assertDecode(t, decoder, "heeeello", "heeeello")
	assertDecode(t, decoder, "heeeeello", "heeeeello")
	assertDecodeFail(t, decoder, "hllo")
	assertDecodeFail(t, decoder, "hello")
	assertDecodeFail(t, decoder, "heello")

	fst = assertBuildFst(t, "<hello> ::= he{2,4}llo", "hello")
	decoder = nnlp.NewDecoder(fst, 8)
	assertDecode(t, decoder, "heello", "heello")
	assertDecode(t, decoder, "heeello", "heeello")
	assertDecode(t, decoder, "heeeello", "heeeello")
	assertDecodeFail(t, decoder, "hllo")
	assertDecodeFail(t, decoder, "hello")
	assertDecodeFail(t, decoder, "heeeeello")
}

var closureExprA = `
<city> ::= ( bellevue| redmond| seattle)
<weather> ::= weather( in)?<city>*
`

func TestClosureExprComplex(t *testing.T) {
	fst := assertBuildFst(t, closureExprA, "weather")
	decoder := nnlp.NewDecoder(fst, 8)
	assertDecode(t, decoder, "weather bellevue", "weather bellevue")
	assertDecode(t, decoder, "weather in seattle", "weather in seattle")
	assertDecode(t, decoder, "weather", "weather")
	assertDecode(t, decoder, "weather in seattle bellevue", "weather in seattle bellevue")
}

func TestRangeExpr(t *testing.T) {
	fst := assertBuildFst(t, "<hi> ::= hi [abc0-9]+", "hi")
	decoder := nnlp.NewDecoder(fst, 8)
	assertDecode(t, decoder, "hi abc123cbaaabbcc002233", "hi abc123cbaaabbcc002233")
}

var multiLineExpr = `
<city> ::= ( 
	bellevue
	redmond
	seattle
)
<weather> ::= weather in <city>
`

func TestMultiLineExpr(t *testing.T) {
	fst := assertBuildFst(t, multiLineExpr, "weather")
	decoder := nnlp.NewDecoder(fst, 8)
	assertDecode(t, decoder, "weather in bellevue", "weather in bellevue")
	assertDecode(t, decoder, "weather in seattle", "weather in seattle")
}

var captureExpr = `
$capture = <city>
<city> ::= ( 
	bellevue
	redmond
	seattle
)
<weather> ::= weather in <city>
`

func TestCapture(t *testing.T) {
	fst := assertBuildFst(t, captureExpr, "weather")
	decoder := nnlp.NewDecoder(fst, 8)
	assertDecode(t, decoder, "weather in seattle", "weather in <city>seattle</city>")
}
