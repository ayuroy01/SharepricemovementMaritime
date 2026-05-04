"""Tests for scripts/security_check.py.

Verifies the redactor never emits raw secret values and that placeholder
patterns are correctly allowlisted.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "security_check", ROOT / "scripts" / "security_check.py"
)
sec = importlib.util.module_from_spec(SPEC)
sys.modules["security_check"] = sec
SPEC.loader.exec_module(sec)  # type: ignore[union-attr]


def test_redact_never_returns_raw_value():
    val = "0123456789abcdef0123456789abcdef"
    assert val not in sec._redact(val)
    assert "redacted" in sec._redact(val)


def test_placeholder_values_are_allowlisted():
    assert sec._is_allowlisted("your_newsapi_key_here")
    assert sec._is_allowlisted("YOURKEYHERE")
    assert sec._is_allowlisted("xxxxxxxx")
    assert sec._is_allowlisted("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")  # all-same chars
    assert not sec._is_allowlisted("0123456789abcdef0123456789abcdef")


def test_scan_file_flags_obvious_newsapi_assignment(tmp_path):
    # Build a 32-hex string with enough variety to defeat the placeholder
    # allowlist (which collapses repeated/two-char values).
    fake = ("ab12cd34" * 4)  # 32 chars, 6 distinct
    p = tmp_path / "leak.py"
    p.write_text(
        f'NEWSAPI_KEY = "{fake}"\n'
        'OTHER = "harmless"\n'
    )
    findings = sec._scan_file(p)
    assert findings
    # No raw value should appear in the structured tuple — only the redacted form.
    for *_, redacted, line in findings:
        assert fake not in redacted


def test_scan_file_skips_placeholder_env_example(tmp_path):
    p = tmp_path / ".env.example"
    p.write_text("NEWSAPI_KEY=your_newsapi_key_here\nNEWSAPI_KEY=\n")
    findings = sec._scan_file(p)
    assert findings == []


def test_scan_file_ignores_md5_like_text_outside_keylike_lines(tmp_path):
    p = tmp_path / "doc.md"
    p.write_text(
        "Commit hash: 0123456789abcdef0123456789abcdef\n"
    )
    findings = sec._scan_file(p)
    # The bare-hex rule requires key/token/secret/api context
    assert findings == []


def test_check_gitignore_covers_env(tmp_path):
    (tmp_path / ".gitignore").write_text(".env\n.venv\n__pycache__\n")
    ok, _ = sec._check_gitignore_covers_env(tmp_path)
    assert ok


def test_check_gitignore_missing_env(tmp_path):
    (tmp_path / ".gitignore").write_text(".venv\n")
    ok, _ = sec._check_gitignore_covers_env(tmp_path)
    assert not ok


def test_check_env_example_clean(tmp_path):
    (tmp_path / ".env.example").write_text("NEWSAPI_KEY=\nAPP_MODE=auto\n")
    ok, _ = sec._check_env_example(tmp_path)
    assert ok


def test_check_env_example_with_real_looking_key(tmp_path):
    fake = ("ab12cd34" * 4)
    (tmp_path / ".env.example").write_text(f"NEWSAPI_KEY={fake}\n")
    ok, _ = sec._check_env_example(tmp_path)
    assert not ok


def test_placeholder_not_flagged_when_repeated_chars():
    # All-same-char strings are treated as placeholders.
    assert sec._is_allowlisted("1" * 32)
    assert sec._is_allowlisted("0" * 32)


def test_security_check_marker_skips_line():
    """Lines bearing 'security-check: ignore' are skipped entirely."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "leak.py"
        p.write_text(
            f'NEWSAPI_KEY = "{"a" * 32}"  # security-check: ignore (test fixture)\n'
        )
        # Even though the value isn't a placeholder by content, the marker skips it.
        # Use a non-allowlisted value to make sure marker is what's saving us:
        p.write_text(
            'NEWSAPI_KEY = "deadbeefcafebabe1234567890abcdef"  # security-check: ignore\n'
        )
        findings = sec._scan_file(p)
        assert findings == []
