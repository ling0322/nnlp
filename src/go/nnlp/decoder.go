package nnlp

import (
	"fmt"
	"io"
	"log"
	"math"
	"sort"

	"github.com/ling0322/nnlp/src/go/nfst"
)

const (
	noValue = -1
)

// decoderToken is a node in decoding lattice
type decoderToken struct {
	state     int32
	output    int32
	cost      float32
	prevToken *decoderToken
	capture   rune
}

// decoderBeam is one frame of beam in decoder, maps state to decoderToken
type decoderBeam map[int32]*decoderToken

// Decoder is the base FST-based decoder
type Decoder struct {
	fst       *nfst.Fst
	beam      decoderBeam
	beamAgent decoderBeam
	beamSize  int
	logger    *log.Logger
}

type inputSymbol struct {
	symbolID int
	symbol   string
}

func NewDecoder(fst *nfst.Fst, beamSize int) *Decoder {
	log.Default().SetOutput(io.Discard)
	return &Decoder{
		fst:       fst,
		beam:      decoderBeam{},
		beamSize:  beamSize,
		beamAgent: nil,
		logger:    log.Default(),
	}
}

// initializeBeam initializes the first frame of beam in decoder
func (d *Decoder) initializeBeam() {
	d.beam = decoderBeam{0: &decoderToken{
		state:     0,
		output:    nfst.EpsilonSymbol,
		cost:      0,
		prevToken: nil,
		capture:   noValue,
	}}
}

// pruneBeam prunes the beam to beamSize by cost of each token
func (d *Decoder) pruneBeam() {
	d.logger.Printf("PruneBeam: beam_size=%d", len(d.beam))
	if len(d.beam) < d.beamSize {
		// do nothing if len(beam) less than beam size
		d.logger.Println("PruneBeam: skip")
		return
	}

	costs := make([]float64, 0, len(d.beam))
	for _, tok := range d.beam {
		costs = append(costs, float64(tok.cost))
	}

	// sort the weights to get the n-th element for pruning, n is beamSize
	sort.Float64s(costs)
	pruneCost := float32(costs[d.beamSize])

	// prune the beam to prunedBeam
	prunedBeam := decoderBeam{}
	for state, tok := range d.beam {
		if tok.cost <= pruneCost {
			prunedBeam[state] = tok
		}
	}
	d.beam = prunedBeam
	d.logger.Printf("PruneBeam: done, beam_size=%d", len(d.beam))
}

// processsEpsilonArc processes epsilon arc for one state and returns the states
// to queue
func (d *Decoder) processsStateEpsilonArcs(state int32) (nextStates []int32) {
	nextStates = []int32{}

	// find epsilon arcs for state
	base := d.fst.States[state].EpsilonBase
	if base < 0 {
		return
	}

	fromToken := d.beam[state]
	nEpsArcs := int32(len(d.fst.EpsilonArcs))
	for ; base < nEpsArcs; base++ {
		arcData := &d.fst.EpsilonArcs[base]
		if arcData.Check != state {
			break
		}

		// insert the token to beam
		token := &decoderToken{
			state:     arcData.TargetState,
			output:    arcData.OutputSymbol,
			cost:      fromToken.cost + arcData.Weight,
			prevToken: fromToken,
			capture:   noValue,
		}
		tgtToken, ok := d.beam[token.state]
		if ok && tgtToken.cost > token.cost {
			// there must be epsilon selfloops in the FST. We do not add this
			// state into queue again
			d.beam[token.state] = token
		}
		if !ok {
			d.beam[token.state] = token
			nextStates = append(nextStates, token.state)
		}
	}

	return
}

// processEpsilonArcs process the epsilon arcs in FST for tokens in beam
func (d *Decoder) processEpsilonArcs() {
	stateQueue := make([]int32, 0, len(d.beam)*2)
	for state := range d.beam {
		stateQueue = append(stateQueue, state)
	}

	// loop until no new states in queue
	for len(stateQueue) > 0 {
		// deque a state
		state := stateQueue[0]
		stateQueue = stateQueue[1:]

		// process the epsilon arcs for this state and enqueue the next states
		nextStates := d.processsStateEpsilonArcs(state)
		stateQueue = append(stateQueue, nextStates...)
	}
}

// processSymbolArcs process the non-epsilon symbol arcs in FST for tokens
// in beam
func (d *Decoder) processSymbolArcs(state int32, symbol int) {
	base := int(d.fst.States[state].Base)
	d.logger.Printf("ProcessSymbolArcs: beam=%d", base)

	if base == -1 {
		// no outgoing arcs in this state
		return
	}

	if symbol == noValue {
		// this is an unknown symbol
		return
	}

	arcIdx := base ^ symbol
	d.logger.Printf("ProcessSymbolArcs: arcIdx=%d", arcIdx)

	if int(arcIdx) >= len(d.fst.Arcs) {
		// this will not happed in current implementation of n-fst
		panic("out of boudnary")
	}

	arc := &d.fst.Arcs[arcIdx]
	if arc.Check != state {
		// arc is not for this state
		return
	}

	fromToken := d.beam[state]
	token := &decoderToken{
		state:     arc.TargetState,
		output:    arc.OutputSymbol,
		cost:      fromToken.cost + arc.Weight,
		prevToken: fromToken,
		capture:   noValue,
	}
	tgtToken, ok := d.beamAgent[token.state]
	if (ok && tgtToken.cost > token.cost) || !ok {
		d.beamAgent[token.state] = token
	}
}

// processRangeArcsForState process the range arcs in FST for tokens in beam
func (d *Decoder) processRangeArcs(state int32, symbol rune) {
	base := d.fst.States[state].RangeBase
	if base < 0 {
		return
	}

	nRangeArcs := int32(len(d.fst.RangeArcs))
	for ; base < nRangeArcs; base++ {
		arc := &d.fst.RangeArcs[base]
		if arc.Check != state {
			break
		}

		if symbol > arc.End || symbol < arc.Begin {
			// not match
			continue
		}

		// insert the token to beam
		fromToken := d.beam[state]
		token := &decoderToken{
			state:     arc.TargetState,
			output:    arc.OutputSymbol,
			cost:      fromToken.cost + arc.Weight,
			prevToken: fromToken,
			capture:   symbol,
		}
		tgtToken, ok := d.beamAgent[token.state]
		if (ok && tgtToken.cost > token.cost) || !ok {
			d.beamAgent[token.state] = token
		}
	}
}

// processArcs process the non-epsilon arcs in FST for tokens in beam
func (d *Decoder) processArcs(s inputSymbol) {
	d.logger.Printf("ProcessArcs: symbol='%s', symId=%d", s.symbol, s.symbolID)
	d.beamAgent = decoderBeam{}

	symbol := []rune(s.symbol)
	symbolID := s.symbolID

	for state := range d.beam {
		d.processSymbolArcs(state, symbolID)

		// only process range arcs for single character symbol
		if len(symbol) == 1 {
			d.processRangeArcs(state, symbol[0])
		}
	}

	d.beam = d.beamAgent
	d.beamAgent = nil
}

// addFinalWeights add final weights to the cost of tokens in beam. If final
// weights is INF, just delete this token
func (d *Decoder) addFinalWeights() {
	d.beamAgent = decoderBeam{}
	for state, token := range d.beam {
		finalWeight := d.fst.States[state].Final
		if math.IsInf(float64(finalWeight), 1) {
			continue
		}

		token.cost += finalWeight
		d.beamAgent[state] = token
	}

	d.beam = d.beamAgent
	d.beamAgent = nil
}

// getBestPath gets the best path from lattice, returns the non-epsilon symbols
// or captures in this path
func (d *Decoder) getBestPath() (symbols []string, err error) {
	// get best token
	var bestTok *decoderToken
	for _, tok := range d.beam {
		if bestTok == nil || bestTok.cost > tok.cost {
			bestTok = tok
		}
	}

	// get osymbols from best token
	token := bestTok
	symbolIds := []int32{}
	captured := []string{}
	for token != nil {
		if token.output != nfst.EpsilonSymbol {
			symbolIds = append([]int32{token.output}, symbolIds...)
		}
		if token.capture != noValue {
			captured = append([]string{string(token.capture)}, captured...)
		}
		token = token.prevToken
	}

	// from symbol-id to symbol it self
	symbols = []string{}
	for _, symbolId := range symbolIds {
		if symbolId == nfst.AlphaSymbol {
			if len(captured) == 0 {
				err = fmt.Errorf("capture symbols and range arcs mismatch")
				return
			}
			symbols = append(symbols, captured[0])
			captured = captured[1:]
		} else {
			symbols = append(symbols, d.fst.OutputSymbols[symbolId])
		}
	}

	return
}

// convertInput converts the input string to slice of decoderInput
func (d *Decoder) convertInput(input []string) []inputSymbol {
	inputs := []inputSymbol{}
	for _, sym := range input {
		inputSymbol := inputSymbol{symbol: sym}
		symbol, ok := d.fst.InputSymbols[sym]
		if ok {
			inputSymbol.symbolID = symbol
		} else {
			inputSymbol.symbolID = noValue
		}

		inputs = append(inputs, inputSymbol)
	}

	return inputs
}

// splitStringByRune splits the input string into list of sub-strings. each
// sub-string contains just one rune
func (d *Decoder) splitString(input string) (output []string) {
	output = []string{}
	for _, ch := range input {
		output = append(output, string(ch))
	}

	return
}

// debugPrintBeam prints beam information to logger
func (d *Decoder) debugPrintBeam() {
	d.logger.Println("-------------------- BEAM -----------------------")
	d.logger.Println("State     Cost      Capture     Output           ")
	d.logger.Println("-------------------------------------------------")
	for _, tok := range d.beam {
		d.logger.Printf(
			"%-9d %-9g %-11d %s", tok.state, tok.cost, tok.capture,
			d.fst.OutputSymbols[tok.output])
	}
	d.logger.Println("------------------ END BEAM ---------------------")
}

// DecodeSequence converts the input sequence to output sequence by beam serach
// in FST
func (d *Decoder) decodeInternal(input []string) (output []string, err error) {
	d.initializeBeam()

	inputs := d.convertInput(input)

	for i, inputSymbol := range inputs {
		d.logger.Printf("DecodeInternal: i=%d", i)

		d.pruneBeam()

		// process epsilon arcs for all tokens in beam
		d.processEpsilonArcs()

		// process non-epsilon arcs for all tokens in beam
		d.processArcs(inputSymbol)

		// early exit if no states in beam
		if len(d.beam) == 0 {
			err = fmt.Errorf("no active tokens in beam")
			return
		}

		d.debugPrintBeam()
	}

	// add final weights for each token in beam
	d.pruneBeam()
	d.processEpsilonArcs()
	d.addFinalWeights()
	if len(d.beam) == 0 {
		err = fmt.Errorf("no active tokens in beam")
		return
	}

	// get best path
	output, err = d.getBestPath()

	return
}

// DecodeString decodes characters from input string and return decoding result
func (d *Decoder) DecodeString(input string) (output []string, err error) {
	inputs := d.splitString(input)
	return d.decodeInternal(inputs)
}
