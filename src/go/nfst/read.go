package nfst

import (
	"encoding/binary"
	"fmt"
	"io"
)

// readArray reads an array of type T from reader
func readArray[T any](r io.Reader, n int) ([]T, error) {
	objects := make([]T, n)
	for i := 0; i < int(n); i++ {
		if err := binary.Read(r, binary.LittleEndian, &objects[i]); err != nil {
			return nil, err
		}
	}

	return objects, nil
}

// readArray reads an sparse array of type T from reader. Fill defaultVal if
// the value not exist
//lint:ignore U1000 For future use
func readSparseArray[T any](r io.Reader) (array []T, err error) {
	// read header
	header := struct {
		size       uint32
		nRecords   uint32
		defaultVal T
		mn0        uint16
	}{}
	if err = binary.Read(r, binary.LittleEndian, &header); err != nil {
		return
	}
	if header.mn0 != MagicNumber {
		err = fmt.Errorf("invalid sparse array")
		return
	}

	array = make([]T, header.size)
	for i := range array {
		array[i] = header.defaultVal
	}
	record := struct {
		index uint32
		value T
	}{}
	for i := 0; i < int(header.nRecords); i++ {
		if err := binary.Read(r, binary.LittleEndian, &record); err != nil {
			return nil, err
		}
		array[record.index] = record.value
	}

	// check magic numbers again
	var mn1 uint16
	if err = binary.Read(r, binary.LittleEndian, &mn1); err != nil {
		return
	}
	if mn1 != MagicNumber {
		err = fmt.Errorf("invalid sparse array")
		return
	}

	return
}

// readSymbols reads n symbols from file, the symbol binary format is
//   len uint8
//   data [len+1]byte  <- zero-terminated string
func readSymbols(r io.Reader, n int) (symbols []string, err error) {
	symbols = []string{}
	for i := 0; i < n; i++ {
		// read length
		var len uint8
		if err = binary.Read(r, binary.LittleEndian, &len); err != nil {
			return
		}

		// read string
		bytes := make([]byte, len+1)
		if err = binary.Read(r, binary.LittleEndian, &bytes); err != nil {
			return
		}
		if bytes[len] != 0 {
			err = fmt.Errorf("invalid symbol table (zero-terminated string expected)")
			return
		}

		symbol := string(bytes[:len])
		symbols = append(symbols, symbol)
	}

	return
}

// readInputSymbols reads the input symbol table and returns symbol to symbolID
// mapping (excepts the <eps> symbol).
func readInputSymbols(r io.Reader, n int) (map[string]int, error) {
	symbols, err := readSymbols(r, n)
	if err != nil {
		return nil, err
	}

	inputSymbols := map[string]int{}
	for id, symbol := range symbols {
		inputSymbols[symbol] = id
	}

	return inputSymbols, nil
}

// readStates reads the state-based data from reader
func (fst *Fst) readStates(r io.Reader) (err error) {
	// read base
	nStates := int(fst.Header.NumStates)
	fst.States, err = readArray[State](r, nStates)
	if err != nil {
		return err
	}

	return
}

// readBases reads the base arrays
func (fst *Fst) readArcs(r io.Reader) (err error) {
	// read non-epsilon arcs
	nArcs := int(fst.Header.NumArcs)
	if fst.Arcs, err = readArray[Arc](r, nArcs); err != nil {
		return
	}

	// read epsilon arcs
	nEpsilonArcs := int(fst.Header.NumEpsilonArcs)
	if fst.EpsilonArcs, err = readArray[Arc](r, nEpsilonArcs); err != nil {
		return
	}

	// read range arcs
	nRangeArcs := int(fst.Header.NumRangeArcs)
	if fst.RangeArcs, err = readArray[RangeArc](r, nRangeArcs); err != nil {
		return
	}

	return
}

// Read read n-fst from file
func Read(r io.Reader) (fst *Fst, err error) {
	header := Header{}
	if err = binary.Read(r, binary.LittleEndian, &header); err != nil {
		return
	}

	// check header-name
	if string(header.Name[:]) != HeaderText {
		err = fmt.Errorf("invalid fst header")
		return
	}

	// check version
	if header.Version != 1 {
		err = fmt.Errorf("unsupported version")
		return
	}

	fst = &Fst{Header: &header}

	// read state-based data
	if err = fst.readStates(r); err != nil {
		return
	}

	// read arcs
	if err = fst.readArcs(r); err != nil {
		return
	}

	// read input symbols
	nInputSymbols := int(header.NumInputSymbols)
	if fst.InputSymbols, err = readInputSymbols(r, nInputSymbols); err != nil {
		return
	}

	// read output symbols
	nOutputSymbols := int(header.NumOutputSymbols)
	if fst.OutputSymbols, err = readSymbols(r, nOutputSymbols); err != nil {
		return
	}

	return
}
