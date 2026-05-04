"""Setup doctor — diagnose a fresh clone or a broken environment.

Run from the repo root:
    python3 scripts/doctor.py

Output: PASS / WARN / FAIL table + summary + next steps.
Never prints API key values.
"""
from __future__ import annotations

import importlib
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Check primitives
# ---------------------------------------------------------------------------
PASS, WARN, FAIL = "PASS", "WARN", "FAIL"
Result = Tuple[str, str, str]   # (status, name, detail)


def _file(p: Path, name: str) -> Result:
    return (PASS, name, str(p)) if p.exists() else (FAIL, name, f"missing: {p}")


def _check_python() -> Result:
    v = sys.version_info
    if v.major == 3 and v.minor >= 11:
        return (PASS, "python", f"{v.major}.{v.minor}.{v.micro}")
    if v.major == 3 and v.minor >= 9:
        return (WARN, "python", f"{v.major}.{v.minor} (3.11+ recommended)")
    return (FAIL, "python", f"{v.major}.{v.minor} (need 3.9+)")


def _check_cwd() -> Result:
    return (PASS, "cwd", str(Path.cwd()))


def _check_required_files() -> List[Result]:
    needed = [
        "dashboard.py", "maritime_data.py", "config.py", "providers.py",
        "indicators.py", "signals.py", "backtest.py", "demo_data.py",
        "route_economics.py", "requirements.txt", ".env.example",
        ".gitignore", "README.md", "LICENSE",
    ]
    return [_file(ROOT / f, f"file:{f}") for f in needed]


def _check_imports() -> List[Result]:
    out: List[Result] = []
    for mod in ["streamlit", "pandas", "numpy", "yfinance", "requests",
                "vaderSentiment", "plotly", "pytest"]:
        try:
            m = importlib.import_module(mod)
            ver = getattr(m, "__version__", "?")
            out.append((PASS, f"import:{mod}", f"v{ver}"))
        except Exception as exc:  # noqa: BLE001
            out.append((FAIL, f"import:{mod}", f"{type(exc).__name__}"))
    return out


def _check_env() -> List[Result]:
    out: List[Result] = []
    env = ROOT / ".env"
    out.append((PASS if env.exists() else WARN, "file:.env",
                "present" if env.exists() else "absent (demo mode will be used)"))
    # Permissions on POSIX — should not be world-readable
    if env.exists() and os.name == "posix":
        try:
            mode = oct(env.stat().st_mode & 0o777)
            other = int(mode[-1])
            if other == 0:
                out.append((PASS, ".env permissions", mode))
            else:
                out.append((WARN, ".env permissions",
                            f"{mode} (consider chmod 600 .env to restrict)"))
        except OSError as exc:
            out.append((WARN, ".env permissions", str(exc)))

    # NEWSAPI_KEY presence — boolean only, never the value
    has_key = bool(os.environ.get("NEWSAPI_KEY", "").strip())
    if not has_key and env.exists():
        try:
            for line in env.read_text().splitlines():
                if line.strip().startswith("NEWSAPI_KEY") and "=" in line:
                    _, v = line.split("=", 1)
                    if v.strip().strip('"').strip("'"):
                        has_key = True
                        break
        except OSError:
            pass
    out.append((PASS if has_key else WARN, "NEWSAPI_KEY",
                "detected" if has_key else "NOT set (demo mode will run)"))

    # .gitignore covers .env
    gi = ROOT / ".gitignore"
    if gi.exists():
        text = gi.read_text()
        ok = ".env" in text.splitlines() or "\n.env\n" in text or text.startswith(".env")
        out.append((PASS if ok else FAIL, ".gitignore covers .env",
                    "yes" if ok else "FIX: add `.env` to .gitignore"))
    return out


def _check_git() -> List[Result]:
    out: List[Result] = []
    project_git = ROOT / ".git"
    out.append((PASS if project_git.exists() else WARN, "project .git",
                "initialised" if project_git.exists() else "not initialised — `git init` once parent .git issue is fixed"))

    # Walk upward to detect an invalid parent .git file (the known gotcha
    # at /Users/bentheboii/.git on this machine).
    bad: List[str] = []
    for parent in ROOT.parents:
        candidate = parent / ".git"
        if candidate.exists() and candidate.is_file():
            try:
                size = candidate.stat().st_size
                if size == 0:
                    bad.append(f"{candidate} (zero-byte file — invalid)")
                else:
                    # gitlinks are valid (used by submodules); just flag for awareness.
                    text = candidate.read_text(errors="ignore")[:64]
                    if not text.startswith("gitdir:"):
                        bad.append(f"{candidate} (invalid file, not a gitlink)")
            except OSError:
                bad.append(f"{candidate} (unreadable)")
    if bad:
        out.append((WARN, "parent .git files", "; ".join(bad)
                    + "  → see README 'Git troubleshooting' for the safe fix."))
    else:
        out.append((PASS, "parent .git files", "none found above project root"))
    return out


def _check_sample_data() -> List[Result]:
    out: List[Result] = []
    for p, label in [
        (ROOT / "sample_data" / "watchlist.json", "sample_data/watchlist.json"),
        (ROOT / "sample_data" / "fundamentals.json", "sample_data/fundamentals.json"),
        (ROOT / "sample_data" / "news.json", "sample_data/news.json"),
        (ROOT / "sample_data" / "prices" / "BDRY.csv", "sample_data/prices/BDRY.csv"),
        (ROOT / "sample_data" / "route_scenarios" / "may_2026_vlcc_pg_singapore.json",
         "sample_data/route_scenarios/may_2026_vlcc_pg_singapore.json"),
    ]:
        out.append(_file(p, label))
    return out


def _check_port(port: int = 8501) -> Result:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        try:
            sock.bind(("127.0.0.1", port))
            return (PASS, f"port {port}", "available")
        except OSError:
            return (WARN, f"port {port}", "in use — launcher will pick the next free port")


def _check_app_imports() -> List[Result]:
    out: List[Result] = []
    for mod in ["config", "providers", "maritime_data", "indicators",
                "signals", "backtest", "demo_data", "route_economics"]:
        try:
            importlib.import_module(mod)
            out.append((PASS, f"app:{mod}", "imports cleanly"))
        except Exception as exc:  # noqa: BLE001
            out.append((FAIL, f"app:{mod}", f"{type(exc).__name__}: {exc}"))
    return out


# ---------------------------------------------------------------------------
# Reporter
# ---------------------------------------------------------------------------
COLORS = {PASS: "\033[32m", WARN: "\033[33m", FAIL: "\033[31m", "RESET": "\033[0m"}


def _fmt(status: str) -> str:
    return f"{COLORS[status]}{status:<4}{COLORS['RESET']}" if sys.stdout.isatty() else status


def main() -> int:
    print("=" * 72)
    print("  Open Maritime Quant Dashboard — setup doctor")
    print("=" * 72)

    results: List[Result] = []
    results.append(_check_python())
    results.append(_check_cwd())
    results.extend(_check_required_files())
    results.extend(_check_app_imports())
    results.extend(_check_imports())
    results.extend(_check_env())
    results.extend(_check_git())
    results.extend(_check_sample_data())
    results.append(_check_port(8501))

    fails = sum(1 for s, *_ in results if s == FAIL)
    warns = sum(1 for s, *_ in results if s == WARN)

    width = max(len(name) for _, name, _ in results) + 2
    for status, name, detail in results:
        print(f"  {_fmt(status)}  {name:<{width}} {detail}")

    print("-" * 72)
    summary = f"  {fails} FAIL · {warns} WARN · {len(results) - fails - warns} PASS"
    print(summary)

    next_steps: List[str] = []
    if fails:
        next_steps.append("Resolve FAIL rows above before running the app.")
    if any(s == FAIL and n.startswith("import:") for s, n, _ in results):
        next_steps.append("Install dependencies:  pip install -r requirements.txt")
    if any(s == WARN and n == "NEWSAPI_KEY" for s, n, _ in results):
        next_steps.append("Run public demo (no key):  APP_MODE=demo python3 -m streamlit run dashboard.py")
        next_steps.append("Or copy .env.example to .env and add NEWSAPI_KEY for live mode.")
    if any(s == WARN and n == "parent .git files" for s, n, _ in results):
        next_steps.append(
            "Parent .git issue:  ls -la /Users/$USER/.git && file /Users/$USER/.git\n"
            "       If it is a zero-byte file:  mv /Users/$USER/.git /Users/$USER/.git.bak\n"
            "       Then in this directory:  git init && git add . && git commit -m 'Initial'"
        )
    if any(s == WARN and n == "project .git" for s, n, _ in results):
        next_steps.append("Initialise version control once the parent .git issue is fixed: git init")

    if next_steps:
        print("\n  Next steps:")
        for s in next_steps:
            print(f"    • {s}")
    else:
        print("\n  All green. Run:  python3 launcher.py")
    print("=" * 72)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
