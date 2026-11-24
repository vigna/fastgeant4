// -*- C++ -*-
//
// See G4RngSelect.h.

#include "CLHEP/Random/G4RngSelect.h"
#include "CLHEP/Random/G4RngConfig.h"
#include "CLHEP/Random/G4RngCountingEngine.h"
#include "CLHEP/Random/G4RngEngines.h"
#include "CLHEP/Random/MixMaxRng.h"

#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <typeinfo>

namespace CLHEP {

namespace {

#ifdef G4RNG_FAST
const char *const kVariant = "fast";
#else
const char *const kVariant = "dropin";
#endif

const char *requestedEngine() {
  const char *v = std::getenv("G4RNG_ENGINE");
  return v != nullptr && *v != '\0' ? v : nullptr;
}

bool debugEnabled() {
  static const bool on = [] {
    const char *v = std::getenv("G4RNG_DEBUG");
    return v != nullptr && *v != '\0' && std::strcmp(v, "0") != 0;
  }();
  return on;
}

std::atomic<bool> bannerPrinted{false};

[[noreturn]] void die(const char *msg, const char *name) {
  std::fprintf(stderr, "G4RNG: %s '%s'\n", msg, name);
  std::abort();
}

}  // namespace

HepRandomEngine *G4RngMakeEngine(const std::string &name) {
  static const std::string countPrefix = "count:";
  if (name.compare(0, countPrefix.size(), countPrefix) == 0)
    return new G4RngCountingEngine(G4RngMakeEngine(name.substr(countPrefix.size())));
  if (name == "mixmax") return new MixMaxRng;
  if (name == "xoshiro256pp") return new Xoshiro256ppEngine;
  if (name == "mwc192x") return new Mwc192xEngine;
  die("unknown engine (use mixmax, xoshiro256pp, mwc192x or count:<engine>):",
      name.c_str());
}

HepRandomEngine *G4RngNewEngineLike(const HepRandomEngine *e) {
  if (const auto *c = dynamic_cast<const G4RngCountingEngine *>(e)) {
    HepRandomEngine *inner = G4RngNewEngineLike(c->inner());
    if (inner == nullptr && dynamic_cast<const MixMaxRng *>(c->inner()) != nullptr)
      inner = new MixMaxRng;
    return inner != nullptr ? new G4RngCountingEngine(inner) : nullptr;
  }
  if (dynamic_cast<const Xoshiro256ppEngine *>(e) != nullptr) return new Xoshiro256ppEngine;
  if (dynamic_cast<const Mwc192xEngine *>(e) != nullptr) return new Mwc192xEngine;
  return nullptr;
}

HepRandomEngine *G4RngDefaultEngineForThread() {
  const char *req = requestedEngine();
#ifdef G4RNG_FAST
  // A fast-path build runs only its compiled engine.
  if (req != nullptr && std::strcmp(req, G4RNG_FAST_NAME) != 0)
    die("this fast-path build runs only " G4RNG_FAST_NAME "; G4RNG_ENGINE is", req);
  const char *name = G4RNG_FAST_NAME;
#else
  const char *name = req != nullptr ? req : "mixmax";
#endif
  if (!bannerPrinted.exchange(true))
    std::fprintf(stderr, "G4RNG: variant=%s engine=%s\n", kVariant, name);
  if (std::strcmp(name, "mixmax") == 0) return nullptr;  // CLHEP's built-in default
  return G4RngMakeEngine(name);
}

void G4RngNoteEngine(const HepRandomEngine *oldEngine, const HepRandomEngine *newEngine) {
  if (newEngine == nullptr) return;
  if (oldEngine != nullptr && typeid(*oldEngine) != typeid(*newEngine))
    std::fprintf(stderr, "G4RNG: engine replaced by %s\n", newEngine->name().c_str());
  if (debugEnabled())
    std::fprintf(stderr, "G4RNG: thread engine=%s\n", newEngine->name().c_str());
}

}  // namespace CLHEP
