/* Prints the first 8 raw outputs of each reference generator from a fixed state,
   and the outputs after jump seeding. Build: see tests/kat/gen_kat.sh. */
#include <stdint.h>
void kat_xoshiro256pp(void);
void kat_mwc192x(void);
void kat_jump_xoshiro256pp(const uint64_t *seeds, int n);
void kat_jump_mwc192x(const uint64_t *seeds, int n);
static const uint64_t jump_seeds[] = {
	0, 1, 2, 3, 0x80000000ULL, 0x100000000ULL, 0x100000001ULL, 99999999ULL,
	0x05f5e0ff05f5e0ffULL, 0x5bd1e9955bd1e995ULL, 0xffffffffffffffffULL };
int main(void) {
	kat_xoshiro256pp(); kat_mwc192x();
	const int n = sizeof jump_seeds / sizeof *jump_seeds;
	kat_jump_xoshiro256pp(jump_seeds, n);
	kat_jump_mwc192x(jump_seeds, n);
	return 0;
}
