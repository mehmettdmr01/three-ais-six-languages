#!/usr/bin/env python3
"""Builds every agent's six files with the exact commands from PROMPT.txt, checks them on the given seed
and on hidden seeds the agents never saw, then times them next to my versions in ref/ (interleaved
rounds, best of 7, the program's own sim_ms, plus an independent estimate from wall-clock
differences, so a wrong timer cannot win).
  python3 measure.py                          -> results.json (claude-sonnet, codex, gemini, claude-opus)
Python runs with $PYTHON (default: python3); the video used Python 3.15 with NumPy 2.5.4."""
import json, os, re, shutil, statistics, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE / "build"
PY = os.environ.get("PYTHON", "python3")
WALL = str(HERE / "build/wall")
SEED = str(HERE / "seed/start_512.txt")
TESTS = [("512", "200", SEED, 18885), ("512", "2000", SEED, 8836), ("300", "150", str(HERE / "seed/hidden_300.txt"), 7791),
         ("1000", "50", str(HERE / "seed/hidden_1000.txt"), 122523), ("64", "500", str(HERE / "seed/hidden_64.txt"), 147)]
ROUNDS, LONG_ROUNDS = 7, 3
LANGS = {"c": ("life.c", lambda d: ["clang", "-O2", "-o", "life_c", "life.c"], lambda d: [str(d / "life_c")]),
         "rust": ("life.rs", lambda d: ["rustc", "-C", "opt-level=3", "-o", "life_rs", "life.rs"], lambda d: [str(d / "life_rs")]),
         "go": ("life.go", lambda d: ["go", "build", "-o", "life_go", "life.go"], lambda d: [str(d / "life_go")]),
         "zig": ("life.zig", lambda d: ["zig", "build-exe", "-O", "ReleaseFast", "-femit-bin=life_zig", "life.zig"], lambda d: [str(d / "life_zig")]),
         "python": ("life.py", None, lambda d: [PY, str(d / "life.py")]),
         "js": ("life.js", None, lambda d: ["node", str(d / "life.js")])}
REFS = {  # my versions: the V5 repo's, plus a JavaScript one written for this video
    "ref_c_fast": ("c", HERE / "ref/c/fast.c"), "ref_c_bitpacked": ("c", HERE / "ref/c/bitpacked.c"), "ref_rust_fast": ("rust", HERE / "ref/rust/fast.rs"),
    "ref_go_fast": ("go", HERE / "ref/go/fast.go"), "ref_go_swar": ("go", HERE / "ref/go/swar.go"), "ref_zig_fast": ("zig", HERE / "ref/zig/fast.zig"),
    "ref_zig_vector": ("zig", HERE / "ref/zig/vector.zig"), "ref_numpy": ("python", HERE / "ref/numpy/life.py"),
    "ref_numpy_four_rolls": ("python", HERE / "ref/numpy/four_rolls.py"), "ref_js_fast": ("js", HERE / "ref/js/fast.js")}
THREADS = re.compile(r"pthread|std::thread|thread::spawn|rayon|go func|sync\.WaitGroup|std\.Thread|worker_threads|multiprocessing|concurrent\.futures|Thread\(")

def env(d):
    return dict(os.environ, GOCACHE=str(d / ".cache/go"), ZIG_GLOBAL_CACHE_DIR=str(d / ".cache/zig"))

def run(cmd, timeout=180):
    try:
        p = subprocess.run([WALL, *cmd], capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    w = re.search(r"seconds=([\d.]+) maxrss_kb=(\d+) cpu_s=([\d.]+)", p.stdout)
    a = re.search(r"alive=(\d+)(?:\s+sim_ms=([\d.eE+-]+))?", p.stdout)
    if not w: return {"error": (p.stdout + p.stderr)[-300:]}
    return {"alive": int(a[1]) if a else None, "sim_ms": float(a[2]) if a and a[2] else None, "wall": float(w[1]),
            "rss_kb": int(w[2]), "cpu_s": float(w[3]), "out": p.stdout.split("seconds=")[0].strip()[-200:]}

def prepare(name, lang, src, build):
    d = WORK / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    fname = LANGS[lang][0]
    if not Path(src).exists(): return d, {"ok": False, "error": "file missing"}
    shutil.copy(src, d / fname)
    info = {"ok": True, "lines": sum(1 for l in open(d / fname) if l.strip()), "threads_in_source": bool(THREADS.search((d / fname).read_text()))}
    if LANGS[lang][1]:
        t = time.perf_counter()
        p = subprocess.run(LANGS[lang][1](d), cwd=d, env=env(d), capture_output=True, text=True)
        info["build_s"] = round(time.perf_counter() - t, 2)
        if p.returncode != 0:
            return d, {"ok": False, "error": "build failed", "build_log": (p.stdout + p.stderr)[-1500:]}
        info["binary_kb"] = (d / Path(LANGS[lang][2](d)[0]).name).stat().st_size // 1024
    return d, info

def main():
    agents = sys.argv[1:] or ["claude-sonnet", "codex", "gemini", "claude-opus"]
    WORK.mkdir(exist_ok=True)
    subprocess.run(["clang", "-O2", "-o", WALL, str(HERE / "lib/wall.c")], check=True)
    progs = {}
    for a in agents:
        for lang, (fname, _, _) in LANGS.items():
            progs[f"{a}_{lang}"] = (lang, HERE / a / fname)
    for n, (lang, src) in REFS.items(): progs[n] = (lang, src)
    res = {"machine": "MacBook Air M1 2020, 8 GB", "load_before": os.getloadavg(), "programs": {}}
    cmds = {}
    for n, (lang, src) in progs.items():
        d, info = prepare(n, lang, src, LANGS[lang][1])
        res["programs"][n] = {"lang": lang, **info}
        if not info["ok"]:
            print(n, "SKIP", info["error"], flush=True); continue
        base = LANGS[lang][2](d)
        tests = []
        for N, G, S, want in TESTS:
            r = run([*base, N, G, S], timeout=600)
            tests.append({"test": f"{N} {G} {Path(S).name}", "want": want, "got": r.get("alive"), "error": r.get("error"),
                          "wall": r.get("wall"), "cpu_s": r.get("cpu_s")})
        res["programs"][n]["tests"] = tests
        res["programs"][n]["correct"] = all(t["got"] == t["want"] for t in tests)
        long = tests[1]
        res["programs"][n]["multithread"] = bool(long["wall"] and long["cpu_s"] and long["cpu_s"] > 1.25 * long["wall"])
        print(n, "correct" if res["programs"][n]["correct"] else "WRONG", [t["got"] for t in tests], flush=True)
        cmds[n] = base
    # timing: interleaved rounds over every program that is correct
    timed = [n for n in cmds if res["programs"][n]["correct"]]
    for n in timed: run([*cmds[n], "512", "200", SEED]); res["programs"][n].update(sim_ms=[], wall=[], wall_2000=[], rss_kb=0)
    for r in range(ROUNDS):
        for n in timed:
            x = run([*cmds[n], "512", "200", SEED])
            p = res["programs"][n]; p["sim_ms"].append(x["sim_ms"]); p["wall"].append(x["wall"]); p["rss_kb"] = max(p["rss_kb"], x["rss_kb"])
        print("round", r + 1, flush=True)
    for r in range(LONG_ROUNDS):
        for n in timed:
            if min(res["programs"][n]["wall"]) > 3: continue
            res["programs"][n]["wall_2000"].append(run([*cmds[n], "512", "2000", SEED])["wall"])
        print("long round", r + 1, flush=True)
    for n in timed:
        p = res["programs"][n]
        p["sim_ms_best"] = min(x for x in p["sim_ms"] if x is not None) if any(x is not None for x in p["sim_ms"]) else None
        p["wall_best"] = min(p["wall"])
        # independent of the program's own timer: 1,800 extra generations cost (wall_2000 - wall_200)
        p["sim_ms_from_wall"] = round((min(p["wall_2000"]) - p["wall_best"]) / 1800 * 200 * 1000, 2) if p["wall_2000"] else None
    res["load_after"] = os.getloadavg()
    (HERE / "results.json").write_text(json.dumps(res, indent=1))
    print(f"\n{'program':24s} {'ok':>3} {'sim ms':>9} {'from wall':>9} {'wall s':>7} {'MB':>6} {'lines':>5} {'thr':>3}")
    for n, p in sorted(res["programs"].items(), key=lambda x: (x[1].get("sim_ms_best") or 1e9)):
        print(f"{n:24s} {'Y' if p.get('correct') else 'N':>3} {p.get('sim_ms_best') or 0:9.2f} {p.get('sim_ms_from_wall') or 0:9.2f} "
              f"{p.get('wall_best') or 0:7.3f} {p.get('rss_kb', 0)/1024:6.1f} {p.get('lines', 0):5d} {'!' if p.get('multithread') or p.get('threads_in_source') else '':>3}")
    print("load", res["load_before"], res["load_after"])

if __name__ == "__main__":
    main()
