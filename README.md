# AI Skin Analysis — Streamlit

A simple Streamlit app for selfie-based skin analysis.

## Features

- Built-in Streamlit camera capture
- Image upload fallback
- Standard and HD analysis modes
- Skin concern score cards
- Detection-mask gallery when result images are available
- Clear API and network error messages
- Server-side API key only

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

For Railway or another host, add the environment variable:

```text
SKIN_API_KEY=YOUR_API_KEY
```

Never commit the real key.

## Analysis flow

```text
Camera / Upload
      ↓
File upload API
      ↓
Skin analysis task
      ↓
Task polling
      ↓
Scores + detection maps
      ↓
Streamlit results
```

## Standard mode

Includes the available standard skin concerns such as wrinkles, pores, texture,
acne, oiliness, radiance, eye bags, dark spots, dark circles, firmness,
hydration, redness, tear trough and skin type.

## HD mode

Uses the HD concern set only. Standard and HD concerns are not mixed in the
same request.

## Files

- `streamlit_app.py` — app UI and analysis flow
- `src/skin_api.py` — API upload, task creation and polling
- `.streamlit/secrets.toml.example` — safe secret template
- `Dockerfile` — container/Railway deployment
- `test_api.py` — basic parser/action tests

## Notes

This app displays cosmetic image-analysis outputs. It is not a medical
diagnosis.
