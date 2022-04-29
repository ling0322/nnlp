package nregex

// Abstract syntax tree for n-regex
type AST interface {
	// Checks if this node and its child nodes are correct
	// mainly check 2 things
	//   cycle reference (regular grammar didn't supoort it)
	//   reference class not exist
	// refStack is the stack of reference class to this node
	Check(g *Grammar, refStack []string) (err error)

	// AddToFst adds this node to FST
	AddToFst(grammar *Grammar, fst *MutFst, startState int) (endState int)
}
