from __future__ import annotations

import base64
import os
from typing import Any

import pandas as pd
import requests
import streamlit as st

from src.camera_component import perfectcorp_camera
from src.perfectcorp_api import PerfectCorpError, run_skin_analysis, output_items


st.set_page_config(
    page_title="AI Skin Analysis",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container { max-width: 1180px; padding-top: 1.5rem; }
      .hero { padding: 8px 0 20px 0; }
      .hero h1 {
        font-size: clamp(2.1rem, 6vw, 4rem);
        letter-spacing: -0.045em;
        margin: 0;
      }
      .hero p {
        max-width: 760px;
        font-size: 1.02rem;
        opacity: .72;
        margin-top: .6rem;
      }
      .score-card {
        border: 1px solid rgba(127,127,127,.16);
        border-radius: 20px;
        padding: 16px;
        min-height: 122px;
        background: rgba(127,127,127,.035);
      }
      .score-name {
        font-size: .78rem;
        opacity:.62;
        text-transform:uppercase;
        letter-spacing:.08em;
        font-weight:700;
      }
      .score-value {
        font-size:2rem;
        font-weight:780;
        letter-spacing:-.04em;
      }
      .score-raw { font-size:.75rem; opacity:.55; }
      .notice {
        padding: 12px 14px;
        border-radius: 14px;
        background: rgba(127,127,127,.07);
        font-size: .9rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_api_key() -> str | None:
    try:
        value = st.secrets.get("PERFECTCORP_API_KEY")
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv("PERFECTCORP_API_KEY") or None


def data_url_to_bytes(data_url: str) -> tuple[bytes, str]:
    if not data_url.startswith("data:"):
        raise ValueError("Camera returned an invalid image.")
    header, encoded = data_url.split(",", 1)
    mime = header.split(";")[0].replace("data:", "") or "image/jpeg"
    return base64.b64decode(encoded), mime


def concern_title(name: str) -> str:
    label = name.replace("hd_", "").replace("_v2", "")
    aliases = {
        "age_spot": "Dark Spots",
        "moisture": "Hydration",
        "pore": "Pores",
        "dark_circle": "Dark Circles",
        "skin_type": "Skin Type",
        "tear_trough": "Tear Trough",
        "eye_bag": "Eye Bags",
        "droopy_upper_eyelid": "Upper Eyelid",
        "droopy_lower_eyelid": "Lower Eyelid",
    }
    return aliases.get(label, label.replace("_", " ").title())


def score_number(item: dict[str, Any]) -> float | None:
    value = item.get("ui_score")
    if isinstance(value, (int, float)):
        return float(value)

    regional = []
    for value in item.values():
        if isinstance(value, dict):
            candidate = value.get("ui_score")
            if isinstance(candidate, (int, float)):
                regional.append(float(candidate))
    return sum(regional) / len(regional) if regional else None


def score_cards(items: list[dict[str, Any]]):
    scored = [(item, score_number(item)) for item in items]
    scored = [(item, score) for item, score in scored if score is not None]

    for start in range(0, len(scored), 4):
        cols = st.columns(4)
        for col, (item, score) in zip(cols, scored[start:start + 4]):
            raw = item.get("raw_score")
            raw_text = (
                f"Raw: {float(raw):.2f}"
                if isinstance(raw, (int, float))
                else "Perfect Corp score"
            )
            with col:
                st.markdown(
                    f"""
                    <div class="score-card">
                      <div class="score-name">
                        {concern_title(str(item.get("type","")))}
                      </div>
                      <div class="score-value">{score:.0f}</div>
                      <div class="score-raw">{raw_text}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def collect_mask_urls(item: dict[str, Any]) -> list[str]:
    found: list[str] = []

    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "mask_urls" and isinstance(child, list):
                    found.extend(
                        str(url) for url in child if isinstance(url, str)
                    )
                else:
                    walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(item)
    return list(dict.fromkeys(found))


def show_masks(items: list[dict[str, Any]]):
    masks = []
    for item in items:
        title = concern_title(str(item.get("type", "")))
        for url in collect_mask_urls(item):
            masks.append((title, url))

    if not masks:
        st.info("No detection-mask URLs were returned for this result.")
        return

    st.subheader("Detection maps")
    cols = st.columns(3)
    for idx, (title, url) in enumerate(masks):
        with cols[idx % 3]:
            try:
                response = requests.get(url, timeout=20)
                response.raise_for_status()
                st.image(
                    response.content,
                    caption=title,
                    use_container_width=True,
                )
            except Exception:
                st.caption(f"{title}: result image unavailable")


st.markdown(
    """
    <div class="hero">
      <h1>AI Skin Analysis</h1>
      <p>
        Guided capture with Perfect Corp Camera Kit, then server-side
        Skin Analysis API processing. This is cosmetic image analysis,
        not a medical diagnosis.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

api_key = get_api_key()
if not api_key:
    st.warning(
        "Add `PERFECTCORP_API_KEY` to `.streamlit/secrets.toml` "
        "or your deployment environment."
    )

with st.sidebar:
    st.header("Capture settings")
    quality_mode = st.radio(
        "Analysis quality",
        ["Standard", "HD"],
        index=0,
    )
    quality_level = st.selectbox(
        "Camera quality checks",
        ["relaxed", "moderate", "strict"],
        index=1,
    )
    video_quality = st.selectbox(
        "Camera output",
        ["720p", "1080p", "1920p"],
        index=1 if quality_mode == "Standard" else 2,
    )

hd = quality_mode == "HD"
camera_mode = "hdskincare" if hd else "skincare"

camera_tab, upload_tab = st.tabs(["Camera", "Upload"])

image_bytes = None
image_mime = "image/jpeg"
image_name = "perfectcorp_camera.jpg"

with camera_tab:
    camera_result = perfectcorp_camera(
        mode=camera_mode,
        quality_level=quality_level,
        video_quality=video_quality,
        key="skin_camera",
    )

    capture = getattr(camera_result, "capture", None)
    if capture and capture.get("image"):
        try:
            image_bytes, image_mime = data_url_to_bytes(capture["image"])
            st.success(
                f"Captured {capture.get('width','?')} × "
                f"{capture.get('height','?')}."
            )
            st.image(image_bytes, caption="Captured selfie", width=340)
        except Exception as exc:
            st.error(f"Could not read captured image: {exc}")

with upload_tab:
    uploaded = st.file_uploader(
        "Upload a front-facing selfie",
        type=["jpg", "jpeg", "png"],
    )
    if uploaded:
        image_bytes = uploaded.getvalue()
        image_mime = uploaded.type or "image/jpeg"
        image_name = uploaded.name
        st.image(image_bytes, caption="Uploaded selfie", width=340)

st.markdown(
    """
    <div class="notice">
      Use even lighting and keep the full face visible. For HD mode,
      the camera must meet Perfect Corp's higher resolution requirement.
    </div>
    """,
    unsafe_allow_html=True,
)

analyze = st.button(
    "Analyze skin",
    type="primary",
    disabled=not (api_key and image_bytes),
    use_container_width=True,
)

if analyze and api_key and image_bytes:
    progress = st.progress(0, text="Preparing image…")

    def on_poll(attempt: int, status: str):
        progress.progress(
            min(90, 25 + attempt * 8),
            text=f"Perfect Corp analysis: {status}…",
        )

    try:
        progress.progress(10, text="Uploading securely…")
        result = run_skin_analysis(
            api_key,
            image_bytes,
            hd=hd,
            filename=image_name,
            content_type=image_mime,
            on_poll=on_poll,
        )
        progress.progress(100, text="Analysis complete")
        st.session_state["perfectcorp_result"] = result
    except PerfectCorpError as exc:
        progress.empty()
        st.error(str(exc))
    except Exception as exc:
        progress.empty()
        st.error(f"Unexpected error: {type(exc).__name__}: {exc}")

result = st.session_state.get("perfectcorp_result")
if result:
    items = output_items(result)

    st.divider()
    st.header("Skin analysis")

    if items:
        score_cards(items)

        table_rows = [
            {
                "Concern": concern_title(str(item.get("type", ""))),
                "UI score": score_number(item),
                "Raw score": item.get("raw_score"),
            }
            for item in items
        ]
        st.dataframe(
            pd.DataFrame(table_rows),
            hide_index=True,
            use_container_width=True,
        )
        show_masks(items)
    else:
        st.warning(
            "The task completed, but `results.output` was not found."
        )

    with st.expander("Raw API response"):
        st.json(result)
