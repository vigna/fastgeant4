#!/bin/bash
# perf profiles of the stock build: share of samples in the random-number code.
# Writes <dir>/profile.md. Usage: scripts/profile.sh <results-dir> [workload...]
# Needs examples built against install-stock. Run on the build host, idle.
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
source "$repo/hosts/${HOST:-desktop}.env"
dir=${1:?results-dir}; shift
wl=("$@"); [ ${#wl[@]} -gt 0 ] || wl=(testem3 b4hadr testem11 opnovice2 range)
mkdir -p "$dir/profile"
python3 - "$repo" "$dir" "$ROOT" "$ST_CPUS" "$MT_CPUS" "$MT_THREADS" "${wl[@]}" <<'PY'
import json, os, re, subprocess, sys, tempfile
from pathlib import Path
repo, d, root, st_cpus, mt_cpus, mt_threads, *wls = sys.argv[1:]
d, root = Path(d), Path(root)
workloads = json.loads((Path(repo) / "workloads" / "workloads.json").read_text())
cats = [("MixMaxRng::flat", r"CLHEP::MixMaxRng::flat\(\)"),
        ("MixMaxRng::iterate", r"CLHEP::MixMaxRng::(iterate|iterate_raw_vec|modadd|get_next)"),
        ("getTheEngine", r"CLHEP::HepRandom::getTheEngine"),
        ("reseeding", r"CLHEP::MixMaxRng::(setSeeds|seed_uniquestream|apply_bigskip|seed_vielbein|state_init|fmodmulM61|seed_spbox)"),
        ("CLHEP distributions", r"CLHEP::Rand\w+::"),
        ("G4Poisson etc.", r"G4Poisson|G4RandomDirection|G4RandomTools")]
lines = ["| workload | mode | " + " | ".join(c for c, _ in cats) + " | total |",
         "|:--|:--|" + "--:|" * (len(cats) + 1)]
for w in wls:
    wl = workloads[w]
    for mode in ("st", "mt"):
        exe = root / "examples-stock" / Path(wl["example"]).name / wl["exe"]
        events = max(1, int(wl["events_st" if mode == "st" else "events_mt"] // 2))
        text = (Path(repo) / "workloads" / wl["macro"]).read_text()
        text = text.replace("@EVENTS@", str(events)).replace("@SEED1@", "1001").replace("@SEED2@", "7")
        env = dict(os.environ, LD_LIBRARY_PATH=str(root / "install-stock" / "lib64"))
        if mode == "st":
            env["G4FORCE_RUN_MANAGER_TYPE"] = "Serial"; cpus = st_cpus.split()[0]
        else:
            env["G4FORCE_RUN_MANAGER_TYPE"] = "Tasking"; env["G4FORCENUMBEROFTHREADS"] = mt_threads
            cpus = mt_cpus
        data = d / "profile" / f"{mode}-{w}.perf.data"
        with tempfile.TemporaryDirectory() as work:
            (Path(work) / "run.mac").write_text(text)
            args = [a.replace("@MACRO@", "run.mac") for a in wl.get("args", ["@MACRO@"])]
            subprocess.run(["perf", "record", "-q", "-F", "1999", "-o", str(data), "--",
                            "taskset", "-c", cpus, str(exe)] + args,
                           cwd=work, env=env, check=True, capture_output=True)
        rep = subprocess.run(["perf", "report", "-i", str(data), "--no-children", "--sort", "sym",
                              "--stdio", "-q"], capture_output=True, text=True, check=True).stdout
        (d / "profile" / f"{mode}-{w}.txt").write_text(rep)
        share = [0.0] * len(cats)
        for line in rep.splitlines():
            m = re.match(r"\s*([0-9.]+)%\s+\[\.\]\s+(.*)", line)
            if not m:
                continue
            for i, (_, rx) in enumerate(cats):
                if re.search(rx, m.group(2)):
                    share[i] += float(m.group(1))
                    break
        lines.append(f"| {w} | {mode} | " + " | ".join(f"{s:.2f}%" for s in share) +
                     f" | {sum(share):.2f}% |")
        print(lines[-1], flush=True)
md = "## Share of perf samples in random-number code (stock build)\n\n" + "\n".join(lines) + "\n"
(d / "profile.md").write_text(md)
PY
