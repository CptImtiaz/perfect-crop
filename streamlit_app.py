from __future__ import annotations

import base64
import os
from typing import Any

import requests
import streamlit as st

from src.result_component import show_result_viewer
from src.skin_api import SkinAPIError, output_items, run_skin_analysis


st.set_page_config(
    page_title="AI Skin Analysis",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="collapsed",
)


APP_CSS = r"""
<style>
:root {
  --cyan:#1dd4e5; --blue:#31aee8; --red:#ff5948; --orange:#ff981f;
  --purple:#c36dea; --pink:#ef79e4; --green:#79db73; --coral:#ff8b7f;
}
html, body, [data-testid="stAppViewContainer"] { background:#111 !important; }
[data-testid="stHeader"], [data-testid="stToolbar"], footer { display:none !important; }
[data-testid="stAppViewBlockContainer"] {
  max-width:520px !important;
  padding:0 !important;
  background:#000;
  min-height:100vh;
  box-shadow:0 0 80px rgba(0,0,0,.55);
}
.block-container { max-width:520px !important; padding:0 !important; }

.skin-title {
  color:#fff; text-align:center; padding:18px 18px 8px; background:#000;
  font-size:20px; font-weight:650; letter-spacing:-.02em;
}
.quality-strip {
  display:grid; grid-template-columns:repeat(3,1fr); gap:10px;
  padding:10px; background:#000;
}
.quality-card {
  min-height:72px; display:flex; flex-direction:column; align-items:center;
  justify-content:center; text-align:center; color:#fff; padding:8px 4px;
  background:rgba(70,70,70,.78);
}
.quality-card span { font-size:13px; }
.quality-card strong { margin-top:4px; font-size:17px; font-weight:500; }
.camera-hint {
  margin:0 18px 12px; text-align:center; color:#fff; background:rgba(70,70,70,.55);
  border-radius:999px; padding:9px 14px; font-size:13px;
}

/* Camera area */
div[data-testid="stCameraInput"] {
  background:#050505; padding:0 10px 12px; margin:0; border:0;
}
div[data-testid="stCameraInput"] label { display:none; }
div[data-testid="stCameraInput"] video,
div[data-testid="stCameraInput"] img {
  width:100% !important; max-height:600px; object-fit:cover; border-radius:0 !important;
}
div[data-testid="stCameraInput"] button {
  border-radius:999px !important; min-height:48px; font-weight:650;
}

/* Upload tab */
[data-testid="stFileUploader"] { padding:8px 12px 12px; background:#000; color:#fff; }
[data-testid="stFileUploaderDropzone"] { background:#171717; border-color:#5c5c5c; }

/* Tabs */
.stTabs { background:#000; }
.stTabs [data-baseweb="tab-list"] { gap:0; background:#000; padding:0 10px; }
.stTabs [data-baseweb="tab"] { color:#ddd; flex:1; }
.stTabs [aria-selected="true"] { color:#fff !important; }

/* Analyze button */
.stButton { background:#000; padding:8px 18px 18px; }
.stButton > button {
  width:100%; border:0 !important; border-radius:999px !important;
  min-height:52px; background:#fff !important; color:#111 !important;
  font-size:17px !important; font-weight:700 !important;
}

.capture-ready {
  margin:0 18px 10px; padding:10px 14px; border-radius:10px;
  background:#163f1a; color:#c9ffd0; text-align:center; font-size:13px;
}
.mode-row { padding:8px 18px 0; background:#000; color:#fff; }
.mode-row div[role="radiogroup"] { justify-content:center; }
.mode-row label { color:#fff !important; }

/* Scanning screen */
.scan-shell {
  position:relative; height:680px; overflow:hidden; background:#000; color:#fff;
}
.scan-shell img { width:100%; height:100%; object-fit:cover; }
.scan-vignette { position:absolute; inset:0; background:radial-gradient(circle at 50% 46%,transparent 32%,rgba(0,0,0,.48) 100%); }
.scan-oval {
  position:absolute; width:72%; height:63%; left:50%; top:49%; transform:translate(-50%,-50%);
  border:2px solid rgba(255,255,255,.65); border-radius:50%;
}
.scanner-line {
  position:absolute; left:20%; width:60%; height:5px; top:35%;
  background:#fff; border-radius:999px;
  box-shadow:0 0 11px #fff,0 0 30px #fff,0 0 55px rgba(255,255,255,.85);
  animation:scan 1.45s ease-in-out infinite alternate;
}
@keyframes scan { from{top:35%;opacity:.65} to{top:61%;opacity:1} }
.scan-copy { position:absolute; left:0; right:0; bottom:48px; text-align:center; font-size:15px; }
.spinner { width:28px; height:28px; margin:0 auto 9px; border:3px solid rgba(255,255,255,.25); border-top-color:#fff; border-radius:50%; animation:spin .75s linear infinite; }
@keyframes spin { to{transform:rotate(360deg)} }

/* Streamlit messages / technical section */
[data-testid="stAlert"] { margin:10px 12px; }
[data-testid="stExpander"] { margin:8px 12px 18px; background:#fff; color:#111; }
[data-testid="stMarkdownContainer"] p { margin-bottom:.3rem; }

@media(max-width:699px) {
  [data-testid="stAppViewBlockContainer"] { width:100% !important; box-shadow:none; }
}
</style>
"""

st.markdown(APP_CSS, unsafe_allow_html=True)


def get_api_key() -> str | None:
    try:
        value = st.secrets.get("SKIN_API_KEY")
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv("SKIN_API_KEY") or None


def image_data_url(image_bytes: bytes, content_type: str) -> str:
    mime = content_type or "image/jpeg"
    if mime == "image/jpg":
        mime = "image/jpeg"
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def normalize_key(name: str) -> str:
    key = str(name or "").lower().replace("hd_", "").replace("_v2", "")
    mapping = {
        "moisture": "hydration",
        "age_spot": "pigment",
        "pore": "pores",
        "dark_circle": "dark_circles",
        "eye_bag": "eye_bags",
    }
    return mapping.get(key, key)


def concern_title(name: str) -> str:
    key = normalize_key(name)
    aliases = {
        "hydration": "Hydration",
        "pigment": "Dark Spots",
        "pores": "Pores",
        "dark_circles": "Dark Circles",
        "skin_type": "Skin Type",
        "tear_trough": "Tear Trough",
        "eye_bags": "Eye Bags",
        "droopy_upper_eyelid": "Upper Eyelid",
        "droopy_lower_eyelid": "Lower Eyelid",
        "oiliness": "Oiliness/Shine",
        "radiance": "Radiance",
        "firmness": "Firmness",
        "redness": "Redness",
        "texture": "Texture",
        "wrinkle": "Wrinkles",
        "acne": "Acne",
    }
    return aliases.get(key, key.replace("_", " ").title())


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


CATEGORY_STYLE = {
    "hydration": {
        "color": "#20d5df", "top": "Hydrated", "bottom": "Dry",
        "gradient": "linear-gradient(#0d55ff 0%,#1ec8df 25%,#6ddd65 43%,#ffcc45 60%,#ff6757 80%,#e62a3f 100%)",
    },
    "redness": {
        "color": "#ff5b47", "top": "Less visible", "bottom": "More visible",
        "gradient": "linear-gradient(#ffe0d9,#ff806b,#d52e2e)",
    },
    "oiliness": {
        "color": "#ff981f", "top": "Balanced", "bottom": "More shine",
        "gradient": "linear-gradient(#fff0ad,#da9711,#ff7512)",
    },
    "pigment": {
        "color": "#1fc2ec", "top": "Less visible", "bottom": "More visible",
        "gradient": "linear-gradient(#71c7f5,#3278b8,#07155c)",
    },
    "texture": {
        "color": "#c36dea", "top": "Smoother", "bottom": "Uneven",
        "gradient": "linear-gradient(#fff352,#735edb,#25049c)",
    },
    "pores": {
        "color": "#ef79e4", "top": "Fine", "bottom": "Visible",
        "gradient": "linear-gradient(#f1f8ff,#c47af0,#6a2c91)",
    },
    "dark_circles": {
        "color": "#ff8b7f", "top": "Less visible", "bottom": "More visible",
        "gradient": "linear-gradient(#f7d8d5,#d88d97,#7d4d70)",
    },
    "acne": {
        "color": "#79db73", "top": "Fewer", "bottom": "More visible",
        "gradient": "linear-gradient(#fff18a,#ff8d4d,#d9303e)",
    },
    "wrinkle": {
        "color": "#31aee8", "top": "Less visible", "bottom": "More visible",
        "gradient": "linear-gradient(#dff3ff,#5caadd,#17305c)",
    },
    "radiance": {
        "color": "#ffd34e", "top": "Radiant", "bottom": "Less radiant",
        "gradient": "linear-gradient(#fffbd1,#ffd34e,#bc7610)",
    },
    "firmness": {
        "color": "#77d5b6", "top": "Higher", "bottom": "Lower",
        "gradient": "linear-gradient(#d9fff2,#4dc59d,#176a56)",
    },
}


def result_categories(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    categories = []
    for index, item in enumerate(items):
        score = score_number(item)
        if score is None:
            continue

        key = normalize_key(str(item.get("type", "")))
        style = CATEGORY_STYLE.get(
            key,
            {
                "color": "#64b9e9",
                "top": "Higher",
                "bottom": "Lower",
                "gradient": "linear-gradient(#d8efff,#286ba3,#152b5f)",
            },
        )
        masks = collect_mask_urls(item)
        categories.append(
            {
                "key": key or f"result_{index}",
                "label": concern_title(str(item.get("type", ""))),
                "score": round(float(score), 1),
                "raw_score": item.get("raw_score"),
                "overlay": masks[0] if masks else "",
                "color": style["color"],
                "legend_top": style["top"],
                "legend_bottom": style["bottom"],
                "gradient": style["gradient"],
            }
        )
    return categories


st.markdown('<div class="skin-title">AI Skin Analysis</div>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="quality-strip">
      <div class="quality-card"><span>Lighting</span><strong>Even light</strong></div>
      <div class="quality-card"><span>Look Straight</span><strong>Face camera</strong></div>
      <div class="quality-card"><span>Face Position</span><strong>Centered</strong></div>
    </div>
    <div class="camera-hint">Center your face and use a clear, unfiltered photo</div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    quality_mode = st.radio("Analysis quality", ["Standard", "HD"], index=0)

hd = quality_mode == "HD"
api_key = get_api_key()

camera_tab, upload_tab = st.tabs(["Camera", "Use a photo instead"])
selected_file = None

with camera_tab:
    camera_file = st.camera_input(
        "Camera",
        help="Use even lighting and keep your full face visible.",
        label_visibility="collapsed",
    )
    if camera_file is not None:
        selected_file = camera_file

with upload_tab:
    upload_file = st.file_uploader(
        "Upload a selfie",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed",
    )
    if upload_file is not None:
        selected_file = upload_file

if selected_file is not None:
    image_bytes = selected_file.getvalue()
    image_name = getattr(selected_file, "name", "skin_scan.jpg") or "skin_scan.jpg"
    image_type = getattr(selected_file, "type", "image/jpeg") or "image/jpeg"
    st.session_state["scan_image_bytes"] = image_bytes
    st.session_state["scan_image_type"] = image_type
    st.markdown('<div class="capture-ready">Photo ready for analysis</div>', unsafe_allow_html=True)
else:
    image_bytes = st.session_state.get("scan_image_bytes")
    image_type = st.session_state.get("scan_image_type", "image/jpeg")
    image_name = "skin_scan.jpg"

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
        preview_url = image_data_url(image_bytes, image_type)
        scan_slot = st.empty()
        scan_slot.markdown(
            f"""
            <div class="scan-shell">
              <img src="{preview_url}" alt="Captured selfie" />
              <div class="scan-vignette"></div>
              <div class="scan-oval"></div>
              <div class="scanner-line"></div>
              <div class="scan-copy"><div class="spinner"></div><p>Analyzing your skin...</p></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        try:
            result = run_skin_analysis(
                api_key,
                image_bytes,
                hd=hd,
                filename=image_name,
                content_type=image_type,
            )
            st.session_state["skin_analysis_result"] = result
            st.session_state["result_base_image"] = preview_url
            scan_slot.empty()
        except SkinAPIError as exc:
            scan_slot.empty()
            st.error(str(exc))
        except requests.RequestException as exc:
            scan_slot.empty()
            st.error(f"Network error: {exc}")
        except Exception as exc:
            scan_slot.empty()
            st.error(f"Unexpected error: {type(exc).__name__}: {exc}")

result = st.session_state.get("skin_analysis_result")
if result:
    items = output_items(result)
    categories = result_categories(items)
    base_image = st.session_state.get("result_base_image", "")

    if categories and base_image:
        show_result_viewer(base_image, categories)
    elif not items:
        st.warning("The analysis finished, but no result items were returned.")

    with st.expander("Technical response"):
        st.json(result)
