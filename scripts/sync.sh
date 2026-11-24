#!/bin/sh
# Copies the repository (without upstream/ and scratch) to a host's ~/geant4-rng/repo.
set -eu
host=${1:-desktop}
here=$(cd "$(dirname "$0")/.." && pwd)
rsync -a --delete --exclude upstream/ --exclude .superpowers/ --exclude __pycache__/ \
  --exclude 'results/' "$here/" "$host:geant4-rng/repo/"
