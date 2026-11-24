// -*- C++ -*-
//
// Fast path for the Geant4 PRNG study (fast-path builds only, that is, when
// G4RngConfig.h defines G4RNG_FAST as an engine class name).
//
// Each thread keeps two initial-exec thread-local pointers to its default
// engine: g4rng_tls_engine, as a HepRandomEngine, and g4rng_fast_engine, as
// the compiled engine class (nullptr if the thread's engine is of another
// type). HepRandom::getTheEngine() becomes an inline read of the first, and
// G4UniformRand() (see Randomize.hh) a qualified, hence non-virtual and
// inlinable, call to the compiled engine's flat() through the second.
// Random.cc keeps both pointers equal to the thread's default engine.
//
// Included at the end of Random.h; do not include directly.

#ifndef G4RngFast_h
#define G4RngFast_h 1

#include "CLHEP/Random/G4RngConfig.h"

#ifdef G4RNG_FAST

#include "CLHEP/Random/G4RngEngines.h"
#include "CLHEP/Random/MixMaxRng.h"

namespace CLHEP {

extern __thread HepRandomEngine *g4rng_tls_engine;
extern __thread G4RNG_FAST *g4rng_fast_engine;

inline HepRandomEngine *HepRandom::getTheEngine() {
  HepRandomEngine *e = g4rng_tls_engine;
  return __builtin_expect(e != nullptr, 1) ? e : getTheEngineSlow();
}

inline double G4RngFastFlat() {
  G4RNG_FAST *e = g4rng_fast_engine;
  if (__builtin_expect(e != nullptr, 1)) return e->G4RNG_FAST::flat();
  return HepRandom::getTheEngine()->flat();
}

}  // namespace CLHEP

#endif  // G4RNG_FAST

#endif
