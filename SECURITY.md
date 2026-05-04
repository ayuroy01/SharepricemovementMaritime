# Security policy

## Reporting a vulnerability

If you find a security issue, please **do not open a public issue**.
Instead, contact the maintainers privately (e.g. via the email listed in
the GitHub project profile, or by opening a private security advisory on
GitHub).

We aim to acknowledge reports within 7 days.

## Secrets handling

This project never reads, prints, logs, or commits API key values.

- All secrets load from environment variables (typically via a local
  `.env` file). `.env` is gitignored.
- The dashboard only ever reports **"NewsAPI key detected"** or
  **"No NewsAPI key set"** — the value is never displayed.
- Provider error messages are sanitised before display (URLs containing
  `apiKey=`, `Authorization`, etc. are redacted).
- For public deployments, supply secrets via the platform's own
  secret store (Streamlit Cloud secrets, Hugging Face Spaces secrets,
  Docker `--env`, Kubernetes secrets, etc.). **Never** bake them into
  an image or commit them.

## If a key is exposed

If a key is accidentally committed or pasted into a chat / log /
screenshot:

1. **Rotate the key immediately** in the provider's dashboard.
2. Force-remove the leaked value from history if possible
   (`git filter-repo`, BFG, or rewriting + force-push) — but treat the
   key as compromised regardless.
3. Audit recent usage on the provider's dashboard for anomalous calls.
4. Update the deployment with the new key via the platform's secret
   store.

## Dependencies

We pin top-level dependencies in `requirements.txt` for reproducibility.
Security-relevant updates (e.g. `requests`, `streamlit`) are merged
promptly when reported. CI runs `pip check` on every push.

## Key rotation procedure (NewsAPI)

If a NewsAPI key has been exposed (in chat, screenshots, terminal logs,
a commit, or a deployed environment):

1. **Rotate immediately** at <https://newsapi.org/account>. Old key
   becomes useless even if attackers already saved it.
2. **Replace it everywhere it was set:** local `.env`, deployment
   secret stores (Streamlit Cloud, Hugging Face Spaces, Docker `--env`,
   Kubernetes, etc.).
3. **Audit recent usage** on the NewsAPI dashboard for unfamiliar
   request volumes or patterns.
4. **If it was committed**, rewrite Git history to remove it
   (`git filter-repo --invert-paths --path .env` or BFG), then
   force-push. Treat the key as compromised regardless — anyone who
   had access to the diff already saw it.
5. **Run the security check** from the repo root to confirm no other
   leaked values remain in tracked files:

```bash
python3 scripts/security_check.py     # or:  make security-check
```

The check exits non-zero if anything is found. Findings include the
file path, line number, and a redacted (`[redacted, length=N]`) marker
— **never** the value itself.

## Deployment secrets

For public deployments:

- **Streamlit Community Cloud** — add `NEWSAPI_KEY` and (optionally)
  `APP_MODE=live` under *App settings → Secrets*. Streamlit injects
  these as env vars at runtime.
- **Hugging Face Spaces** — *Settings → Repository secrets*. Same
  semantics.
- **Docker** — pass via `--env NEWSAPI_KEY=...` or an env-file. **Never**
  bake the key into the image (it lives forever in image layers).
- **Kubernetes / generic** — use the platform's Secret resource and
  mount it as an env var.

The dashboard runs entirely server-side; secrets never reach the
browser. The UI only reports **"NewsAPI key detected"** vs **"No
NewsAPI key set"**.

## Where keys must (and must not) live

**OK:**
- Local `.env` (gitignored).
- Deployment platform secret stores (Streamlit Cloud secrets,
  Hugging Face Spaces secrets, Docker `--env`, Kubernetes Secrets).
- Process environment variables.

**Never:**
- Source code, sample data, tests, fixtures.
- README, CHANGELOG, or any other Markdown.
- GitHub issues, PR descriptions, comments, or commit messages.
- Screenshots, screencasts, or terminal recordings.
- Chat / prompt logs (including AI tools).
- CI logs, build artefacts, container image layers.

If a key shows up in any of these, treat it as **compromised** and
rotate it. Don't try to "scrub history" as a substitute for rotation —
anyone with diff access already saw it.

## Reporting

To report a vulnerability privately, open a
[GitHub security advisory](https://docs.github.com/en/code-security/security-advisories/repository-security-advisories/about-repository-security-advisories)
on this repo. Please don't open a public issue for security topics.
