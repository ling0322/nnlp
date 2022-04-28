#include "nfst_api.h"

#include <stdint.h>

extern int64_t _CreateMutableFst();
extern void _DestroyMutableFst(int64_t);

struct NFstApi nfst_api = {
  _CreateMutableFst,
  _DestroyMutableFst
};
