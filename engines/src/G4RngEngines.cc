// -*- C++ -*-
//
// Out-of-line members of the GenEngine template (see G4RngEngines.h).

#include "CLHEP/Random/G4RngEngines.h"
#include "CLHEP/Random/engineIDulong.h"

#include <fstream>
#include <iostream>

namespace CLHEP {

namespace {

constexpr long kDefaultSeed = 0x5eed;

#include "CLHEP/Random/G4RngJumpTables.icc"

using u128 = unsigned __int128;

// r = a * b * 2^-192 mod m, m = MWC_A2 * 2^128 - 1, for a, b < m
// (Montgomery multiplication with R = 2^192). Since m = -1 mod 2^64, the
// Montgomery multiplier -m^-1 mod 2^64 is 1: each reduction step takes
// q = t[i], which clears limb i (t[i] - q), and adds q * MWC_A2 at limb i + 2.
void mwcMontMul(std::uint64_t r[3], const std::uint64_t a[3], const std::uint64_t b[3]) {
  constexpr std::uint64_t A2 = Mwc192xGen::MWC_A2;
  std::uint64_t t[7] = {0, 0, 0, 0, 0, 0, 0};
  for (int i = 0; i < 3; i++) {
    std::uint64_t carry = 0;
    for (int j = 0; j < 3; j++) {
      const u128 p = (u128)a[i] * b[j] + t[i + j] + carry;
      t[i + j] = (std::uint64_t)p;
      carry = (std::uint64_t)(p >> 64);
    }
    t[i + 3] = carry;
  }
  for (int i = 0; i < 3; i++) {
    const u128 p = (u128)t[i] * A2;
    t[i] = 0;
    u128 sum = (u128)t[i + 2] + (std::uint64_t)p;
    t[i + 2] = (std::uint64_t)sum;
    sum = (u128)t[i + 3] + (std::uint64_t)(p >> 64) + (std::uint64_t)(sum >> 64);
    t[i + 3] = (std::uint64_t)sum;
    std::uint64_t c = (std::uint64_t)(sum >> 64);
    for (int k = i + 4; c != 0 && k < 7; k++) {
      sum = (u128)t[k] + c;
      t[k] = (std::uint64_t)sum;
      c = (std::uint64_t)(sum >> 64);
    }
  }
  // The result t[3..6] is < 2m: subtract m (add 2^192 - m = (2^64 - A2) 2^128 + 1) if >= m.
  const bool ge = t[6] != 0 || t[5] > A2 - 1 ||
                  (t[5] == A2 - 1 && t[4] == ~UINT64_C(0) && t[3] == ~UINT64_C(0));
  if (ge) {
    u128 sum = (u128)t[3] + 1;
    t[3] = (std::uint64_t)sum;
    sum = (u128)t[4] + (std::uint64_t)(sum >> 64);
    t[4] = (std::uint64_t)sum;
    t[5] = t[5] + (std::uint64_t)(sum >> 64) + (0 - A2);
  }
  r[0] = t[3];
  r[1] = t[4];
  r[2] = t[5];
}

}  // namespace

void Xoshiro256ppGen::seedJump(std::uint64_t d) {
  std::uint64_t x = 0;
  std::uint64_t s0 = g4rngSplitMix64(x), s1 = g4rngSplitMix64(x);
  std::uint64_t s2 = g4rngSplitMix64(x), s3 = g4rngSplitMix64(x);
  for (int i = 0; i < 64; i++) {
    if (((d >> i) & 1) == 0) continue;
    // Apply the jump polynomial with the accumulate-and-step loop of jump(),
    // branchless (the coefficients are random bits) and in registers.
    std::uint64_t t0 = 0, t1 = 0, t2 = 0, t3 = 0;
    for (int w = 0; w < 4; w++) {
      std::uint64_t p = kXoshiro256Jump[i][w];
      for (int b = 0; b < 64; b++) {
        const std::uint64_t m = 0 - (p & 1);
        p >>= 1;
        t0 ^= s0 & m;
        t1 ^= s1 & m;
        t2 ^= s2 & m;
        t3 ^= s3 & m;
        const std::uint64_t t = s1 << 17;
        s2 ^= s0;
        s3 ^= s1;
        s1 ^= s2;
        s0 ^= s3;
        s2 ^= t;
        s3 = rotl(s3, 45);
      }
    }
    s0 = t0;
    s1 = t1;
    s2 = t2;
    s3 = t3;
  }
  s[0] = s0;
  s[1] = s1;
  s[2] = s2;
  s[3] = s3;
}

void Mwc192xGen::seedJump(std::uint64_t d) {
  std::uint64_t x = 0;
  s[0] = g4rngSplitMix64(x);
  s[1] = g4rngSplitMix64(x);
  s[2] = 1 + (std::uint64_t)(((u128)g4rngSplitMix64(x) * (MWC_A2 - 2)) >> 64);
  // The state x + y b + c b^2 is multiplied by A^(2^(96+i)) mod m for each set bit i.
  for (int i = 0; i < 64; i++)
    if ((d >> i) & 1) mwcMontMul(s, s, kMwc192xJumpMont[i]);
}

// ---- GenEngine ----

template <class Gen> GenEngine<Gen>::GenEngine() : HepRandomEngine() {
  setSeed(kDefaultSeed, 0);
}

template <class Gen> GenEngine<Gen>::GenEngine(long seed) : HepRandomEngine() {
  setSeed(seed, 0);
}

template <class Gen> void GenEngine<Gen>::flatArray(const int size, double *vect) {
  for (int i = 0; i < size; ++i) vect[i] = flat();
}

template <class Gen> void GenEngine<Gen>::seedFrom(const long *seeds, int count) {
  std::uint64_t d = (std::uint32_t)seeds[0];
  if (count > 1) d |= (std::uint64_t)(std::uint32_t)seeds[1] << 32;
  gen.seedJump(d);
}

template <class Gen> void GenEngine<Gen>::setSeed(long seed, int) {
  theSeed = seed;
  const long one[1] = {seed};
  seedFrom(one, 1);
}

template <class Gen> void GenEngine<Gen>::setSeeds(const long *seeds, int count) {
  theSeed = seeds[0];
  theSeeds = seeds;
  seedFrom(seeds, count < 1 ? 2 : count);
}

template <class Gen> std::ostream &GenEngine<Gen>::put(std::ostream &os) const {
  os << beginTag() << "\n";
  for (int i = 0; i < Gen::WORDS; ++i) os << gen.s[i] << (i + 1 < Gen::WORDS ? " " : "\n");
  os << engineName() << "-end\n";
  return os;
}

template <class Gen> std::istream &GenEngine<Gen>::get(std::istream &is) {
  std::string tag;
  is >> tag;
  if (tag != beginTag()) {
    is.clear(std::ios::badbit | is.rdstate());
    std::cerr << "Input stream mispositioned or bad in reading " << engineName()
              << " state: expected " << beginTag() << ", found " << tag << "\n";
    return is;
  }
  return getState(is);
}

template <class Gen> std::istream &GenEngine<Gen>::getState(std::istream &is) {
  std::uint64_t w[Gen::WORDS];
  for (std::uint64_t &x : w) is >> x;
  std::string tag;
  is >> tag;
  if (!is || tag != engineName() + "-end") {
    is.clear(std::ios::badbit | is.rdstate());
    std::cerr << "Bad " << engineName() << " state in input stream\n";
    return is;
  }
  for (int i = 0; i < Gen::WORDS; ++i) gen.s[i] = w[i];
  return is;
}

// The vector form stores each 64-bit word as two 32-bit halves (low first),
// as MixMaxRng does, so that it does not depend on the width of long.
template <class Gen> std::vector<unsigned long> GenEngine<Gen>::put() const {
  std::vector<unsigned long> v;
  v.reserve(1 + 2 * Gen::WORDS);
  v.push_back(engineIDulong<GenEngine<Gen>>());
  for (int i = 0; i < Gen::WORDS; ++i) {
    v.push_back((unsigned long)(gen.s[i] & 0xffffffffULL));
    v.push_back((unsigned long)(gen.s[i] >> 32));
  }
  return v;
}

template <class Gen> bool GenEngine<Gen>::get(const std::vector<unsigned long> &v) {
  if (v.empty() || v[0] != engineIDulong<GenEngine<Gen>>()) {
    std::cerr << "\n" << engineName() << " get:state vector has wrong ID word - state unchanged\n";
    return false;
  }
  return getState(v);
}

template <class Gen> bool GenEngine<Gen>::getState(const std::vector<unsigned long> &v) {
  if (v.size() != 1 + 2 * (std::size_t)Gen::WORDS) {
    std::cerr << "\n" << engineName() << " getState:state vector has wrong length - state unchanged\n";
    return false;
  }
  for (int i = 0; i < Gen::WORDS; ++i)
    gen.s[i] = (std::uint64_t)(v[1 + 2 * i] & 0xffffffffUL) |
               ((std::uint64_t)(v[2 + 2 * i] & 0xffffffffUL) << 32);
  return true;
}

template <class Gen> void GenEngine<Gen>::saveStatus(const char filename[]) const {
  std::ofstream os(filename, std::ios::out);
  if (!os) {
    std::cerr << "  -- Engine state not saved (cannot open " << filename << ")\n";
    return;
  }
  put(os);
}

template <class Gen> void GenEngine<Gen>::restoreStatus(const char filename[]) {
  std::ifstream is(filename, std::ios::in);
  if (!is) {
    std::cerr << "  -- Engine state remains unchanged (cannot open " << filename << ")\n";
    return;
  }
  get(is);
}

template <class Gen> void GenEngine<Gen>::showStatus() const {
  std::cout << "\n--------- " << engineName() << " engine status ---------\n";
  std::cout << " Initial seed = " << theSeed << "\n State =";
  for (int i = 0; i < Gen::WORDS; ++i) std::cout << " " << gen.s[i];
  std::cout << "\n----------------------------------------\n";
}

template class GenEngine<Xoshiro256ppGen>;
template class GenEngine<Mwc192xGen>;

}  // namespace CLHEP
