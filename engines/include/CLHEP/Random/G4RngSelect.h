// -*- C++ -*-
//
// Engine selection for the Geant4 PRNG study.
//
// Drop-in builds choose the default engine of every thread from the
// environment variable G4RNG_ENGINE: mixmax (default), xoshiro256pp,
// mwc192x, or count:<one of these> (a counting wrapper, for counting runs
// only). Fast-path builds (G4RNG_FAST defined in G4RngConfig.h) compile one
// engine in, and accept G4RNG_ENGINE only if unset or naming that engine.
//
// Diagnostics on stderr:
//   G4RNG: variant=<dropin|fast> engine=<name>   once per process
//   G4RNG: engine replaced by <name>              a thread's engine changed type
//   G4RNG: thread engine=<name>                    with G4RNG_DEBUG=1, every change

#ifndef G4RngSelect_h
#define G4RngSelect_h 1

#include <string>

namespace CLHEP {

class HepRandomEngine;

// Creates the engine named by `name`; prints a message and aborts on an
// unknown name.
HepRandomEngine *G4RngMakeEngine(const std::string &name);

// A new engine of the same type as `e` (for a counting engine, a new counter
// around a new inner engine of the same type), or nullptr if `e` is not one
// of the engines added by this study (callers then use their own cloning).
HepRandomEngine *G4RngNewEngineLike(const HepRandomEngine *e);

// Called when a thread's CLHEP defaults are created: the engine to install
// as the thread's default, or nullptr to keep CLHEP's built-in MixMaxRng.
// Prints the banner the first time it is called in a process.
HepRandomEngine *G4RngDefaultEngineForThread();

// Called whenever a thread's default engine is set (oldEngine is nullptr at
// creation).
void G4RngNoteEngine(const HepRandomEngine *oldEngine, const HepRandomEngine *newEngine);

}  // namespace CLHEP

#endif
