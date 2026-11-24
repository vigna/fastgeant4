// Reference outputs for jump seeding of xoshiro256++: from the fixed base
// state (four SplitMix64 outputs from 0), jump by s * 2^128 with boost-random's
// xoshiro256pp::jump(s, 128) (Boost.Random, https://github.com/boostorg/random), then print 4 outputs.
#include <boost/random/xoshiro.hpp>

#include <cinttypes>
#include <cstdint>
#include <cstdio>

static uint64_t splitmix64(uint64_t &x) {
  uint64_t z = (x += 0x9e3779b97f4a7c15ULL);
  z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
  z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
  return z ^ (z >> 31);
}

extern "C" void kat_jump_xoshiro256pp(const uint64_t *seeds, int n) {
  for (int k = 0; k < n; k++) {
    uint64_t x = 0, base[4];
    for (uint64_t &w : base) w = splitmix64(x);
    boost::random::xoshiro256pp g;
    g.seed(base, base + 4);
    g.jump(seeds[k], 128);
    std::printf("xoshiro256pp-jump 0x%016" PRIx64 ":", seeds[k]);
    for (int i = 0; i < 4; i++) std::printf(" 0x%016" PRIx64 "ULL", (uint64_t)g());
    std::printf("\n");
  }
}
