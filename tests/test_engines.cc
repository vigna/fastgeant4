// Tests for the new CLHEP engines (xoshiro256++, MWC192X).
// Known answers come from tests/kat/gen_kat.sh (the user's reference C code).

#include "CLHEP/Random/G4RngEngines.h"

#include <cassert>
#include <cstdint>
#include <cstdio>
#include <sstream>
#include <vector>

using namespace CLHEP;

#define CHECK(cond)                                                            \
  do {                                                                         \
    if (!(cond)) {                                                             \
      std::fprintf(stderr, "%s:%d: CHECK failed: %s\n", __FILE__, __LINE__,    \
                   #cond);                                                     \
      std::abort();                                                            \
    }                                                                          \
  } while (0)

template <class Gen>
static void check_kat(Gen &g, const uint64_t (&expected)[8]) {
  for (int i = 0; i < 8; i++) CHECK(g.next() == expected[i]);
}

static void test_kat_xoshiro256pp() {
  static const uint64_t e[8] = {
      0x0000000002800001ULL, 0x0000000003800067ULL, 0x000cc00003800067ULL,
      0x000cc201994400b2ULL, 0x8012a2019ac433cdULL, 0x8a69978acdee33baULL,
      0xc271134733154abdULL, 0xac2ba09179169e97ULL};
  Xoshiro256ppEngine eng;
  Xoshiro256ppGen &g = eng.generator();
  g.s[0] = 1; g.s[1] = 2; g.s[2] = 3; g.s[3] = 4;
  check_kat(g, e);
}

static void test_kat_mwc192x() {
  static const uint64_t e[8] = {
      0x0000000000000001ULL, 0xff4e24dd418f5436ULL, 0xfe9c49ba831ea867ULL,
      0x8672faed93e70801ULL, 0x094f02d02df8e258ULL, 0xff3e8a4b44b688faULL,
      0x46f742ef8c2ef445ULL, 0x82aac36383dd5649ULL};
  Mwc192xEngine eng;
  Mwc192xGen &g = eng.generator();
  g.s[0] = 1; g.s[1] = 2; g.s[2] = 3;  // x, y, c
  check_kat(g, e);
}

template <class E> static void check_flat_range() {
  E eng;
  for (long i = 0; i < 10000000; i++) {
    const double u = eng.flat();
    CHECK(u > 0.0 && u <= 1.0);
  }
}

static void test_to_double_bounds() {
  CHECK(g4rngToDouble(0) == 0x1.0p-53);
  CHECK(g4rngToDouble(~UINT64_C(0)) == 1.0);
  CHECK(g4rngToDouble(UINT64_C(1) << 63) == 0.5 + 0x1.0p-53);
  check_flat_range<Xoshiro256ppEngine>();
  check_flat_range<Mwc192xEngine>();
}

template <class E> static void check_seed_determinism() {
  const long s1[2] = {12345, 67890}, s2[2] = {12345, 67891};
  E a, b, c;
  a.setSeeds(s1, -1);
  b.setSeeds(s1, -1);
  c.setSeeds(s2, -1);
  bool differ = false;
  for (int i = 0; i < 100; i++) {
    const double x = a.flat(), y = b.flat(), z = c.flat();
    CHECK(x == y);
    if (x != z) differ = true;
  }
  CHECK(differ);
  // Explicit counts and setSeed agree with the documented combination.
  E d, f;
  d.setSeeds(s1, 2);
  f.setSeeds(s1, -1);
  CHECK(d.flat() == f.flat());
  E g, h;
  const long one[1] = {42};
  g.setSeed(42, 0);
  h.setSeeds(one, 1);
  CHECK(g.flat() == h.flat());
}

static void test_seed_determinism() {
  check_seed_determinism<Xoshiro256ppEngine>();
  check_seed_determinism<Mwc192xEngine>();
}

static void test_mwc_carry() {
  Mwc192xEngine eng;
  for (long i = 0; i < 10000; i++) {
    const long seeds[2] = {i * 7919, i ^ 0x5bd1e995};
    eng.setSeeds(seeds, -1);
    const uint64_t c = eng.generator().s[2];
    CHECK(c >= 1 && c <= Mwc192xGen::MWC_A2 - 2);
  }
}

template <class E> static void check_put_get() {
  E eng;
  const long seeds[2] = {3, 4};
  eng.setSeeds(seeds, -1);
  for (int i = 0; i < 37; i++) eng.flat();

  // Stream form.
  std::ostringstream os;
  eng.put(os);
  double first[10];
  for (double &x : first) x = eng.flat();
  std::istringstream is(os.str());
  eng.get(is);
  CHECK(!is.fail());
  for (double x : first) CHECK(eng.flat() == x);

  // Vector form.
  const std::vector<unsigned long> v = eng.put();
  for (double &x : first) x = eng.flat();
  CHECK(eng.get(v));
  for (double x : first) CHECK(eng.flat() == x);

  // A vector from another engine type is refused.
  std::vector<unsigned long> bad = v;
  bad[0] ^= 1;
  CHECK(!eng.get(bad));

  // File form.
  const char *file = "test_engines.status";
  eng.saveStatus(file);
  for (double &x : first) x = eng.flat();
  eng.restoreStatus(file);
  for (double x : first) CHECK(eng.flat() == x);
  std::remove(file);
}

static void test_put_get_roundtrip() {
  check_put_get<Xoshiro256ppEngine>();
  check_put_get<Mwc192xEngine>();
}

// Jump seeding (as MixMaxRng): a fixed base state moved by s * 2^128
// (xoshiro256++) or s * 2^96 (MWC192X) steps; references from boost-random's
// jump(s, 128) and MWC192X.c's jump_ce(s, 96).
#include "kat/jump_kat.inc"

template <class E, size_t N>
static void check_jump_kat(const uint64_t (&kat)[N][5]) {
  for (size_t k = 0; k < N; k++) {
    E eng;
    eng.generator().seedJump(kat[k][0]);
    for (int i = 0; i < 4; i++) CHECK(eng.generator().next() == kat[k][1 + i]);
  }
}

static void test_jump_seeding_kat() {
  check_jump_kat<Xoshiro256ppEngine>(kJumpKat_xoshiro256pp);
  check_jump_kat<Mwc192xEngine>(kJumpKat_mwc192x);
}

template <class E> static void check_setseeds_jumps() {
  const long seeds[2] = {99999999, 12345678};
  const uint64_t s = (uint64_t)(uint32_t)seeds[0] | (uint64_t)(uint32_t)seeds[1] << 32;
  E a, b, c, d;
  a.setSeeds(seeds, -1);
  b.generator().seedJump(s);
  for (int i = 0; i < 16; i++) CHECK(a.generator().next() == b.generator().next());
  c.setSeed(42, 0);
  d.generator().seedJump(42);
  for (int i = 0; i < 16; i++) CHECK(c.generator().next() == d.generator().next());
}

static void test_setseeds_jumps() {
  check_setseeds_jumps<Xoshiro256ppEngine>();
  check_setseeds_jumps<Mwc192xEngine>();
}

static void test_names() {
  CHECK(Xoshiro256ppEngine().name() == "Xoshiro256ppEngine");
  CHECK(Mwc192xEngine().name() == "Mwc192xEngine");
}

int main() {
  test_kat_xoshiro256pp();
  test_kat_mwc192x();
  test_to_double_bounds();
  test_seed_determinism();
  test_mwc_carry();
  test_put_get_roundtrip();
  test_jump_seeding_kat();
  test_setseeds_jumps();
  test_names();
  std::printf("ALL ENGINE TESTS PASSED\n");
  return 0;
}
