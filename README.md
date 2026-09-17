# AI Skin Analysis — Streamlit

A Streamlit app for selfie-based skin analysis with the same mobile-first visual style as the `skinscan` project.

## UI

The app now follows the SkinScan flow:

```text
Camera / Upload
      ↓
Guidance cards
Lighting · Look Straight · Face Position
      ↓
Analyze Skin
      ↓
Full-screen scanning animation
      ↓
Face result + detection overlay
      ↓
Right-side concern legend
      ↓
Horizontal circular score rail
```

The result rail is interactive: tap a concern score to switch the displayed detection map and legend.

The reliable built-in Streamlit camera is kept instead of a custom browser camera component, so photo capture and the Analyze Skin button remain simple and stable.

## Features

- Built-in Streamlit camera capture
- Image upload fallback
- SkinScan-style black mobile camera interface
- Standard and HD analysis modes
- Scanning-line animation while the API runs
- Full-face result viewer
- Interactive circular skin-concern scores
- Detection overlays when result masks are returned
- Server-side API key only
- Clear API/network error messages

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Configure the API key

Copy:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Then set:

```toml
SKIN_API_KEY = "YOUR_API_KEY"
```

For Railway or another host:

```text
SKIN_API_KEY=YOUR_API_KEY
```

Never commit the real key.

## Files

- `streamlit_app.py` — capture, scan animation, API flow and UI styling
- `src/result_component.py` — interactive SkinScan-style result viewer
- `src/skin_api.py` — API upload, task creation and polling
- `.streamlit/secrets.toml.example` — safe secret template
- `Dockerfile` — container/Railway deployment
- `test_api.py` — basic parser/action tests

## Notes

The app displays cosmetic image-analysis outputs. It is not a medical diagnosis.
