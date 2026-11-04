#!/usr/bin/env python3
"""One agent, one prompt, six languages. Runs the agent in its own folder inside sandbox.sb (it cannot
read ~/Developer, ~/Desktop, ~/.ssh, ~/.config or the other runs), with only the commands it needs.
  python3 run_agent.py claude|codex|gemini [--minutes 60]
Writes ~/.cache/agent-runs/<agent>/ and copies the result to runs/<agent>/ when done.
Versions used in the video: Claude Code 2.1.314/2.1.317 (claude-sonnet-5-5; CLAUDE_MODEL=claude-opus-5-5 RUN_NAME=claude-opus for the Opus run), Codex CLI 0.154 (gpt-5.6-terra),
Antigravity CLI (gemini-3.8-flash-high). Set CLAUDE to your claude binary if it is not on PATH."""
import json, os, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
H = Path.home()
agent = sys.argv[1]
minutes = int(sys.argv[sys.argv.index("--minutes") + 1]) if "--minutes" in sys.argv else 60
prompt = (HERE / "PROMPT.txt").read_text().strip()
run_name = os.environ.get("RUN_NAME", agent)
run = H / ".cache/agent-runs" / run_name
shutil.rmtree(run, ignore_errors=True)
(run / ".tmp").mkdir(parents=True)
shutil.copy(HERE / "seed/start_512.txt", run)
SB = ["sandbox-exec", "-D", f"HOME={H}", "-f", str(HERE / "sandbox.sb")]
CLAUDE = os.environ.get("CLAUDE", "claude")
TOOLS = "Read Write Edit Glob Grep " + " ".join(f"Bash({c}:*)" for c in
        ["clang", "rustc", "go", "zig", "python3", "node", "./life_c", "./life_rs", "./life_go", "./life_zig", "ls", "cat", "time", "diff", "wc", "rm", "mkdir"])
# agy ends the whole run at the first command it may not run (3 Nov, 14 s run), so it gets the harmless
# shell utilities too; file access is still limited by sandbox.sb
CMDS = ["clang", "rustc", "go", "zig", "python3", "node", "./life_c", "./life_rs", "./life_go", "./life_zig", "ls", "cat", "time", "diff",
        "wc", "rm", "mkdir", "head", "tail", "cut", "grep", "sed", "awk", "echo", "printf", "sort", "uniq", "tr", "cmp", "md5", "shasum",
        "mv", "cp", "touch", "file", "which", "pwd", "true", "test", "env", "for", "cd", "/usr/bin/time", "hyperfine", "sleep", "xxd", "od"]
# naming commands one by one did not work for agy either (it then called /usr/bin/head and stopped), so Gemini may run any
# command, but inside sandbox-strict.sb: it can only write into its run folder and its own state, and cannot read the rest
AGY = json.dumps({"permissions": {"allow": [f"write_file({run})", f"read_file({run})", "command(*)"]}})
SB_GEMINI = ["sandbox-exec", "-D", f"HOME={H}", "-D", f"RUN={run}", "-f", str(HERE / "sandbox-strict.sb")]
CMD = {
    "claude": [*SB, str(CLAUDE), "-p", prompt, "--model", os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5"), "--permission-mode", "acceptEdits",
               "--allowedTools", TOOLS, "--output-format", "stream-json", "--verbose"],
    # Codex has its own macOS sandbox (writes only in this folder, no network); it cannot run inside another one
    "codex": ["codex", "exec", "-m", "gpt-5.6-terra", "-s", "workspace-write", "--skip-git-repo-check", "-c", "mcp_servers={}",
              "--color", "never", "--json", "-o", "codex-last.md", prompt],
    "gemini": [*SB_GEMINI, str(H / ".local/bin/agy"), "--print", prompt, "--model", "gemini-3.8-flash-high", "--settings", AGY,
               "--print-timeout", f"{minutes}m", "--output-format", "stream-json", "--disable-slash-commands"],
}[agent]
env = dict(os.environ, PWD=str(run), OLDPWD=str(run), CI="1", TERM="dumb", NO_COLOR="1",
           GOCACHE=str(run / ".cache/go"), ZIG_GLOBAL_CACHE_DIR=str(run / ".cache/zig"), TMPDIR=str(run / ".tmp"),
           PATH=os.environ["PATH"])
t0 = time.time(); timed_out = False
with open(run / "transcript.jsonl", "w") as log:
    try:
        code = subprocess.run(CMD, cwd=run, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                              timeout=minutes * 60, text=True).returncode
    except subprocess.TimeoutExpired:
        timed_out, code = True, -1
meta = {"agent": agent, "model": {"claude": os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5"), "codex": "gpt-5.6-terra", "gemini": "gemini-3.8-flash-high"}[agent],
        "seconds": round(time.time() - t0), "exit_code": code, "timed_out": timed_out,
        "started": time.strftime("%Y-%m-%d %H:%M", time.localtime(t0))}
(run / "meta.json").write_text(json.dumps(meta, indent=1))
print(json.dumps(meta), flush=True)
keep = HERE / "runs" / run_name
shutil.rmtree(keep, ignore_errors=True)
shutil.copytree(run, keep, ignore=shutil.ignore_patterns(".cache", ".tmp", "__pycache__", "life_c", "life_rs", "life_go", "life_zig"))
