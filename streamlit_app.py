from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests
import streamlit as st

from src.skin_api import SkinAPIError, output_items, run_skin_analysis


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
        value = st.secrets.get("SKIN_API_KEY")
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv("SKIN_API_KEY") or None


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
    for child in item.values():
        if isinstance(child, dict):
            candidate = child.get("ui_score")
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
                else "AI score"
            )
            with col:
                st.markdown(
                    f"""
                    <div class="score-card">
                      <div class="score-name">{concern_title(str(item.get("type", "")))}</div>
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
                    found.extend(str(url) for url in child if isinstance(url, str))
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
        return

    st.subheader("Detection maps")
    cols = st.columns(3)
    for idx, (title, url) in enumerate(masks):
        with cols[idx % 3]:
            try:
                response = requests.get(url, timeout=20)
                response.raise_for_status()
                st.image(response.content, caption=title, use_container_width=True)
            except Exception:
                st.caption(f"{title}: image unavailable")


st.markdown(
    """
    <div class="hero">
      <h1>AI Skin Analysis</h1>
      <p>
        Capture or upload a clear selfie, then analyze skin concerns and
        view scores and detection maps. Cosmetic image analysis only.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Analysis settings")
    quality_mode = st.radio("Analysis quality", ["Standard", "HD"], index=0)

hd = quality_mode == "HD"
api_key = get_api_key()

camera_tab, upload_tab = st.tabs(["Camera", "Upload"])
selected_file = None

with camera_tab:
    camera_file = st.camera_input(
        "Take a clear front-facing photo",
        help="Use even lighting and keep your full face visible.",
    )
    if camera_file is not None:
        selected_file = camera_file
        st.caption("Photo ready for analysis.")

with upload_tab:
    upload_file = st.file_uploader(
        "Upload a selfie",
        type=["jpg", "jpeg", "png"],
    )
    if upload_file is not None:
        selected_file = upload_file

if selected_file is not None:
    image_bytes = selected_file.getvalue()
    image_name = getattr(selected_file, "name", "skin_scan.jpg") or "skin_scan.jpg"
    image_type = getattr(selected_file, "type", "image/jpeg") or "image/jpeg"
    st.image(image_bytes, caption="Selected image", width=340)
else:
    image_bytes = None
    image_name = "skin_scan.jpg"
    image_type = "image/jpeg"

st.markdown(
    """
    <div class="notice">
      Use even lighting, avoid filters, and keep only one face in the image.
    </div>
    """,
    unsafe_allow_html=True,
)

analyze = st.button(
    "Analyze skin",
    type="primary",
    disabled=image_bytes is None,
    use_container_width=True,
)

if analyze:
    if not api_key:
        st.error(
            "The server API key is not configured. Add `SKIN_API_KEY` to your "
            "deployment variables or `.streamlit/secrets.toml`, then try again."
        )
    elif image_bytes is None:
        st.warning("Take or upload a photo first.")
    else:
        progress = st.progress(5, text="Preparing image…")

        def on_poll(attempt: int, status: str):
            progress.progress(
                min(92, 25 + attempt * 7),
                text=f"Analyzing: {status}…",
            )

        try:
            progress.progress(12, text="Uploading image…")
            result = run_skin_analysis(
                api_key,
                image_bytes,
                hd=hd,
                filename=image_name,
                content_type=image_type,
                on_poll=on_poll,
            )
            progress.progress(100, text="Analysis complete")
            st.session_state["skin_analysis_result"] = result
        except SkinAPIError as exc:
            progress.empty()
            st.error(str(exc))
        except requests.RequestException as exc:
            progress.empty()
            st.error(f"Network error: {exc}")
        except Exception as exc:
            progress.empty()
            st.error(f"Unexpected error: {type(exc).__name__}: {exc}")

result = st.session_state.get("skin_analysis_result")
if result:
    items = output_items(result)

    st.divider()
    st.header("Skin analysis")

    if items:
        score_cards(items)
        rows = [
            {
                "Concern": concern_title(str(item.get("type", ""))),
                "UI score": score_number(item),
                "Raw score": item.get("raw_score"),
            }
            for item in items
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        show_masks(items)
    else:
        st.warning("The analysis finished, but no result items were returned.")

    with st.expander("Technical response"):
        st.json(result)
