package main

// #include "nfst_api.h"
import "C"
import (
	"fmt"
	"os"

	"github.com/ling0322/nnlp/src/go/nmutfst"
)

//export _CreateMutableFst
func _CreateMutableFst() C.NHANDLE {
	mutableFst := nmutfst.NewMutableFst()
	hInstance := gHandleTable.Add(mutableFst)
	return C.NHANDLE(hInstance)
}

//export _DestroyMutableFst
func _DestroyMutableFst(h C.NHANDLE) {
	hInstance := Handle(h)
	_, err := QueryTable[nmutfst.MutableFst](gHandleTable, hInstance)
	if err != nil {
		fmt.Fprintf(os.Stderr, "WARNING: _DestroyMutableFst: %s\n", err)
		return
	}

	gHandleTable.Delete(hInstance)
}

//export _MutableFstAddState
func _MutableFstAddState(hFst C.NHANDLE, pState *C.int64_t) C.NRESULT {
	hInstance := Handle(hFst)
	instance, err := QueryTable[nmutfst.MutableFst](gHandleTable, hInstance)
	if err != nil {
		return C.N_FAIL
	}

	state := instance.AddState()
	*pState = C.int64_t(state)

	return C.N_OK
}

//export NFstGetApi
func NFstGetApi(apiVersion C.int64_t) *C.struct_NFstApi {
	return &C.nfst_api
}

func main() {}
