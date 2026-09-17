from __future__ import annotations

import streamlit as st


HTML = r"""
<div class="pc-card">
  <div class="pc-head">
    <div>
      <div class="pc-kicker">PERFECT CORP CAMERA KIT</div>
      <div class="pc-title">AI Skin Camera</div>
    </div>
    <div id="pc-status" class="pc-status">Ready</div>
  </div>

  <div id="YMK-module" class="ymk-mount"></div>

  <div class="pc-quality">
    <div class="q-item"><span>Face</span><strong id="q-face">—</strong></div>
    <div class="q-item"><span>Position</span><strong id="q-position">—</strong></div>
    <div class="q-item"><span>Frontal</span><strong id="q-frontal">—</strong></div>
    <div class="q-item"><span>Lighting</span><strong id="q-lighting">—</strong></div>
  </div>

  <div class="pc-actions">
    <button id="pc-open" class="primary">Open camera</button>
    <button id="pc-close" class="secondary">Close</button>
  </div>

  <div id="pc-error" class="pc-error"></div>
</div>
"""

CSS = r"""
.pc-card {
  width:100%;
  max-width:760px;
  margin:0 auto;
  border:1px solid color-mix(in srgb,var(--st-text-color) 12%,transparent);
  border-radius:24px;
  padding:18px;
  background:color-mix(in srgb,var(--st-background-color) 96%,#fff 4%);
  box-sizing:border-box;
  box-shadow:0 16px 50px rgba(0,0,0,.08);
}
.pc-head{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:14px}
.pc-kicker{font-size:11px;letter-spacing:.16em;opacity:.55;font-weight:700}
.pc-title{font-size:24px;font-weight:750;margin-top:2px}
.pc-status{padding:7px 11px;border-radius:999px;background:rgba(120,120,120,.10);font-size:12px;font-weight:650}
.ymk-mount{min-height:420px;width:100%;overflow:hidden;border-radius:20px;background:#0b0b0d}
.pc-quality{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px}
.q-item{padding:10px 11px;border-radius:14px;background:rgba(127,127,127,.08);display:flex;flex-direction:column;gap:2px}
.q-item span{font-size:11px;opacity:.6}.q-item strong{font-size:13px}
.pc-actions{display:flex;gap:10px;margin-top:12px}
.pc-actions button{border:none;border-radius:14px;padding:12px 18px;font-size:14px;font-weight:700;cursor:pointer}
.primary{background:var(--st-primary-color);color:white}
.secondary{background:rgba(127,127,127,.12);color:var(--st-text-color)}
.pc-error{color:#d74343;font-size:12px;margin-top:8px}
@media(max-width:620px){.pc-quality{grid-template-columns:repeat(2,1fr)}.ymk-mount{min-height:360px}}
"""

JS = r"""
export default function(component) {
  const { data, parentElement, setStateValue } = component;
  const $ = (sel) => parentElement.querySelector(sel);

  const statusEl = $("#pc-status");
  const errorEl = $("#pc-error");
  const openBtn = $("#pc-open");
  const closeBtn = $("#pc-close");
  const qFace = $("#q-face");
  const qPosition = $("#q-position");
  const qFrontal = $("#q-frontal");
  const qLighting = $("#q-lighting");

  const config = data || {};
  const listenerIds = [];
  let cancelled = false;

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text;
  }
  function setError(text) {
    if (errorEl) errorEl.textContent = text || "";
  }
  function fmt(value) {
    if (value === true) return "Good";
    if (value === false) return "Check";
    if (value == null) return "—";
    const s = String(value);
    return s.charAt(0).toUpperCase() + s.slice(1);
  }
  function addListener(name, fn) {
    try {
      const id = window.YMK.addEventListener(name, fn);
      if (id != null) listenerIds.push(id);
    } catch (_) {}
  }

  function setupListeners() {
    if (!window.YMK || cancelled) return;

    addListener("loading", (v) => setStatus(`Loading ${v ?? 0}%`));
    addListener("loaded", () => setStatus("Camera ready"));
    addListener("opened", () => setStatus("Camera open"));
    addListener("closed", () => setStatus("Ready"));

    addListener("cameraFailed", (e) => {
      const msg = e?.error || e?.code || e?.message || "Camera unavailable";
      setError(`Camera error: ${msg}`);
      setStatus("Camera error");
    });

    addListener("unsupportedResolution", () => {
      setError("Camera resolution is too low for this mode. Try Standard mode.");
    });

    addListener("faceQualityChanged", (q) => {
      qFace.textContent = fmt(q?.hasFace);
      qPosition.textContent = fmt(q?.position);
      qFrontal.textContent = fmt(q?.frontal);
      qLighting.textContent = fmt(q?.lighting);
    });

    addListener("faceDetectionCaptured", (result) => {
      try {
        const item = result?.images?.[0];
        if (!item?.image || typeof item.image !== "string") {
          setError("Capture completed but no base64 image was returned.");
          return;
        }

        setStatus("Captured");
        setStateValue("capture", {
          image: item.image,
          width: item.width ?? null,
          height: item.height ?? null,
          phase: item.phase ?? 0,
          mode: result?.mode ?? config.mode ?? "skincare",
          captured_at: Date.now()
        });

        try { window.YMK.close(); } catch (_) {}
      } catch (e) {
        setError(`Capture error: ${e.message || e}`);
      }
    });
  }

  function initAndOpen() {
    setError("");
    if (!window.YMK) {
      setError("Perfect Corp Camera Kit is still loading.");
      return;
    }

    try {
      window.YMK.init({
        faceDetectionMode: config.mode || "skincare",
        imageFormat: "base64",
        language: config.language || "enu",
        width: Math.min(720, Math.max(320, window.innerWidth - 80)),
        height: config.height || 520,
        disableCameraResolutionCheck: !!config.disable_resolution_check,
        hideFlipCameraButton: false,
        countingDuration: 800,
        qualityLevel: config.quality_level || "moderate",
        videoQuality: config.video_quality || "1080p"
      });
      setStatus("Opening…");
      window.YMK.openCameraKit();
    } catch (e) {
      setError(`Could not open Camera Kit: ${e.message || e}`);
      setStatus("Error");
    }
  }

  function ensureSdk() {
    if (window.YMK) {
      setupListeners();
      return;
    }

    const previous = window.YMKAsyncInit;
    window.YMKAsyncInit = function() {
      try {
        if (typeof previous === "function") previous();
      } catch (_) {}
      setupListeners();
      setStatus("Ready");
    };

    const existing = document.querySelector('script[data-perfectcorp-camera-kit="v2.5"]');
    if (existing) {
      existing.addEventListener("load", () => {
        setupListeners();
        setStatus("Ready");
      }, { once: true });
      return;
    }

    const script = document.createElement("script");
    script.src = "https://plugins-media.makeupar.com/v2.5-camera-kit/sdk.js";
    script.async = true;
    script.dataset.perfectcorpCameraKit = "v2.5";
    script.onload = () => {
      if (window.YMK) {
        setupListeners();
        setStatus("Ready");
      }
    };
    script.onerror = () => {
      setError("Could not load Perfect Corp Camera Kit SDK.");
      setStatus("SDK error");
    };
    document.head.appendChild(script);
    setStatus("Loading SDK…");
  }

  openBtn.onclick = initAndOpen;
  closeBtn.onclick = () => {
    try { window.YMK?.close(); } catch (_) {}
    setStatus("Ready");
  };

  ensureSdk();

  return () => {
    cancelled = true;
    try {
      listenerIds.forEach((id) => window.YMK?.removeEventListener(id));
    } catch (_) {}
  };
}
"""


camera_component = st.components.v2.component(
    name="perfectcorp_skin_camera_v25",
    html=HTML,
    css=CSS,
    js=JS,
    isolate_styles=False,
)


def perfectcorp_camera(
    *,
    mode: str = "skincare",
    quality_level: str = "moderate",
    video_quality: str = "1080p",
    key: str = "perfectcorp_camera",
):
    return camera_component(
        key=key,
        data={
            "mode": mode,
            "quality_level": quality_level,
            "video_quality": video_quality,
            "language": "enu",
            "height": 520,
            "disable_resolution_check": False,
        },
        default={"capture": None},
        on_capture_change=lambda: None,
        height="content",
        width="stretch",
    )
