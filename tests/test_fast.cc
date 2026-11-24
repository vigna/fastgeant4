// Fast-path test: G4UniformRand() (inlined, non-virtual) draws exactly the
// sequence that a separate engine of the compiled type draws through its
// virtual flat(), from the same seeds; and the fast pointer is in use.
#include "Randomize.hh"
#include "CLHEP/Random/G4RngSelect.h"

#include <cstdio>
#include <cstdlib>

int main() {
  const long seeds[2] = {12345, 67890};
  G4Random::setTheSeeds(seeds, -1);
  CLHEP::HepRandomEngine *ref = CLHEP::G4RngMakeEngine(G4RNG_FAST_NAME);
  ref->setSeeds(seeds, -1);
  for (long i = 0; i < 1000000; i++) {
    const double a = G4UniformRand(), b = ref->flat();
    if (a != b) {
      std::fprintf(stderr, "mismatch at draw %ld: %.17g != %.17g\n", i, a, b);
      return 1;
    }
  }
  if (CLHEP::g4rng_fast_engine == nullptr ||
      static_cast<CLHEP::HepRandomEngine *>(CLHEP::g4rng_fast_engine) != G4Random::getTheEngine()) {
    std::fprintf(stderr, "fast engine pointer not set to the default engine\n");
    return 1;
  }
  std::printf("FAST TEST PASSED (%s)\n", G4Random::getTheEngine()->name().c_str());
  return 0;
}
