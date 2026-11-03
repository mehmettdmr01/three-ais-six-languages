# Three AIs, six languages, one program

Video: (link coming)

I gave Claude Code, Codex and Gemini the same prompt ([PROMPT.txt](PROMPT.txt)): write Conway's Game of Life
(512×512, wrapping edges, 200 generations) in C, Rust, Go, Zig, Python and JavaScript, as fast as you can.
One prompt, one run each, no help from me. Then I tested every program on sizes the agents never saw and timed
it next to my own versions from the previous video ([same-program-rust-go-zig](https://github.com/mehmettdmr01/same-program-rust-go-zig)).

## Results

Simulation loop only (the program's own `sim_ms`), best of 7 interleaved rounds, Apple M1 (MacBook Air 2020, 8 GB).
**Bold** = faster than mine.

| Language | Mine | Claude Code (Opus 5.5) | Gemini (3.8 Flash) | Codex (GPT-5.6 Terra) |
|---|---|---|---|---|
| C | 6.41 (`ref/c/fast.c`) | **1.33** | **3.00** | 7.68 |
| Rust | 5.32 (`ref/rust/fast.rs`) | **1.42** | **3.00** | 7.41 |
| Go | 23.1 (`ref/go/swar.go`) | **2.85** | **5.00** | 115 |
| Zig | 6.87 (`ref/zig/vector.zig`) | **1.25** | **3.00** | **5.91** |
| Python | 23.2 (`ref/numpy/four_rolls.py`) | **9.45** | **19.0** | 154 |
| JavaScript | 269 (`ref/js/fast.js`) | **13.4** | **27.0** | **162** |

- **All 18 AI programs passed every hidden test** (300×300, 1000×1000 and 64×64 seeds they never saw, plus 2,000 generations at 512).
- **The only program that failed was mine:** `ref/c/bitpacked.c`, which I called the fastest in my last two videos, sets `W = N / 64`,
  so it silently drops the last `N % 64` cells of every row. 300×300: alive=6421 instead of 7791; 1000×1000: 117650 instead of 122523.
  At 512 it is correct (3.35 ms). Claude's and Gemini's bit-packed versions round up (`(N + 63) / 64`) and mask the last word.
- **Claude** kept one bit per cell in all six languages. **Gemini** did too. **Codex** kept one byte per cell with a copied halo,
  close to my own version from the last video.
- **Gemini searched the web twice** although the prompt said "There is no internet"; it searched for the prompt's own sentences.
  The log does not record what came back, and its code does not resemble mine. See [gemini/LOG-EXCERPT.md](gemini/LOG-EXCERPT.md).

## What to keep in mind

- One task, one machine, one run per agent. Models change every month.
- Gemini ran as **3.8 Flash**: the Antigravity CLI I used had no Pro model. Claude ran Opus 5.5, Codex GPT-5.6 Terra (the best model my ChatGPT account allowed in Codex).
- **Gemini's first two runs** stopped after 14 s and about 25 s: the Antigravity CLI ends the whole run at the first command
  that is not on its allow list. The third run allowed every command inside [sandbox-strict.sb](sandbox-strict.sb) (writes only to its own folder).
- The three agents ran **at the same time** on the same 8 GB laptop, so their own timings while working were noisy.
  All numbers above were measured afterwards on an idle machine with [measure.py](measure.py).
- **My JavaScript** (`ref/js/fast.js`) was written for this video, in the same style as my C `fast` version; there was no JavaScript in the last video.
  My Go column is the SWAR version (`ref/go/swar.go`); the plain `fast.go` takes 66.4 ms.
- Gemini prints `sim_ms` in whole milliseconds; the wall-clock estimate in results.json (`sim_ms_from_wall`) agrees (2.7–3.1 ms).
- Python was timed with Python 3.15 and NumPy 2.5.4. With Homebrew's Python 3.13 and NumPy 2.4.0 the same NumPy code ran 5× slower;
  I measured that by mistake first.
- Cost: Claude's run would have cost $2.88 at API prices (12 minutes; it ran on a subscription).
  Codex took 9 minutes and 19k output tokens, Gemini 18 minutes and 95k output tokens.

## Run it

```
python3 measure.py                 # builds everything in build/, runs the hidden tests, times all programs -> results.json
PYTHON=/path/to/python3 python3 measure.py   # the Python used for life.py (needs NumPy)
python3 run_agent.py claude        # rerun one agent (macOS: uses sandbox-exec; needs the agent's CLI and login)
```

Build commands are fixed by the prompt: `clang -O2`, `rustc -C opt-level=3`, `go build`, `zig build-exe -O ReleaseFast` (Zig 0.17), Node 22.

## Files

- `claude/`, `codex/`, `gemini/`: the six files each agent wrote, unedited, and its own NOTES.md
- `ref/`: my versions (C, Rust, Go, Zig and NumPy from the last video; JavaScript written for this one)
- `seed/`: `start_512.txt` (the only seed the agents had) and the hidden seeds (`make_hidden.py`)
- `PROMPT.txt`, `run_agent.py`, `sandbox.sb`, `sandbox-strict.sb`, `measure.py`, `results.json`, `lib/wall.c`

The scripts in this repo were written with Claude Code.
