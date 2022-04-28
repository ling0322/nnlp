package nregex

import (
	"bufio"
	"strings"
)

// A scanner with filename and line number informatoion
type grammarReader struct {
	filename string
	line     int

	scannar *bufio.Scanner
}

// newStringScanner creates a scanner from string
func newStringScanner(text string) *grammarReader {
	reader := strings.NewReader(text)
	return &grammarReader{
		filename: "<inline-string>",
		line:     0,
		scannar:  bufio.NewScanner(reader),
	}
}

// The same as scanner.Scan
func (f *grammarReader) Scan() bool {
	f.line++
	return f.scannar.Scan()
}

// The same as scanner.Text
func (f *grammarReader) Text() string {
	return f.scannar.Text()
}

// Line returns the current line number
func (f *grammarReader) Line() int {
	return f.line
}

// Line returns the current filename
func (f *grammarReader) Filename() string {
	return f.filename
}

// The same as scanner.Err
func (f *grammarReader) Err() error {
	return f.scannar.Err()
}

// close the reader
func (f *grammarReader) Close() {
}
