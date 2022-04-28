#include <stdint.h>

typedef int64_t NHANDLE;
typedef int64_t NRESULT;

#define N_OK 0
#define N_FAIL 0x80004005

struct NFstApi {
  NHANDLE (*CreateMutableFst)();
  void (*DestroyMutableFst)(NHANDLE);
};

extern struct NFstApi nfst_api;

