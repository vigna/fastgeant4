// -*- C++ -*-
//
// xoshiro256++ and MWC192X as CLHEP random engines.
//
// The next-state functions are those of the reference implementations:
// xoshiro256++ by D. Blackman and S. Vigna, MWC192X 1.0 by
// S. Vigna (https://github.com/vigna/MWCPRNG/blob/main/prngs/MWC192X.c).
//
// flat() returns ((x >> 11) + 1) * 2^-53, which lies in (0, 1], as the
// values returned by MixMaxRng::flat(): Geant4 takes logarithms of flat().
//
// Seeding: setSeeds() uses the first two seeds when its count is < 1 (as
// MixMaxRng does, and as Geant4 calls it), the first `count` seeds
// otherwise; each seed is reduced to 32 bits, as MixMaxRng does.
//
// xoshiro256++ and MWC192X are seeded as MixMaxRng is (setSeeds ->
// seed_uniquestream -> apply_bigskip): from a fixed base state, the
// generator jumps by s * 2^128 (xoshiro256++) or s * 2^96 (MWC192X) steps,
// where s = seed0 + seed1 * 2^32 (further seeds are ignored), so distinct
// seeds give non-overlapping streams of 2^128 (2^96) numbers. The jumps use
// the tables of G4RngJumpTables.icc (scripts/gen_jump_tables.py), one entry
// per bit of s. The base state is the SplitMix64 output from 0 (for MWC192X,
// with the carry drawn as MWC192X.c recommends).

#ifndef G4RngEngines_h
#define G4RngEngines_h 1

#include "CLHEP/Random/RandomEngine.h"

#include <cstdint>
#include <iosfwd>
#include <string>
#include <vector>

namespace CLHEP {

// One step of SplitMix64: advances x and returns the next output.
inline std::uint64_t g4rngSplitMix64(std::uint64_t &x) {
  std::uint64_t z = (x += 0x9e3779b97f4a7c15ULL);
  z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
  z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
  return z ^ (z >> 31);
}

// Maps 64 random bits to a double in (0, 1], never 0.
inline double g4rngToDouble(std::uint64_t x) {
  return double((x >> 11) + 1) * 0x1.0p-53;
}

struct Xoshiro256ppGen {
  static constexpr int WORDS = 4;
  std::uint64_t s[WORDS];
  static const char *label() { return "Xoshiro256ppEngine"; }

  static inline std::uint64_t rotl(const std::uint64_t x, int k) {
    return (x << k) | (x >> (64 - k));
  }

  inline std::uint64_t next() {
    const std::uint64_t result = rotl(s[0] + s[3], 23) + s[0];
    const std::uint64_t t = s[1] << 17;
    s[2] ^= s[0];
    s[3] ^= s[1];
    s[1] ^= s[2];
    s[0] ^= s[3];
    s[2] ^= t;
    s[3] = rotl(s[3], 45);
    return result;
  }

  // The base state moved by d * 2^128 steps.
  void seedJump(std::uint64_t d);
};

struct Mwc192xGen {
  static constexpr int WORDS = 3;
  static constexpr std::uint64_t MWC_A2 = 0xff4e24dd418f5433ULL;
  std::uint64_t s[WORDS];  // x, y, c
  static const char *label() { return "Mwc192xEngine"; }

  inline std::uint64_t next() {
    std::uint64_t y = s[1];
    const std::uint64_t c = s[2];
    const unsigned __int128 t = MWC_A2 * (unsigned __int128)s[0] + c;
    // An empty asm makes y opaque: otherwise GCC's SLP vectorizer (enabled by
    // Geant4's -O3 -ftree-vectorize) packs the stores of y and of the low half
    // of t into one 16-byte store, which the 8-byte loads of the next call
    // cannot forward from (3.7 instead of 1.3 ns per call). No instruction.
    __asm__("" : "+r"(y));
    s[0] = y;
    s[1] = (std::uint64_t)t;
    s[2] = (std::uint64_t)(t >> 64);
    return y ^ c;
  }

  // The base state moved by d * 2^96 steps.
  void seedJump(std::uint64_t d);
};

template <class Gen> class GenEngine final : public HepRandomEngine {
public:
  GenEngine();
  explicit GenEngine(long seed);
  ~GenEngine() override = default;

  double flat() override { return g4rngToDouble(gen.next()); }
  void flatArray(const int size, double *vect) override;

  void setSeed(long seed, int dum = 0) override;
  void setSeeds(const long *seeds, int count = 0) override;

  void saveStatus(const char filename[] = "Config.conf") const override;
  void restoreStatus(const char filename[] = "Config.conf") override;
  void showStatus() const override;

  std::string name() const override { return engineName(); }
  static std::string engineName() { return Gen::label(); }
  static std::string beginTag() { return engineName() + "-begin"; }

  std::ostream &put(std::ostream &os) const override;
  std::istream &get(std::istream &is) override;
  std::istream &getState(std::istream &is) override;
  std::vector<unsigned long> put() const override;
  bool get(const std::vector<unsigned long> &v) override;
  bool getState(const std::vector<unsigned long> &v) override;

  operator double() override { return flat(); }
  operator float() override { return float(flat()); }
  operator unsigned int() override { return (unsigned int)(gen.next() >> 32); }

  // The underlying generator (for tests and the fast path).
  Gen &generator() { return gen; }

private:
  void seedFrom(const long *seeds, int count);
  Gen gen;
};

using Xoshiro256ppEngine = GenEngine<Xoshiro256ppGen>;
using Mwc192xEngine = GenEngine<Mwc192xGen>;

extern template class GenEngine<Xoshiro256ppGen>;
extern template class GenEngine<Mwc192xGen>;

}  // namespace CLHEP

#endif
