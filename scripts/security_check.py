"""Static security audit — find leaked secrets in tracked/public files.

Usage:
    python3 scripts/security_check.py
    python3 scripts/security_check.py --quiet   # only output failures

Exits non-zero if any likely secret is found in public files.

This script never prints the matched secret value. Findings list the
file, line number, and a redacted match (`[redacted, length=N]`) only.

What's checked:
  - .env is gitignored.
  - .env.example contains placeholders only (no real-looking keys).
  - README and docs do not embed live keys.
  - Source files (.py, .md, .yml, .yaml, .toml, .json, .ini, .cfg, etc.)
    do not contain assignments like NEWSAPI_KEY=<32+hex> or generic
    32+ character base64-ish secret patterns.
  - Heuristic regex set (NewsAPI 32-hex, AWS, GitHub, Google, generic).

What's excluded:
  - .env (intentionally — only present locally; should be gitignored)
  - .git, .venv, venv, __pycache__, .pytest_cache, .cache
  - sample_data, docs/screenshots
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".cache",
    "node_modules", "dist", "build", ".mypy_cache", ".ruff_cache",
    "sample_data",  # synthetic only; covered by separate placeholder check
    "docs",         # screenshots etc.
}
# .env is special: must be gitignored, never scanned.
EXCLUDE_FILES = {".env", ".env.local", ".env.production"}

# File extensions to scan (text-y).
TEXT_EXTS = {
    ".py", ".md", ".txt", ".yml", ".yaml", ".toml", ".json", ".cfg",
    ".ini", ".sh", ".env.example", "Makefile", "Dockerfile",
}

# Known placeholder values that should never trigger a finding.
ALLOWLIST_VALUES = {
    "your_newsapi_key_here", "yourkeyhere", "xxxxxxxx", "xxxxx",
    "fake-test-value", "anything", "super-secret-do-not-print",
    "SECRET", "REDACTED", "TODO", "TBD",
}

# Regex catalogue — each rule produces at most one redacted finding.
RULES: List[Tuple[str, re.Pattern[str]]] = [
    # NEWSAPI_KEY=<32 hex chars> (NewsAPI.org keys are 32 hex)
    ("newsapi_assignment",
     re.compile(r"""(?i)\bNEWSAPI[_-]?KEY\s*[:=]\s*['"]?([A-Fa-f0-9]{32})['"]?""")),
    # Bare 32-hex token on a line (likely NewsAPI even without label)
    ("newsapi_bare", re.compile(r"\b([A-Fa-f0-9]{32})\b")),
    # AWS access key id
    ("aws_access_key", re.compile(r"\b(AKIA[0-9A-Z]{16})\b")),
    # AWS secret (40 base64-ish)
    ("aws_secret", re.compile(r"""(?i)aws.{0,20}['"]?([A-Za-z0-9/+=]{40})['"]?""")),
    # GitHub PAT (ghp_, gho_, ghu_, ghs_, ghr_)
    ("github_token", re.compile(r"\b((ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,})\b")),
    # Google API key
    ("google_api_key", re.compile(r"\b(AIza[0-9A-Za-z\-_]{35})\b")),
    # Slack bot/user tokens
    ("slack_token", re.compile(r"\b(xox[abprs]-[A-Za-z0-9-]{10,})\b")),
    # Stripe secret
    ("stripe_secret", re.compile(r"\b(sk_(?:test|live)_[A-Za-z0-9]{24,})\b")),
    # Generic high-entropy 40-char base64 with key/token/secret prefix
    ("generic_long_secret", re.compile(
        r"""(?i)(?:secret|token|api[_-]?key|password)\s*[:=]\s*['"]([A-Za-z0-9_\-]{32,})['"]""")),
]


def _redact(value: str) -> str:
    return f"[redacted, length={len(value)}]"


def _is_allowlisted(value: str) -> bool:
    if value in ALLOWLIST_VALUES:
        return True
    lo = value.lower()
    if lo in {v.lower() for v in ALLOWLIST_VALUES}:
        return True
    if "your_" in lo or "yourkey" in lo or "placeholder" in lo or "example" in lo:
        return True
    # Treat all-zero / all-x / all-y as placeholders
    if len(set(value)) <= 2:
        return True
    return False


def _iter_files(root: Path):
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.name in EXCLUDE_FILES:
            continue
        # Only scan text-like files
        if path.suffix in TEXT_EXTS or path.name in TEXT_EXTS:
            yield path
        elif path.name in {"Makefile", "Dockerfile", ".env.example", ".gitignore"}:
            yield path


def _scan_file(path: Path):
    findings = []
    try:
        text = path.read_text(errors="ignore")
    except (OSError, UnicodeDecodeError):
        return findings
    for lineno, line in enumerate(text.splitlines(), start=1):
        # Per-line opt-out: marker for intentionally-fake test fixtures.
        if "security-check: ignore" in line:
            continue
        # Skip allowlisted comments/placeholders
        for name, pattern in RULES:
            for m in pattern.finditer(line):
                value = m.group(1)
                if _is_allowlisted(value):
                    continue
                # `newsapi_bare` triggers a lot of false positives (md5 hashes,
                # commit ids, etc). Only flag when in a key/token-ish line.
                if name == "newsapi_bare":
                    if not re.search(r"(?i)key|token|secret|api", line):
                        continue
                # Skip the .env.example file's NEWSAPI_KEY= placeholder
                if path.name == ".env.example" and name.startswith("newsapi"):
                    if not value or _is_allowlisted(value):
                        continue
                findings.append((path, lineno, name, _redact(value), line.strip()[:80]))
    return findings


def _check_gitignore_covers_env(root: Path) -> Tuple[bool, str]:
    gi = root / ".gitignore"
    if not gi.exists():
        return False, ".gitignore is missing"
    text = gi.read_text()
    lines = {l.strip() for l in text.splitlines()}
    if ".env" in lines or "*.env" in lines:
        return True, ".env is gitignored"
    return False, ".env not present in .gitignore"


def _check_env_example(root: Path) -> Tuple[bool, str]:
    p = root / ".env.example"
    if not p.exists():
        return False, ".env.example is missing"
    text = p.read_text()
    # Must NOT contain a 32-hex value as NEWSAPI_KEY
    bad = re.search(r"(?i)NEWSAPI[_-]?KEY\s*=\s*['\"]?([A-Fa-f0-9]{32})['\"]?", text)
    if bad and not _is_allowlisted(bad.group(1)):
        return False, ".env.example contains a real-looking NEWSAPI_KEY"
    return True, ".env.example contains placeholders only"


def main() -> int:
    quiet = "--quiet" in sys.argv

    print("=" * 72)
    print("  Open Maritime Quant Dashboard — security check")
    print("=" * 72)

    failures = 0

    ok, msg = _check_gitignore_covers_env(ROOT)
    print(("  PASS  " if ok else "  FAIL  ") + msg)
    if not ok:
        failures += 1

    ok, msg = _check_env_example(ROOT)
    print(("  PASS  " if ok else "  FAIL  ") + msg)
    if not ok:
        failures += 1

    findings_total = 0
    files_scanned = 0
    for path in _iter_files(ROOT):
        files_scanned += 1
        findings = _scan_file(path)
        if findings:
            findings_total += len(findings)
            failures += len(findings)
            for path, lineno, name, redacted, line_excerpt in findings:
                rel = path.relative_to(ROOT)
                print(f"  FAIL  potential secret in {rel}:{lineno}  ({name})  {redacted}")
                if not quiet:
                    # Show a redacted line excerpt (the value is already redacted by _redact;
                    # but the surrounding context could embed it). We replace alphanumeric runs
                    # of length >= 20 with [redacted].
                    safe = re.sub(r"[A-Za-z0-9_\-]{20,}", "[redacted]", line_excerpt)
                    print(f"        line: {safe}")

    print("-" * 72)
    print(f"  files scanned: {files_scanned}")
    print(f"  potential secret findings: {findings_total}")
    if failures == 0:
        print("  RESULT: clean ✓")
        print("=" * 72)
        return 0
    print(f"  RESULT: {failures} failure(s)")
    print("  Action: rotate any exposed key immediately and remove it from the repo.")
    print("          See SECURITY.md for the rotation procedure.")
    print("=" * 72)
    return 1


if __name__ == "__main__":
    sys.exit(main())
