#ifndef CHECK_H_
#define CHECK_H_

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

struct NFSTARC {
  int64_t tgt_state;
  int64_t ilabel;
  int64_t olabel;
  float weight;
};

void *_c_mutable_fst_new();
void _c_mutable_fst_delete(void *fst);
void _c_mutable_fst_set_start(void *fst_ptr, int64_t state);
int64_t _c_mutable_fst_add_state(void *fst_ptr);
void _c_mutable_fst_add_arc(void *fst_ptr, int64_t state, struct NFSTARC arc);
float _c_mutable_fst_final(void *fst_ptr, int64_t state);
void _c_mutable_fst_set_final(void *fst_ptr, int64_t state, float weight);
int64_t _c_mutable_fst_num_states(void *fst_ptr);

void *_c_arc_iterator_new(void *fst_ptr, int64_t state);
void _c_arc_iterator_delete(void *arc_iter_ptr);
int64_t _c_arc_iterator_done(void *arc_iter_ptr);
void _c_arc_iterator_next(void *arc_iter_ptr);
void _c_arc_iterator_value(void *arc_iter_ptr, struct NFSTARC *arc);

#ifdef __cplusplus
}
#endif

#endif
