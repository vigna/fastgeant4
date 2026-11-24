// Prints the default engine's name, then draws argv[1] numbers (default 0)
// through G4Random::getTheEngine()->flat().
#include "Randomize.hh"

#include <cstdio>
#include <cstdlib>

int main(int argc, char **argv) {
  const long n = argc > 1 ? std::atol(argv[1]) : 0;
  CLHEP::HepRandomEngine *e = G4Random::getTheEngine();
  std::printf("engine=%s\n", e->name().c_str());
  double sum = 0;
  for (long i = 0; i < n; i++) sum += e->flat();
  std::printf("sum=%.17g\n", sum);
  return 0;
}
