// -*- C++ -*-
//
// A wrapper engine that counts the numbers drawn from, and the reseedings
// of, an inner engine. The counters are process-wide (relaxed atomics, so
// counting slows multithreaded runs); at exit the process prints
//   G4RNG-COUNT flat=<n> flatArray=<n> setSeeds=<n>
// on stderr. Used only for counting runs, never for timing runs.

#ifndef G4RngCountingEngine_h
#define G4RngCountingEngine_h 1

#include "CLHEP/Random/RandomEngine.h"

#include <memory>
#include <string>
#include <vector>

namespace CLHEP {

class G4RngCountingEngine final : public HepRandomEngine {
public:
  // Takes ownership of inner.
  explicit G4RngCountingEngine(HepRandomEngine *inner);
  ~G4RngCountingEngine() override;

  double flat() override;
  void flatArray(const int size, double *vect) override;
  void setSeed(long seed, int lux) override;
  void setSeeds(const long *seeds, int count) override;
  void saveStatus(const char filename[] = "Config.conf") const override;
  void restoreStatus(const char filename[] = "Config.conf") override;
  void showStatus() const override;
  std::string name() const override;
  static std::string engineName() { return "G4RngCountingEngine"; }

  std::ostream &put(std::ostream &os) const override;
  std::istream &get(std::istream &is) override;
  std::istream &getState(std::istream &is) override;
  std::vector<unsigned long> put() const override;
  bool get(const std::vector<unsigned long> &v) override;
  bool getState(const std::vector<unsigned long> &v) override;

  operator double() override { return flat(); }
  operator float() override { return float(flat()); }
  operator unsigned int() override;

  const HepRandomEngine *inner() const { return inner_.get(); }

private:
  std::unique_ptr<HepRandomEngine> inner_;
};

}  // namespace CLHEP

#endif
