from libcpp.memory cimport unique_ptr
from libcpp.cast cimport reinterpret_cast

from pywrapfst cimport MutableFst
from pywrapfst cimport MutableFstClass_ptr
from cpywrapfst cimport MutableFstClass

cdef extern from "fstrmepslocal.h" namespace "nnlp::fstext" nogil:
  cdef MutableFstClass *RemoveEpsLocal(MutableFstClass *)

cpdef MutableFst RemoveEpsilonLocal(MutableFst fst):
  fst_ptr = fst._fst.get()
  fst_ptr = RemoveEpsLocal(reinterpret_cast[MutableFstClass_ptr](fst_ptr))
  if fst_ptr == NULL:
    raise Exception('RemoveEpsilonLocal failed')
