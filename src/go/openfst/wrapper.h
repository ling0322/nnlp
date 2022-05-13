#ifndef CHECK_H_
#define CHECK_H_

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

struct FSTARC {
  int64_t tgt_state;
  int64_t ilabel;
  int64_t olabel;
  float weight;
};

void *nf_stdvectorfst_new();
void nf_stdvectorfst_delete(void *fst);
void nf_stdvectorfst_set_start(void *fst, int64_t state);
int64_t nf_stdvectorfst_add_state(void *fst);
void nf_stdvectorfst_add_arc(void *fst, int64_t state, struct FSTARC arc);
float nf_stdvectorfst_final(void *fst, int64_t state);
void nf_stdvectorfst_set_final(void *fst, int64_t state, float weight);
int64_t nf_stdvectorfst_num_states(void *fst);

void *nf_arciterator_new(void *fst, int64_t state);
void nf_arciterator_delete(void *it);
int64_t nf_arciterator_done(void *it);
void nf_arciterator_next(void *it);
void nf_arciterator_value(void *it, struct FSTARC *arc);

#ifdef __cplusplus
}
#endif

#endif
