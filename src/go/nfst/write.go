package nfst

import (
	"encoding/binary"
	"fmt"
	"io"
)

// write writes data to stream using binary.Write if err != nil. Otherwise,
// return the err directly
func (b *Fst) write(w io.Writer, data any, err error) error {
	if err != nil {
		return err
	}
	if err = binary.Write(w, binary.LittleEndian, data); err != nil {
		return err
	}
	return nil
}

// writeOneSymbol write one symbol to stream
func (b *Fst) writeOneSymbol(w io.Writer, symbol string) (err error) {
	if len(symbol) > 255 {
		// it should be checked before
		err = fmt.Errorf("symbol too long: %s", symbol)
		return
	}
	symbolLen := uint8(len(symbol))
	if err = binary.Write(w, binary.LittleEndian, symbolLen); err != nil {
		return
	}
	if _, err = w.Write([]byte(symbol)); err != nil {
		return
	}
	if _, err = w.Write([]byte{0}); err != nil {
		return
	}

	return
}

// convertToList converts a [symbol]symbol-id map to list
func (b *Fst) convertToList(symbolIds map[string]int) (symbols []string) {
	maxId := 0
	for _, symbolId := range symbolIds {
		if symbolId > maxId {
			maxId = symbolId
		}
	}

	symbols = make([]string, maxId+1)
	for i := range symbols {
		symbols[i] = "<eps>"
	}
	for symbol, symbolId := range symbolIds {
		symbols[symbolId] = symbol
	}

	return
}

// write writes data to stream using binary.Write if err != nil. Otherwise,
// return the err directly
func (b *Fst) writeSymbols(w io.Writer, symbols []string, err error) error {
	if err != nil {
		return err
	}

	for _, symbol := range symbols {
		if err = b.writeOneSymbol(w, symbol); err != nil {
			return err
		}
	}

	return nil
}

// Write saves the nfst to stream
func (b *Fst) Write(w io.Writer) (err error) {
	// write header
	var headerBytes [8]byte
	copy(headerBytes[:], []byte(HeaderText))
	header := Header{
		Name:             headerBytes,
		Version:          1,
		NumStates:        int32(len(b.States)),
		NumArcs:          int32(len(b.Arcs)),
		NumEpsilonArcs:   int32(len(b.EpsilonArcs)),
		NumRangeArcs:     int32(len(b.RangeArcs)),
		NumOutputSymbols: int32(len(b.OutputSymbols)),
		NumInputSymbols:  int32(len(b.InputSymbols)),
	}
	err = b.write(w, header, err)
	err = b.write(w, b.States, err)
	err = b.write(w, b.Arcs, err)
	err = b.write(w, b.EpsilonArcs, err)
	err = b.write(w, b.RangeArcs, err)
	err = b.writeSymbols(w, b.convertToList(b.InputSymbols), err)
	err = b.writeSymbols(w, b.OutputSymbols, err)

	return
}
