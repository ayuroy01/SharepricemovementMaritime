# Screenshots

The README references images at:

- `docs/screenshots/overview.png`
- `docs/screenshots/vlcc-route-lab.png`

If those files don't exist yet (clean repo, before first capture), the
README falls back to text. To capture them yourself:

## Capture workflow

```bash
# 1. Install if you haven't yet
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Start in demo mode (no API key required)
APP_MODE=demo python3 -m streamlit run dashboard.py
# or:  make run-demo
# or:  python3 launcher.py  → "Run Demo"
```

Open <http://localhost:8501> and capture:

| Image                                  | Tab                  | Recommended size      |
|----------------------------------------|----------------------|-----------------------|
| `overview.png`                         | 📊 Overview          | 1600×1000 (or 2× HiDPI) |
| `vlcc-route-lab.png`                   | 🛳️ VLCC Route Lab → Cost Breakdown | 1600×1000             |
| `data-health.png` *(optional)*         | 🩺 Data Health       | 1600×1000             |

### macOS

- Full window:  `Cmd-Shift-4`, then `Space`, then click the browser window.
- Region:       `Cmd-Shift-4`, drag.

### Linux

- `gnome-screenshot -w` (window) or `-a` (area).
- `import` (ImageMagick) for command-line capture.

### Windows

- `Win-Shift-S` then save.

## Privacy / safety

- Run in **demo mode** so the URL bar and content show only synthetic
  data. The bundled fixtures contain only fictional headlines and
  generated prices.
- Crop or blur anything that includes real ticker data if you took the
  screenshot in live mode.
- The dashboard **never** displays a NewsAPI key value. If your
  screenshot somehow includes the value of an env var, scrub it before
  committing.

## Saving

Save under `docs/screenshots/`. Use lower-case kebab-case filenames.
PNG preferred (smaller for the simple charts; lossless for tables).
Aim for ≤ 500 KB each — Streamlit charts compress well at PNG-8 quality.
