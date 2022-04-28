package nregex

import (
	"fmt"
	"regexp"
	"strings"

	"github.com/ling0322/nnlp/src/go/nfst"
	"github.com/ling0322/nnlp/src/go/nmutfst"
)

// grammar is a collection of n-regex rules with its class name
type Grammar struct {
	rules map[string]AST
}

var (
	regexSingleLnGrammar = regexp.MustCompile(`^<([^\>\[\]\(\){}^:;,\.\/\\&%$#@?*+~\"\'\t\n\r` + "` ]+?)> *::= *(.*)$")
)

func GrammarError(message string, refStack []string) error {
	return fmt.Errorf("GrammarError: %s at class <%s>", message, refStack[len(refStack)-1])
}

// read reads and parse the grammar from grammar reader
func (g *Grammar) read(reader *grammarReader) (err error) {
	for reader.Scan() {
		line := reader.Text()
		line = strings.TrimSpace(line)
		if line == "" {
			// skip empty lines
			continue
		}

		match := regexSingleLnGrammar.FindStringSubmatch(line)
		if match == nil {
			err = fmt.Errorf("line %d: invalid class definition", reader.Line())
			return
		}

		name := match[1]
		expr := match[2]

		var ast AST
		if ast, err = Parse(expr); err != nil {
			return
		}

		g.rules[name] = ast
	}
	if err = reader.Err(); err != nil {
		return
	}

	return
}

// BuildFst build the FST for specific rule in grammar
func (g *Grammar) BuildFst(name string) (fst *nfst.Fst, err error) {
	mutFst := nmutfst.NewMutableFst()
	ast, ok := g.rules[name]
	if !ok {
		err = fmt.Errorf("rule %s not exist", name)
		return
	}

	endState := ast.AddToFst(g, mutFst, 0)
	mutFst.SetFinal(endState, 0)

	// rmdisambig
	mutFst = mutFst.MustRmDisambig()
	fmt.Println(mutFst.String())

	// convert to n-fst
	fst, err = nmutfst.ConvertFst(mutFst)
	return
}

// FromString builds the FST from n-regex string expression
func FromString(expr string) (grammar *Grammar, err error) {
	reader := newStringScanner(expr)
	grammar = &Grammar{
		rules: map[string]AST{},
	}

	if err = grammar.read(reader); err != nil {
		return
	}

	return
}
