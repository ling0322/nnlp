package main

import (
	"errors"
	"log"
)

// Handle is the handle to object in golang
type Handle int64

// HandleTable maps Handle to pointer of objects
type HandleTable map[Handle]interface{}

// global instance handle table
var gHandleTable = HandleTable{}

// current hInstance ID, it will increase only
var gCurrentHInstance = Handle(1001)

// GetInstance gets instance of type *T by handle
func QueryTable[T any](h HandleTable, hInstance Handle) (T, error) {
	instance, ok := h[hInstance]
	if !ok {
		var defaultVal T
		return defaultVal, errors.New("hInstance not exist")
	}

	typedInst, ok := instance.(T)
	if !ok {
		var defaultVal T
		return defaultVal, errors.New("hInstance type mismatch")
	}

	return typedInst, nil
}

// Delete deletes the hInstance from table. Will do nothing if
// hInstance not exist
func (h HandleTable) Delete(hInstance Handle) {
	_, ok := h[hInstance]
	if ok {
		delete(h, hInstance)
	}
}

// Add adds an object to handle table, then returns the handle to it
func (h HandleTable) Add(instance interface{}) (hInstance Handle) {
	if instance == nil {
		log.Fatal("AddInstance: nil instance")
	}

	hInstance = gCurrentHInstance
	h[hInstance] = instance
	gCurrentHInstance++

	return
}
