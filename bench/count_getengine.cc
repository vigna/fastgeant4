// LD_PRELOAD shim for the drop-in build: counts the calls of the out-of-line
// CLHEP::HepRandom::getTheEngine() and prints
//   G4RNG-COUNT getTheEngine=<calls>
// to stderr at exit (nothing if there were none).
//
// Every G4UniformRand() (= HepRandom::getTheEngine()->flat()) and every
// engine-less distribution shoot() makes one call; a draw through an engine
// pointer cached by the caller (39 sites in Geant4 11.4.3, e.g. the energy-loss
// fluctuation and de-excitation models) makes none. With the totals of the
// counting engine (G4RNG_ENGINE=count:mixmax), the calls give the share of
// draws that go through the static path, the one the fast path inlines.
// Calls bound inside libG4clhep without the PLT are missed (none in the
// drop-in build: tests/test-count-shim.sh checks the count on a known loop).
//
// Build: g++ -std=c++17 -O2 -shared -fPIC count_getengine.cc -o libcountgetengine.so -ldl

#include <dlfcn.h>

#include <atomic>
#include <cinttypes>
#include <cstdint>
#include <cstdio>
#include <cstdlib>

namespace CLHEP {
class HepRandomEngine;
class HepRandom {
 public:
  static HepRandomEngine *getTheEngine();
};
}  // namespace CLHEP

namespace {
std::atomic<std::uint64_t> calls{0};
using Fn = CLHEP::HepRandomEngine *(*)();
std::atomic<Fn> real{nullptr};
}  // namespace

CLHEP::HepRandomEngine *CLHEP::HepRandom::getTheEngine() {
  Fn f = real.load(std::memory_order_acquire);
  if (f == nullptr) {
    f = (Fn)dlsym(RTLD_NEXT, "_ZN5CLHEP9HepRandom12getTheEngineEv");
    if (f == nullptr) {
      std::fprintf(stderr, "count_getengine: real getTheEngine not found\n");
      std::abort();
    }
    real.store(f, std::memory_order_release);
  }
  calls.fetch_add(1, std::memory_order_relaxed);
  return f();
}

__attribute__((destructor)) static void report() {
  const std::uint64_t n = calls.load();
  if (n != 0) std::fprintf(stderr, "G4RNG-COUNT getTheEngine=%" PRIu64 "\n", n);
}
