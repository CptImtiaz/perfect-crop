# Perfect Corp Skin Analysis — Streamlit

This project adapts Perfect Corp's camera + skin-analysis workflow to Streamlit.

## Important platform note

Perfect Corp's **native Mobile CameraKit** is for Android/iOS apps.
A Streamlit app runs in a browser, so this project uses the official
**JavaScript Camera Kit v2.5** for camera capture, then the **Skin Analysis
API v2.1** from the Python backend.

## Flow

```text
Perfect Corp JS Camera Kit v2.5
        ↓
guided camera capture
(face / position / frontal / lighting)
        ↓
Streamlit Components v2
        ↓
Python backend
        ↓
POST /s2s/v2.0/file
        ↓
upload to returned signed URL
        ↓
POST /s2s/v2.1/task/skin-analysis
        ↓
poll task status
        ↓
ui_score + raw_score + mask_urls
        ↓
Streamlit cards + mask gallery
```

## Setup

### 1. Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Add your Perfect Corp API key

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml`:

```toml
PERFECTCORP_API_KEY = "YOUR_NEW_PERFECT_CORP_API_KEY"
```

Never commit the real secrets file.

### 3. Run

```bash
streamlit run streamlit_app.py
```

Camera access normally requires HTTPS in production.

## Standard mode

Camera:

```text
faceDetectionMode = skincare
```

API actions use the SD set:
wrinkles, pores, texture, acne, oiliness, radiance, eye bags, dark spots,
dark circles, eyelids, firmness, hydration/moisture, redness, tear trough,
and skin type.

## HD mode

Camera:

```text
faceDetectionMode = hdskincare
```

API actions use only HD concerns. HD and SD are never mixed.

HD capture requires a sufficiently high-resolution camera.

## Security

The server API key is never sent to JavaScript or the browser.

If a key has been pasted into a chat, issue tracker, public repository, or
other shared location, rotate/revoke it before deployment.

## Files

- `streamlit_app.py` — UI and result rendering
- `src/camera_component.py` — Perfect Corp JS Camera Kit integration
- `src/perfectcorp_api.py` — File API + Skin Analysis API v2.1
- `.streamlit/secrets.toml.example` — safe configuration template
- `Dockerfile` — Railway/container deployment

## Notes

Perfect Corp's documented result format can return:
- `ui_score`
- `raw_score`
- `mask_urls`

The app renders these directly and keeps a raw API-response expander for
debugging.

Skin-analysis scores are cosmetic image-analysis outputs, not a medical
diagnosis.
