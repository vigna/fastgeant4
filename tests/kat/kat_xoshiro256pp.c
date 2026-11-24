/* Reference xoshiro256++ outputs, from https://github.com/vigna/prng-speed/blob/main/cpu/xoshiro/xoshiro256++-speed.c
   (compiled with -DA=17 -DB=45 -DR=23, as in prng-speed's gens.tsv). */
#include <inttypes.h>
#define main xoshiro_harness_main
#define get_user_time xoshiro_get_user_time
#include "xoshiro/xoshiro256++-speed.c"
void kat_xoshiro256pp(void) {
	s[0] = 1; s[1] = 2; s[2] = 3; s[3] = 4;
	printf("xoshiro256pp:");
	for (int i = 0; i < 8; i++) printf(" 0x%016" PRIx64 "ULL", next());
	printf("\n");
}
