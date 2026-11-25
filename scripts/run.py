#!/usr/bin/env python3
"""Campaign runner for the Geant4 PRNG study.

    run.py run   [--host H (default $HOST, else desktop)] --mode st|mt --variants V... --engines E...
                 --workloads W... --reps R --out results/<host>/<date>/runs.csv
    run.py check results/<host>/<date>/runs.csv     # physics consistency
    run.py parse <stdout-file> [<stderr-file>]      # debugging

Every run is pinned with taskset, waits for an idle host, is checked against
the G4RNG banner (variant and engine), and appends one CSV row. Engine names
are the command-line names (mixmax, xoshiro256pp, mwc192x); for a
fast-<engine> variant only that engine is valid. Existing rows are skipped,
so an interrupted campaign resumes where it stopped.
"""

import argparse
import csv
import datetime
import gzip
import json
import math
import os
import re
import resource
import subprocess
import statistics
import sys
import tempfile
import time
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENGINES = ["mixmax", "xoshiro256pp", "mwc192x"]
COLUMNS = ["host", "mode", "workload", "variant", "engine", "rep", "seed1", "seed2",
           "events", "real_s", "user_s", "sys_s", "busy_cpus", "loadavg", "foreign_cpus",
           "sibling_busy", "steal_cpus", "timestamp", "observables"]


class RunMismatch(Exception):
    """The process did not run the requested variant/engine."""


class RunFailed(Exception):
    """The process failed or its output is incomplete."""


class HostBusy(Exception):
    """The host did not become idle in time."""


# ---------------------------------------------------------------- parsing

BANNER_RE = re.compile(r"^G4RNG: variant=(\S+) engine=(\S+)$", re.M)
TIMER_RE = re.compile(r"^  User=([0-9.]+)s Real=([0-9.]+)s Sys=([0-9.]+)s")
EVENTS_RE = re.compile(r"^  Number of events processed : (\d+)")


def variant_kind(variant):
    if variant == "stock":
        return None
    if variant.startswith("fast-"):
        return "fast"
    return "dropin"


def check_banner(stderr, variant, engine):
    banners = BANNER_RE.findall(stderr)
    kind = variant_kind(variant)
    if kind is None:
        if banners:
            raise RunMismatch(f"stock run printed a G4RNG banner: {banners}")
        return
    if len(banners) != 1:
        raise RunMismatch(f"expected one G4RNG banner, found {len(banners)}")
    v, e = banners[0]
    if v != kind or e != engine:
        raise RunMismatch(f"banner variant={v} engine={e}, wanted {kind}/{engine}")
    if "G4RNG: engine replaced" in stderr:
        raise RunMismatch("an engine was replaced during the run")


def parse_timer(stdout):
    """(events, user, real, sys) of the last unprefixed (master) run block."""
    lines = stdout.splitlines()
    found = None
    for i, line in enumerate(lines):
        if not line.startswith(" Run terminated."):
            continue
        events = timer = None
        for nxt in lines[i + 1:i + 6]:
            m = EVENTS_RE.match(nxt)
            if m:
                events = int(m.group(1))
            m = TIMER_RE.match(nxt)
            if m:
                timer = tuple(float(x) for x in m.groups())
        if events is not None and timer is not None:
            found = (events, timer[0], timer[1], timer[2])
    if found is None:
        raise RunFailed("no master 'Run terminated' block with events and timer")
    return found


# G4BestUnit symbols, converted to Geant4's internal units (MeV, mm).
UNITS = {"eV": 1e-6, "keV": 1e-3, "MeV": 1.0, "GeV": 1e3, "TeV": 1e6, "PeV": 1e9,
         "fm": 1e-12, "Ang": 1e-7, "nm": 1e-6, "um": 1e-3, "mm": 1.0, "cm": 10.0,
         "m": 1e3, "km": 1e6}


def parse_observables(stdout, observables):
    """Last match of each observable's regex on unprefixed (master) lines.
    A regex with two groups captures a value and a G4BestUnit symbol."""
    master = "\n".join(l for l in stdout.splitlines() if not l.startswith("G4WT"))
    out = {}
    for ob in observables:
        matches = re.findall(ob["regex"], master, re.M)
        if not matches:
            raise RunFailed(f"observable {ob['name']} not found")
        last = matches[-1]
        if isinstance(last, tuple):
            value, unit = last
            if unit not in UNITS:
                raise RunFailed(f"observable {ob['name']}: unknown unit {unit}")
            out[ob["name"]] = float(value) * UNITS[unit]
        else:
            out[ob["name"]] = float(last)
    return out


# ---------------------------------------------------------------- host state

def read_busy_cpus(interval=2.0):
    """Number of CPUs busy (all users) over `interval` seconds, from /proc/stat."""
    def snap():
        with open("/proc/stat") as f:
            vals = [int(x) for x in f.readline().split()[1:]]
        idle = vals[3] + vals[4]
        return sum(vals), idle
    t0, i0 = snap()
    time.sleep(interval)
    t1, i1 = snap()
    total = t1 - t0
    return 0.0 if total == 0 else (total - (i1 - i0)) / total * os.cpu_count()


def read_loadavg():
    with open("/proc/loadavg") as f:
        return float(f.read().split()[0])


def read_cpu_jiffies(path="/proc/stat"):
    """Per-CPU (busy, steal) jiffies: busy = user + nice + system + irq + softirq."""
    out = {}
    with open(path) as f:
        for line in f:
            if line.startswith("cpu") and line[3].isdigit():
                name, *vals = line.split()
                v = [int(x) for x in vals]
                out[int(name[3:])] = (v[0] + v[1] + v[2] + v[5] + v[6], v[7] if len(v) > 7 else 0)
    return out


def foreign_load(before, after, own_cpu_s, wall_s, hz, watch, exclude=()):
    """Load by others during a run, in CPUs: the busy time of all CPUs but
    `exclude` (those of the other parallel slots) minus the run's own CPU
    time; the busy time of the `watch` CPUs (the idle hyperthread siblings
    of the pinned CPUs, which slow the run without taking its CPU time); and
    the time stolen by the hypervisor."""
    skip = set(exclude)
    busy = sum(after[c][0] - before[c][0] for c in after if c not in skip) / hz
    steal = sum(after[c][1] - before[c][1] for c in after) / hz
    sib = sum(after[c][0] - before[c][0] for c in watch) / hz
    return {"foreign_cpus": max(0.0, busy - own_cpu_s) / wall_s,
            "sibling_busy": sib / wall_s, "steal_cpus": steal / wall_s}


def parse_cpu_list(text):
    cpus = []
    for part in text.strip().split(","):
        lo, _, hi = part.partition("-")
        cpus.extend(range(int(lo), int(hi or lo) + 1))
    return cpus


def read_siblings(cpu):
    return Path(f"/sys/devices/system/cpu/cpu{cpu}/topology/thread_siblings_list").read_text()


def idle_siblings(cpus, read=read_siblings):
    """Hyperthread siblings of `cpus` that are not themselves in `cpus`."""
    pinned = set(cpus)
    return sorted({s for c in cpus for s in parse_cpu_list(read(c))} - pinned)


def wait_for_quiet(read_busy=read_busy_cpus, limit=0.5, max_wait_s=1800, poll_s=30,
                   sleep=time.sleep):
    """Waits until fewer than `limit` CPUs are busy; returns the last reading."""
    waited = 0
    while True:
        busy = read_busy()
        if busy <= limit:
            return busy
        if waited >= max_wait_s:
            raise HostBusy(f"{busy:.2f} CPUs still busy after {waited} s")
        sleep(poll_s)
        waited += poll_s


# ---------------------------------------------------------------- scheduling

def schedule(workloads, configs, reps, slot=0, slots=1):
    """Yields (rep, workload, variant, engine): rep-major, then workload, then
    the configurations rotated by rep, so that no configuration always runs
    in the same position. Slot k of N takes the reps r with r % N == k."""
    n = len(configs)
    for rep in range(reps):
        if rep % slots != slot:
            continue
        rot = configs[rep % n:] + configs[:rep % n]
        for w in workloads:
            for variant, engine in rot:
                yield rep, w, variant, engine


def seeds_for(workload, rep):
    """Seeds shared by all configurations of a (workload, rep): paired design."""
    return 1000 + rep, zlib.crc32(workload.encode()) % 900000 + 1


def configs_for(variants, engines):
    out = []
    for v in variants:
        if v.startswith("fast-"):
            out.append((v, v[len("fast-"):]))
        elif v.startswith("dropin-layout-") or v == "stock":
            out.append((v, "mixmax"))
        else:
            out.extend((v, e) for e in engines)
    return out


# ---------------------------------------------------------------- running

def slot_cpus(host, mode, slot, slots):
    """The taskset CPU list of `slot` of `slots`, and the CPUs of the other
    slots. ST: one CPU of ST_CPUS per slot; MT: MT_CPUS, or with several
    slots one entry of MT_SLOT_CPUS (space-separated lists) per slot."""
    if mode == "st":
        lists = host["ST_CPUS"].split()
    elif slots == 1:
        lists = [host["MT_CPUS"]]
    else:
        lists = host.get("MT_SLOT_CPUS", "").split()
    if not 0 <= slot < slots <= len(lists):
        sys.exit(f"slot {slot} of {slots}: the host lists CPUs for {len(lists)} {mode} slots")
    others = sorted(c for j in range(slots) if j != slot for c in parse_cpu_list(lists[j]))
    return lists[slot], others


def default_event_scale(host, mode, environ=os.environ):
    """Per-host scale of the workloads' event counts (EVENT_SCALE_ST/_MT): from
    the environment if set there (scripts/reproduce.sh exports the calibrated
    scales), else from the host file, else 1."""
    key = f"EVENT_SCALE_{mode.upper()}"
    return float(environ.get(key, host.get(key, 1.0)))


def calibrated_scale(rows, workloads, mode, target_s):
    """The event scale at which the median workload of the pilot `rows` (runs
    of `mode`) takes `target_s` seconds, to two significant digits: for each
    workload, the scale of its base event count (events_st or events_mt)
    that the mean time per event of its runs makes last `target_s`."""
    per_event = {}
    for r in rows:
        if r["mode"] == mode:
            per_event.setdefault(r["workload"], []).append(float(r["real_s"]) / float(r["events"]))
    scales = sorted(target_s / statistics.fmean(v) / workloads[w][f"events_{mode}"]
                    for w, v in per_event.items())
    if not scales:
        raise ValueError(f"no {mode} runs to calibrate from")
    m = statistics.median(scales)
    return float(f"{m:.2g}")


def default_host(environ=os.environ):
    """The host named by $HOST (as the shell scripts use it), else desktop."""
    return environ.get("HOST", "desktop")


def load_host(host):
    env = {}
    text = (REPO / "hosts" / f"{host}.env").read_text()
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if "=" in line:
            k, v = line.split("=", 1)
            env[k] = os.path.expandvars(v.strip().strip('"'))
    return env


def load_workloads():
    return json.loads((REPO / "workloads" / "workloads.json").read_text())


def render_macro(wl, events, seed1, seed2, dest):
    text = (REPO / "workloads" / wl["macro"]).read_text()
    text = text.replace("@EVENTS@", str(events)).replace("@SEED1@", str(seed1)) \
               .replace("@SEED2@", str(seed2))
    dest.write_text(text)


def build_command(wl, exe, macro, cpus):
    """taskset + the example + its arguments (workload "args", default [macro])."""
    args = [a.replace("@MACRO@", macro) for a in wl.get("args", ["@MACRO@"])]
    return ["taskset", "-c", cpus, exe] + args


def run_one(host, mode, name, wl, variant, engine, events, seed1, seed2, logdir, tag,
            cpus=None, exclude=(), prefix=()):
    """Runs one workload; `prefix` goes before the command (scripts/perfstat.py
    puts perf stat there)."""
    root = Path(host["ROOT"])
    exe = root / f"examples-{variant}" / Path(wl["example"]).name / wl["exe"]
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = str(root / f"install-{variant}" / "lib64")
    env.pop("G4RNG_DEBUG", None)
    if variant != "stock":
        env["G4RNG_ENGINE"] = engine
    if cpus is None:
        cpus, exclude = slot_cpus(host, mode, 0, 1)
    if mode == "st":
        env["G4FORCE_RUN_MANAGER_TYPE"] = "Serial"
    else:
        env["G4FORCE_RUN_MANAGER_TYPE"] = "Tasking"
        env["G4FORCENUMBEROFTHREADS"] = str(len(parse_cpu_list(cpus)))
    with tempfile.TemporaryDirectory(prefix="g4rng-") as work:
        work = Path(work)
        macro = work / "run.mac"
        render_macro(wl, events, seed1, seed2, macro)
        cmd = list(prefix) + build_command(wl, str(exe), str(macro), cpus)
        before, ru0, t0 = read_cpu_jiffies(), resource.getrusage(resource.RUSAGE_CHILDREN), \
            time.monotonic()
        p = subprocess.run(cmd, cwd=work, env=env, capture_output=True, text=True)
        wall, after, ru1 = time.monotonic() - t0, read_cpu_jiffies(), \
            resource.getrusage(resource.RUSAGE_CHILDREN)
    own = (ru1.ru_utime - ru0.ru_utime) + (ru1.ru_stime - ru0.ru_stime)
    load = foreign_load(before, after, own, wall, os.sysconf("SC_CLK_TCK"),
                        idle_siblings(parse_cpu_list(cpus)), exclude)
    if logdir is not None:
        logdir.mkdir(parents=True, exist_ok=True)
        for suffix, text in (("out", p.stdout), ("err", p.stderr)):
            with gzip.open(logdir / f"{tag}.{suffix}.gz", "wt") as f:
                f.write(text)
    if p.returncode != 0:
        raise RunFailed(f"{tag}: exit status {p.returncode}: {p.stderr[-500:]}")
    check_banner(p.stderr, variant, engine)
    ev, user, real, sys_ = parse_timer(p.stdout)
    if ev != events:
        raise RunFailed(f"{tag}: {ev} events processed, wanted {events}")
    obs = parse_observables(p.stdout, wl.get("observables", []))
    return {"events": ev, "real_s": real, "user_s": user, "sys_s": sys_, "observables": obs,
            **load}


def csv_fieldnames(path):
    """The header of an existing CSV (rows appended to a file written by an
    older runner keep its columns), else COLUMNS."""
    if path.exists() and path.stat().st_size > 0:
        with open(path) as f:
            return next(csv.reader(f))
    return COLUMNS


def done_keys(path):
    if not path.exists():
        return set()
    with open(path) as f:
        return {(r["mode"], r["workload"], r["variant"], r["engine"], int(r["rep"]))
                for r in csv.DictReader(f)}


def cmd_run(args):
    host = load_host(args.host)
    workloads = load_workloads()
    for w in args.workloads:
        if w not in workloads:
            sys.exit(f"unknown workload {w}")
    configs = configs_for(args.variants, args.engines)
    cpus, others = slot_cpus(host, args.mode, args.slot, args.slots)
    scale = args.event_scale if args.event_scale is not None else \
        default_event_scale(host, args.mode)
    busy_limit = args.busy_limit + len(others)  # the other slots are busy
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    logdir = out.parent / "logs"
    done = done_keys(out)
    new_file = not out.exists()
    evkey = "events_st" if args.mode == "st" else "events_mt"
    with open(out, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=csv_fieldnames(out) if not new_file else COLUMNS,
                           extrasaction="ignore")
        if new_file:
            w.writeheader()
        if not args.no_warmup:
            for name in args.workloads:
                for variant in dict.fromkeys(v for v, _ in configs):
                    engine = next(e for v, e in configs if v == variant)
                    print(f"warm-up {name} {variant}", flush=True)
                    run_one(host, args.mode, name, workloads[name], variant, engine,
                            workloads[name]["events_warmup"], 1, 1, None, "warmup", cpus, others)
        for rep, name, variant, engine in schedule(args.workloads, configs, args.reps,
                                                   args.slot, args.slots):
            key = (args.mode, name, variant, engine, rep)
            if key in done:
                continue
            wl = workloads[name]
            events = int(wl[evkey] * scale)
            s1, s2 = seeds_for(name, rep)
            busy = wait_for_quiet(limit=busy_limit)
            load = read_loadavg()
            tag = f"{args.mode}-{name}-{variant}-{engine}-{rep}"
            t0 = time.time()
            r = run_one(host, args.mode, name, wl, variant, engine, events, s1, s2, logdir, tag,
                        cpus, others)
            row = {"host": args.host, "mode": args.mode, "workload": name, "variant": variant,
                   "engine": engine, "rep": rep, "seed1": s1, "seed2": s2,
                   "events": r["events"], "real_s": r["real_s"], "user_s": r["user_s"],
                   "sys_s": r["sys_s"], "busy_cpus": round(busy, 3), "loadavg": load,
                   **{k: round(r[k], 3) for k in ("foreign_cpus", "sibling_busy", "steal_cpus")},
                   "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
                   "observables": json.dumps(r["observables"], sort_keys=True)}
            w.writerow(row)
            f.flush()
            print(f"{tag}: real={r['real_s']:.3f}s wall={time.time() - t0:.1f}s busy={busy:.2f}",
                  flush=True)


# ---------------------------------------------------------------- physics check

def _betacf(a, b, x):
    """Continued fraction of the incomplete beta function (modified Lentz)."""
    tiny = 1e-300
    c, d = 1.0, 1.0 - (a + b) * x / (a + 1.0)
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 500):
        for aa in (m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m)),
                   -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1))):
            d = 1.0 + aa * d
            d = 1.0 / (d if abs(d) > tiny else tiny)
            c = 1.0 + aa / c
            c = c if abs(c) > tiny else tiny
            h *= d * c
        if abs(d * c - 1.0) < 1e-15:
            break
    return h


def betai(a, b, x):
    """Regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                     + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_sf2(t, df):
    """Two-sided tail P(|T| > |t|) of Student's t with df degrees of freedom."""
    return betai(df / 2.0, 0.5, df / (df + t * t))


def welch(vals, ref):
    """(t, df, p) of Welch's test of mean(vals) = mean(ref). With no spread
    on either side (quantized output) any difference has p = 0."""
    m, se = mean_se(vals)
    m0, se0 = mean_se(ref)
    se_c = math.hypot(se, se0)
    if se_c == 0:
        return (0.0, math.inf, 1.0) if m == m0 else (math.copysign(math.inf, m - m0),
                                                     math.inf, 0.0)
    t = (m - m0) / se_c
    df = se_c ** 4 / ((se ** 4 / (len(vals) - 1) if se else 0.0)
                      + (se0 ** 4 / (len(ref) - 1) if se0 else 0.0))
    return t, df, t_sf2(t, df)


def physics_comparisons(groups, alpha=0.01):
    """Each configuration's observable against dropin/mixmax's, by Welch's
    test. groups: {(mode, workload, observable): {(variant, engine): values}}.
    Builds of one engine run the same events (same seeds; check_identity
    verifies it rep by rep), so a comparison per engine is a separate one:
    the drop-in build's; the others (fast path, layout replicates, stock,
    with MIXMAX the reference itself) are duplicates. With n separate
    comparisons, those with p < alpha / n are flagged (Bonferroni: the chance
    that a campaign with no real difference flags anything is at most alpha).
    Returns dicts with key, cfg, m, m0, t, df, p, n, flagged, duplicate."""
    out, seen = [], set()
    for key, cfgs in sorted(groups.items()):
        ref = cfgs.get(("dropin", "mixmax"))
        if ref is None or len(ref) < 2:
            continue
        engines = {"mixmax"}
        for cfg, vals in sorted(cfgs.items(), key=lambda kv: (kv[0][0] != "dropin", kv[0])):
            if cfg == ("dropin", "mixmax") or len(vals) < 2:
                continue
            t, df, p = welch(vals, ref)
            dup = cfg[1] in engines
            engines.add(cfg[1])
            if not dup:
                seen.add((key, cfg[1]))
            out.append({"key": key, "cfg": cfg, "m": mean_se(vals)[0], "m0": mean_se(ref)[0],
                        "t": t, "df": df, "p": p, "duplicate": dup})
    n = max(len(seen), 1)
    for c in out:
        c["n"] = n
        c["flagged"] = c["p"] < alpha / n
    return out


def cmd_check(args, alpha=0.01):
    """Compares each configuration's observable means with dropin/mixmax by
    Welch's t test, family-wise at alpha (physics_comparisons), and checks
    that builds sharing engine and rep agree exactly (check_identity)."""
    paths = [args.csv] if isinstance(args.csv, str) else args.csv
    groups = {}
    for r in read_rows(paths):
        for k, v in json.loads(r["observables"]).items():
            groups.setdefault((r["mode"], r["workload"], k), {}) \
                  .setdefault((r["variant"], r["engine"]), []).append(v)
    cs = physics_comparisons(groups, alpha)
    for c in cs:
        mode, wl, ob = c["key"]
        flag = "  <-- p < alpha/n" if c["flagged"] else ""
        print(f"{mode} {wl} {ob} {c['cfg'][0]}/{c['cfg'][1]}: {c['m']:.6g} vs {c['m0']:.6g} "
              f"t={c['t']:+.2f} df={c['df']:.0f} p={c['p']:.2g}{flag}")
    bad = sum(c["flagged"] for c in cs)
    distinct = [c for c in cs if not c["duplicate"]]
    if distinct:
        big = sum(abs(c["t"]) > 3 for c in distinct)
        expected = sum(t_sf2(3.0, c["df"]) for c in distinct if math.isfinite(c["df"]))
        print(f"physics: {len(distinct)} distinct comparisons; flag p < {alpha} / "
              f"{len(distinct)} = {alpha / len(distinct):.2g}; smallest p "
              f"{min(c['p'] for c in distinct):.2g}; |t| > 3 in {big} "
              f"(expected with no real difference: {expected:.1f})")
    bad += check_identity(paths)
    print("PHYSICS CHECK " + ("FAILED" if bad else "PASSED"))
    return 1 if bad else 0


def read_rows(paths):
    for p in paths:
        with open(p) as f:
            yield from csv.DictReader(f)


def check_identity(path):
    """Runs of one engine and repetition use the same seeds in every build
    (drop-in, fast path, layout replicates): their observables must be
    equal. A build drawing from another stream (e.g. a fast-path pointer
    that misses the reseeded engine) would pass the z test but not this.
    Returns the number of mismatching runs."""
    groups = {}
    for r in read_rows([path] if isinstance(path, str) else path):
        groups.setdefault((r["mode"], r["workload"], r["engine"], r["rep"]), {})[
            r["variant"]] = json.loads(r["observables"])
    bad = compared = 0
    for (mode, wl, engine, rep), builds in sorted(groups.items()):
        if len(builds) < 2:
            continue
        ref_variant = "dropin" if "dropin" in builds else sorted(builds)[0]
        ref = builds[ref_variant]
        for variant, obs in sorted(builds.items()):
            if variant == ref_variant:
                continue
            compared += 1
            if obs != ref:
                bad += 1
                diff = ", ".join(f"{k} {obs.get(k)} vs {ref.get(k)}"
                                 for k in sorted(set(obs) | set(ref)) if obs.get(k) != ref.get(k))
                print(f"IDENTITY {mode} {wl} {engine} rep {rep}: {variant} differs from "
                      f"{ref_variant}: {diff}  <-- not the same physics")
    print(f"identity: {compared} runs compared with the same engine and repetition in "
          f"another build, {bad} differ")
    return bad


def mean_se(vals):
    n = len(vals)
    m = sum(vals) / n
    var = sum((v - m) ** 2 for v in vals) / (n - 1)
    return m, math.sqrt(var / n)


def cmd_parse(args):
    out = Path(args.stdout).read_text()
    print(parse_timer(out))
    if args.stderr:
        print(BANNER_RE.findall(Path(args.stderr).read_text()))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--host", default=default_host())
    r.add_argument("--mode", choices=["st", "mt"], required=True)
    r.add_argument("--variants", nargs="+", required=True)
    r.add_argument("--engines", nargs="+", default=ENGINES)
    r.add_argument("--workloads", nargs="+", required=True)
    r.add_argument("--reps", type=int, required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--slot", type=int, default=0, help="this slot (parallel runs)")
    r.add_argument("--slots", type=int, default=1, help="number of parallel slots")
    r.add_argument("--event-scale", type=float, default=None,
                   help="multiply the workload's event count (for pilots and checks)")
    r.add_argument("--busy-limit", type=float, default=0.5)
    r.add_argument("--no-warmup", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("csv", nargs="+")
    k = sub.add_parser("calibrate", help="event scale for a target run time, from pilot runs")
    k.add_argument("csv", nargs="+")
    k.add_argument("--mode", choices=["st", "mt"], required=True)
    k.add_argument("--target", type=float, required=True, help="seconds per run")
    p = sub.add_parser("parse")
    p.add_argument("stdout")
    p.add_argument("stderr", nargs="?")
    args = ap.parse_args()
    if args.cmd == "run":
        cmd_run(args)
    elif args.cmd == "check":
        sys.exit(cmd_check(args))
    elif args.cmd == "calibrate":
        print(calibrated_scale(read_rows(args.csv), load_workloads(), args.mode, args.target))
    else:
        cmd_parse(args)


if __name__ == "__main__":
    main()
