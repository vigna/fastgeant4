// -*- C++ -*-
//
// See G4RngCountingEngine.h.

#include "CLHEP/Random/G4RngCountingEngine.h"

#include <atomic>
#include <cinttypes>
#include <cstdio>
#include <cstdlib>
#include <mutex>

namespace CLHEP {

namespace {

std::atomic<std::uint64_t> nFlat{0}, nFlatArray{0}, nSetSeeds{0};

void printCounts() {
  std::fprintf(stderr, "G4RNG-COUNT flat=%" PRIu64 " flatArray=%" PRIu64 " setSeeds=%" PRIu64 "\n",
               nFlat.load(), nFlatArray.load(), nSetSeeds.load());
}

std::once_flag registerOnce;

inline void bump(std::atomic<std::uint64_t> &c, std::uint64_t n = 1) {
  c.fetch_add(n, std::memory_order_relaxed);
}

}  // namespace

G4RngCountingEngine::G4RngCountingEngine(HepRandomEngine *inner) : inner_(inner) {
  std::call_once(registerOnce, [] { std::atexit(printCounts); });
}

G4RngCountingEngine::~G4RngCountingEngine() = default;

double G4RngCountingEngine::flat() {
  bump(nFlat);
  return inner_->flat();
}

void G4RngCountingEngine::flatArray(const int size, double *vect) {
  bump(nFlatArray, size > 0 ? size : 0);
  inner_->flatArray(size, vect);
}

void G4RngCountingEngine::setSeed(long seed, int lux) {
  bump(nSetSeeds);
  theSeed = seed;
  inner_->setSeed(seed, lux);
}

void G4RngCountingEngine::setSeeds(const long *seeds, int count) {
  bump(nSetSeeds);
  theSeed = seeds[0];
  theSeeds = seeds;
  inner_->setSeeds(seeds, count);
}

void G4RngCountingEngine::saveStatus(const char filename[]) const { inner_->saveStatus(filename); }
void G4RngCountingEngine::restoreStatus(const char filename[]) { inner_->restoreStatus(filename); }
void G4RngCountingEngine::showStatus() const { inner_->showStatus(); }

std::string G4RngCountingEngine::name() const { return engineName() + "(" + inner_->name() + ")"; }

std::ostream &G4RngCountingEngine::put(std::ostream &os) const { return inner_->put(os); }
std::istream &G4RngCountingEngine::get(std::istream &is) { return inner_->get(is); }
std::istream &G4RngCountingEngine::getState(std::istream &is) { return inner_->getState(is); }
std::vector<unsigned long> G4RngCountingEngine::put() const { return inner_->put(); }
bool G4RngCountingEngine::get(const std::vector<unsigned long> &v) { return inner_->get(v); }
bool G4RngCountingEngine::getState(const std::vector<unsigned long> &v) { return inner_->getState(v); }

G4RngCountingEngine::operator unsigned int() {
  bump(nFlat);
  return (unsigned int)(*inner_);
}

}  // namespace CLHEP
