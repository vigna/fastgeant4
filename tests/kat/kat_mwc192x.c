/* Reference MWC192X outputs, from https://github.com/vigna/MWCPRNG/blob/main/prngs/MWC192X.c. */
#include <stdio.h>
#include <inttypes.h>
#include "MWC192X.c"
void kat_mwc192x(void) {
	x = 1; y = 2; c = 3;
	printf("mwc192x:");
	for (int i = 0; i < 8; i++) printf(" 0x%016" PRIx64 "ULL", next());
	printf("\n");
}

/* Reference outputs for jump seeding of MWC192X: from the fixed base state
   (x, y and the carry from three SplitMix64 outputs from 0, the carry as
   recommended above), jump by s * 2^96 with jump_ce(s, 96), print 4 outputs. */
static uint64_t splitmix64(uint64_t *x) {
	uint64_t z = (*x += 0x9e3779b97f4a7c15ULL);
	z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
	z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
	return z ^ (z >> 31);
}

void kat_jump_mwc192x(const uint64_t *seeds, int n) {
	for (int k = 0; k < n; k++) {
		uint64_t sm = 0;
		x = splitmix64(&sm);
		y = splitmix64(&sm);
		c = 1 + (uint64_t)(((__uint128_t)splitmix64(&sm) * (MWC_A2 - 2)) >> 64);
		if (seeds[k] != 0) jump_ce(seeds[k], 96);
		printf("mwc192x-jump 0x%016" PRIx64 ":", seeds[k]);
		for (int i = 0; i < 4; i++) printf(" 0x%016" PRIx64 "ULL", next());
		printf("\n");
	}
}
