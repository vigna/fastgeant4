// Stand-ins for CLHEP code that tests/run-tests-local.sh does not compile:
// HepRandomEngine::newEngine (RandomEngine.cc) refers to the EngineFactory,
// which would pull in every CLHEP engine; the engine tests do not use it.
#include "CLHEP/Random/EngineFactory.h"

namespace CLHEP {
HepRandomEngine *EngineFactory::newEngine(std::istream &) { return nullptr; }
HepRandomEngine *EngineFactory::newEngine(std::vector<unsigned long> const &) { return nullptr; }
}  // namespace CLHEP
