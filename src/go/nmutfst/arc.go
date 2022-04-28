package nmutfst

// Arc in FST
type Arc struct {
	NextState    int
	InputSymbol  Symbol
	OutputSymbol Symbol
	Weight       float32
}
