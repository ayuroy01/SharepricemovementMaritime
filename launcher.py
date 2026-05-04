"""Open Maritime Quant Dashboard — local launcher.

Cross-platform:
  - Tkinter GUI when available (tk is in the Python stdlib on macOS/Linux/Windows).
  - Falls back to a numbered terminal menu when tk is unavailable
    (e.g. minimal Linux installs or remote shells).

Usage:
  python3 launcher.py
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
DEFAULT_PORT = 8501


# ---------------------------------------------------------------------------
# Helpers (no secrets are ever printed)
# ---------------------------------------------------------------------------
def newsapi_key_present() -> bool:
    """Boolean check only. NEVER returns the value."""
    val = os.environ.get("NEWSAPI_KEY", "").strip()
    if val:
        return True
    env_path = ROOT / ".env"
    if not env_path.exists():
        return False
    try:
        for raw in env_path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == "NEWSAPI_KEY" and v.strip().strip('"').strip("'"):
                return True
    except OSError:
        return False
    return False


def detected_mode() -> str:
    """What mode the app would resolve to right now (without imports)."""
    explicit = os.environ.get("APP_MODE", "").strip().lower()
    if explicit in {"demo", "live"}:
        return explicit.upper()
    if explicit == "auto" or not explicit:
        return "LIVE" if newsapi_key_present() else "DEMO"
    return "AUTO"


def port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
        return True


def find_free_port(start: int = DEFAULT_PORT) -> int:
    p = start
    for _ in range(20):
        if port_available(p):
            return p
        p += 1
    return start  # give up; caller handles


def launch_streamlit(mode: str, port: int) -> subprocess.Popen:
    """Spawn streamlit in a subprocess. Inherits env vars except APP_MODE override."""
    env = os.environ.copy()
    if mode in {"demo", "live", "auto"}:
        env["APP_MODE"] = mode
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(ROOT / "dashboard.py"),
        "--server.port", str(port), "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ]
    return subprocess.Popen(cmd, cwd=ROOT, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            bufsize=1, text=True)


# ---------------------------------------------------------------------------
# Terminal fallback
# ---------------------------------------------------------------------------
def run_terminal() -> int:
    print("=" * 60)
    print("  Open Maritime Quant Dashboard — launcher (terminal mode)")
    print("=" * 60)
    print(f"  Detected mode      : {detected_mode()}")
    print(f"  NewsAPI key        : {'detected' if newsapi_key_present() else 'NOT set (demo mode will run)'}")
    print(f"  Working directory  : {ROOT}")
    print()

    options = [
        ("Run in DEMO mode (no keys, no network)", lambda: _run("demo")),
        ("Run in LIVE mode (yfinance + NewsAPI)", lambda: _run("live")),
        ("Run in AUTO mode (live if key present, else demo)", lambda: _run("auto")),
        ("Run smoke test (demo)", lambda: _exec([sys.executable, "scripts/smoke_test.py"], env={"APP_MODE": "demo"})),
        ("Run test suite (pytest)", lambda: _exec([sys.executable, "-m", "pytest", "-q"])),
        ("Run setup doctor", lambda: _exec([sys.executable, "scripts/doctor.py"])),
        ("Run security check", lambda: _exec([sys.executable, "scripts/security_check.py"])),
        ("Open README in default app", lambda: _open(ROOT / "README.md")),
        ("Open localhost:8501 in browser", lambda: webbrowser.open(f"http://localhost:{DEFAULT_PORT}")),
        ("Exit", None),
    ]

    while True:
        print("\nOptions:")
        for i, (label, _) in enumerate(options, 1):
            print(f"  {i:2d}. {label}")
        choice = input("\nChoose: ").strip()
        if not choice.isdigit():
            print("  ↳ please enter a number")
            continue
        idx = int(choice)
        if idx < 1 or idx > len(options):
            print("  ↳ out of range")
            continue
        label, action = options[idx - 1]
        if action is None:
            print("  bye")
            return 0
        print(f"\n  ↳ {label}")
        action()


def _run(mode: str) -> None:
    port = find_free_port(DEFAULT_PORT)
    if port != DEFAULT_PORT:
        print(f"  port {DEFAULT_PORT} busy; using {port}")
    print(f"  starting streamlit (APP_MODE={mode}, port={port})…")
    proc = launch_streamlit(mode, port)
    url = f"http://localhost:{port}"
    # wait up to ~10s for the server then open
    for _ in range(20):
        time.sleep(0.5)
        if not port_available(port):  # something is listening
            break
    print(f"  open: {url}")
    try:
        webbrowser.open(url)
    except Exception:  # noqa: BLE001
        pass
    print("  Press Ctrl-C to stop the server and return to the menu.")
    try:
        for line in proc.stdout:  # type: ignore[union-attr]
            sys.stdout.write(line)
    except KeyboardInterrupt:
        print("\n  stopping streamlit…")
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:  # noqa: BLE001
            proc.kill()


def _exec(cmd: list[str], env: Optional[dict] = None) -> None:
    e = os.environ.copy()
    if env:
        e.update(env)
    rc = subprocess.run(cmd, cwd=ROOT, env=e).returncode
    print(f"  exit code: {rc}")


def _open(path: Path) -> None:
    if not path.exists():
        print(f"  not found: {path}")
        return
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", str(path)])
        elif sys.platform.startswith("linux"):
            subprocess.run(["xdg-open", str(path)])
        elif sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            print(f"  open manually: {path}")
    except Exception as exc:  # noqa: BLE001
        print(f"  could not open ({exc}); path: {path}")


# ---------------------------------------------------------------------------
# Tkinter GUI (preferred when available)
# ---------------------------------------------------------------------------
def run_gui() -> int:
    import tkinter as tk
    from tkinter import scrolledtext, ttk

    state = {"proc": None, "port": DEFAULT_PORT, "thread": None}

    root = tk.Tk()
    root.title("Open Maritime Quant Dashboard")
    root.geometry("780x560")
    root.minsize(640, 480)

    style = ttk.Style()
    if "aqua" in style.theme_names():
        style.theme_use("aqua")
    elif "clam" in style.theme_names():
        style.theme_use("clam")

    # --- header
    header = ttk.Frame(root, padding=(16, 12, 16, 8))
    header.pack(fill="x")
    ttk.Label(header, text="🚢  Open Maritime Quant Dashboard",
              font=("Helvetica", 16, "bold")).pack(side="left")

    info = ttk.Frame(root, padding=(16, 0, 16, 8))
    info.pack(fill="x")
    mode_var = tk.StringVar(value=f"Detected mode: {detected_mode()}")
    key_var = tk.StringVar(
        value=f"NewsAPI key: {'detected' if newsapi_key_present() else 'NOT set (demo mode will run)'}"
    )
    ttk.Label(info, textvariable=mode_var).pack(anchor="w")
    ttk.Label(info, textvariable=key_var).pack(anchor="w")

    # --- controls
    ctrls = ttk.Frame(root, padding=(16, 4, 16, 8))
    ctrls.pack(fill="x")
    ttk.Label(ctrls, text="Port:").pack(side="left")
    port_var = tk.IntVar(value=DEFAULT_PORT)
    port_entry = ttk.Spinbox(ctrls, from_=1024, to=65535, width=8, textvariable=port_var)
    port_entry.pack(side="left", padx=(6, 16))

    status_var = tk.StringVar(value="idle")
    ttk.Label(ctrls, textvariable=status_var, foreground="#0277bd").pack(side="right")

    # --- log
    log = scrolledtext.ScrolledText(root, height=18, font=("Menlo", 11),
                                    state="disabled", bg="#0e0e10", fg="#e3e3e3")
    log.pack(fill="both", expand=True, padx=16, pady=(4, 8))

    def append_log(text: str) -> None:
        log.configure(state="normal")
        log.insert("end", text)
        log.see("end")
        log.configure(state="disabled")

    # --- subprocess management
    def start(mode: str) -> None:
        if state["proc"] and state["proc"].poll() is None:
            append_log("[launcher] already running — stop first.\n")
            return
        port = int(port_var.get() or DEFAULT_PORT)
        if not port_available(port):
            new_port = find_free_port(port)
            append_log(f"[launcher] port {port} busy; using {new_port}\n")
            port = new_port
            port_var.set(port)
        state["port"] = port
        append_log(f"[launcher] starting streamlit  APP_MODE={mode}  port={port}\n")
        try:
            proc = launch_streamlit(mode, port)
        except FileNotFoundError as exc:
            append_log(f"[launcher] failed to start: {exc}\n")
            return
        state["proc"] = proc
        status_var.set(f"running ({mode}, :{port})")
        mode_var.set(f"Detected mode: {mode.upper()}  ·  running on port {port}")

        def reader() -> None:
            try:
                for line in proc.stdout:  # type: ignore[union-attr]
                    root.after(0, append_log, line)
            except Exception:  # noqa: BLE001
                pass
            root.after(0, status_var.set, "stopped")

        t = threading.Thread(target=reader, daemon=True)
        t.start()
        state["thread"] = t

        def open_when_ready() -> None:
            for _ in range(30):
                if not port_available(port):
                    webbrowser.open(f"http://localhost:{port}")
                    return
                time.sleep(0.4)
        threading.Thread(target=open_when_ready, daemon=True).start()

    def stop() -> None:
        proc = state["proc"]
        if proc and proc.poll() is None:
            append_log("[launcher] stopping streamlit…\n")
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:  # noqa: BLE001
                proc.kill()
        status_var.set("idle")

    def open_browser() -> None:
        webbrowser.open(f"http://localhost:{state['port']}")

    def open_readme() -> None:
        _open(ROOT / "README.md")

    def run_doctor() -> None:
        append_log("[launcher] running scripts/doctor.py …\n")
        threading.Thread(target=lambda: _stream_cmd([sys.executable, "scripts/doctor.py"], append_log),
                         daemon=True).start()

    def run_security() -> None:
        append_log("[launcher] running scripts/security_check.py …\n")
        threading.Thread(target=lambda: _stream_cmd([sys.executable, "scripts/security_check.py"], append_log),
                         daemon=True).start()

    def run_tests() -> None:
        append_log("[launcher] running pytest -q …\n")
        threading.Thread(target=lambda: _stream_cmd([sys.executable, "-m", "pytest", "-q"], append_log),
                         daemon=True).start()

    def run_smoke() -> None:
        append_log("[launcher] running scripts/smoke_test.py (demo) …\n")
        threading.Thread(target=lambda: _stream_cmd(
            [sys.executable, "scripts/smoke_test.py"], append_log,
            env={"APP_MODE": "demo"},
        ), daemon=True).start()

    # --- buttons
    btns = ttk.Frame(root, padding=(16, 0, 16, 12))
    btns.pack(fill="x")

    def _btn(label: str, cmd) -> ttk.Button:
        b = ttk.Button(btns, text=label, command=cmd)
        return b

    _btn("Run Demo",  lambda: start("demo")).grid(row=0, column=0, padx=4, pady=4, sticky="ew")
    _btn("Run Live",  lambda: start("live")).grid(row=0, column=1, padx=4, pady=4, sticky="ew")
    _btn("Run Auto",  lambda: start("auto")).grid(row=0, column=2, padx=4, pady=4, sticky="ew")
    _btn("Stop",      stop).grid(row=0, column=3, padx=4, pady=4, sticky="ew")
    _btn("Open localhost", open_browser).grid(row=0, column=4, padx=4, pady=4, sticky="ew")

    _btn("Smoke test", run_smoke).grid(row=1, column=0, padx=4, pady=4, sticky="ew")
    _btn("Run tests",  run_tests).grid(row=1, column=1, padx=4, pady=4, sticky="ew")
    _btn("Doctor",     run_doctor).grid(row=1, column=2, padx=4, pady=4, sticky="ew")
    _btn("Security",   run_security).grid(row=1, column=3, padx=4, pady=4, sticky="ew")
    _btn("Open README", open_readme).grid(row=1, column=4, padx=4, pady=4, sticky="ew")

    for i in range(5):
        btns.columnconfigure(i, weight=1)

    # --- footer
    foot = ttk.Frame(root, padding=(16, 0, 16, 12))
    foot.pack(fill="x")
    ttk.Label(foot, text="Tip: leave NewsAPI key blank to run as a public demo.",
              foreground="#666").pack(side="left")
    ttk.Button(foot, text="Quit", command=lambda: (stop(), root.destroy())).pack(side="right")

    def on_close() -> None:
        stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
    return 0


def _stream_cmd(cmd: list[str], log_fn, env: Optional[dict] = None) -> None:
    e = os.environ.copy()
    if env:
        e.update(env)
    proc = subprocess.Popen(cmd, cwd=ROOT, env=e,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            bufsize=1, text=True)
    try:
        for line in proc.stdout:  # type: ignore[union-attr]
            log_fn(line)
    except Exception as exc:  # noqa: BLE001
        log_fn(f"[launcher] error: {exc}\n")
    proc.wait()
    log_fn(f"[launcher] exit {proc.returncode}\n")


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------
def main() -> int:
    if "--terminal" in sys.argv or "--no-gui" in sys.argv or os.environ.get("LAUNCHER_TERMINAL"):
        return run_terminal()
    try:
        import tkinter  # noqa: F401
    except Exception:  # noqa: BLE001
        return run_terminal()
    try:
        return run_gui()
    except Exception as exc:  # noqa: BLE001
        # tkinter may import but fail to display (headless / no DISPLAY)
        print(f"[launcher] GUI unavailable ({exc}); falling back to terminal.")
        return run_terminal()


if __name__ == "__main__":
    sys.exit(main())
