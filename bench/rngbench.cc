// Per-call cost of drawing random numbers through Geant4's call paths.
//   rngbench <what> <n> [reps]
// what: G4UniformRand | getTheEngine_flat | RandGaussQ | setSeeds
// Prints the median, over reps (default 5), of the nanoseconds per call.
// Results are folded into a volatile sink with xor (1-cycle latency), so the
// loop is not bound by the 4-cycle latency of a floating-point sum.
#include "Randomize.hh"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

static volatile std::uint64_t sink;

static inline std::uint64_t bits(double x) {
  std::uint64_t b;
  std::memcpy(&b, &x, sizeof b);
  return b;
}

template <class F> static double ns_per_call(long n, F f) {
  const auto t0 = std::chrono::steady_clock::now();
  f(n);
  const auto t1 = std::chrono::steady_clock::now();
  return std::chrono::duration<double, std::nano>(t1 - t0).count() / n;
}

int main(int argc, char **argv) {
  if (argc < 3) {
    std::fprintf(stderr, "usage: %s G4UniformRand|getTheEngine_flat|RandGaussQ|setSeeds n [reps]\n", argv[0]);
    return 1;
  }
  const std::string what = argv[1];
  const long n = std::atol(argv[2]);
  const int reps = argc > 3 ? std::atoi(argv[3]) : 5;
  const long seeds0[2] = {12345, 67890};
  G4Random::setTheSeeds(seeds0, -1);

  std::vector<double> t;
  for (int r = 0; r < reps; r++) {
    double ns;
    if (what == "G4UniformRand") {
      ns = ns_per_call(n, [](long m) {
        std::uint64_t acc = 0;
        for (long i = 0; i < m; i++) acc ^= bits(G4UniformRand());
        sink = acc;
      });
    } else if (what == "getTheEngine_flat") {
      ns = ns_per_call(n, [](long m) {
        std::uint64_t acc = 0;
        for (long i = 0; i < m; i++) acc ^= bits(G4Random::getTheEngine()->flat());
        sink = acc;
      });
    } else if (what == "RandGaussQ") {
      ns = ns_per_call(n, [](long m) {
        std::uint64_t acc = 0;
        for (long i = 0; i < m; i++) acc ^= bits(G4RandGauss::shoot());
        sink = acc;
      });
    } else if (what == "setSeeds") {
      // Geant4's per-event seeds: pairs of values below 10^8 drawn by the
      // master (G4MTRunManager::InitializeSeeds), precomputed here.
      std::vector<long> s(2 * n);
      for (long &x : s) x = (long)(100000000L * G4UniformRand()) + 1;
      ns = ns_per_call(n, [&s](long m) {
        for (long i = 0; i < m; i++) G4Random::setTheSeeds(&s[2 * i], -1);
      });
    } else {
      std::fprintf(stderr, "unknown measurement %s\n", what.c_str());
      return 1;
    }
    t.push_back(ns);
  }
  std::sort(t.begin(), t.end());
  std::printf("%.4f\n", t[t.size() / 2]);
  return 0;
}
