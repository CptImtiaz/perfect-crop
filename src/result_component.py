from __future__ import annotations

import streamlit as st


HTML = r"""
<div id="skin-result-app">
  <div class="result-stage">
    <img id="result-base" class="result-base" alt="Skin analysis" />
    <img id="result-overlay" class="result-overlay" alt="Analysis overlay" />
    <div class="result-shade"></div>

    <button id="info-btn" class="info-button" type="button">i</button>

    <div class="legend-panel">
      <div id="category-badge" class="category-badge">Hydration</div>
      <div id="legend-top" class="legend-caption legend-top">Hydrated</div>
      <div id="legend-bar" class="legend-bar"></div>
      <div id="legend-bottom" class="legend-caption legend-bottom">Dry</div>
    </div>
  </div>

  <div id="score-rail" class="score-rail"></div>

  <div id="info-sheet" class="sheet-backdrop hidden">
    <div class="info-sheet">
      <div class="sheet-handle"></div>
      <h2 id="info-title">Analysis details</h2>
      <div id="info-content"></div>
      <button id="close-info" class="sheet-button" type="button">Close</button>
    </div>
  </div>
</div>
"""

CSS = r"""
:root {
  --cyan:#1dd4e5; --blue:#31aee8; --red:#ff5948; --orange:#ff981f;
  --purple:#c36dea; --pink:#ef79e4; --green:#79db73; --coral:#ff8b7f;
}
*{box-sizing:border-box}
#skin-result-app{
  width:100%;height:760px;background:#000;position:relative;overflow:hidden;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  color:#fff;
}
.result-stage{position:absolute;inset:0 0 176px 0;overflow:hidden;background:#000}
.result-base,.result-overlay{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.result-overlay{opacity:.68;transition:opacity .2s ease}
.result-shade{position:absolute;inset:0;pointer-events:none;background:linear-gradient(90deg,rgba(0,0,0,.12),transparent 44%,rgba(0,0,0,.18))}
.info-button{position:absolute;left:21px;top:20px;z-index:8;width:41px;height:41px;border:3px solid #72c5ff;background:rgba(0,0,0,.1);color:#fff;font-family:Georgia,serif;font-size:27px;line-height:31px;cursor:pointer}
.legend-panel{position:absolute;right:0;top:16%;width:132px;height:58%;z-index:7;pointer-events:none}
.category-badge{position:absolute;right:0;top:0;min-width:122px;padding:11px 12px;font-size:18px;text-align:center;background:var(--cyan);color:#fff}
.legend-bar{position:absolute;right:26px;top:120px;width:34px;height:55%;background:linear-gradient(#7bd9ff,#071263)}
.legend-caption{position:absolute;right:14px;min-width:82px;padding:5px 9px;background:rgba(110,110,110,.72);color:#eee;font-size:13px;text-align:center}
.legend-top{top:82px}.legend-bottom{bottom:2px}
.score-rail{position:absolute;left:0;right:0;bottom:0;height:176px;background:#fff;color:#111;display:flex;gap:20px;align-items:flex-start;overflow-x:auto;overflow-y:hidden;padding:17px 28px 18px;scroll-snap-type:x proximity;-webkit-overflow-scrolling:touch}
.score-rail::-webkit-scrollbar{display:none}
.score-item{min-width:92px;text-align:center;scroll-snap-align:center;cursor:pointer;user-select:none}
.score-circle{width:78px;height:78px;margin:0 auto 8px;border-radius:50%;border:2px solid var(--item-color);display:grid;place-items:center;background:#fff;font-size:31px;font-weight:600;transition:.18s ease}
.score-item.active .score-circle{background:var(--item-color);color:#060606;border-color:var(--item-color);transform:scale(1.03)}
.score-label{font-size:14px;line-height:1.15;white-space:normal}
.sheet-backdrop{position:absolute;inset:0;z-index:40;background:rgba(0,0,0,.48);display:flex;align-items:flex-end}
.sheet-backdrop.hidden{display:none}
.info-sheet{width:100%;max-height:72%;overflow:auto;background:#fff;color:#1d2630;border-radius:24px 24px 0 0;padding:10px 22px 20px}
.sheet-handle{width:44px;height:5px;border-radius:999px;background:#d5d7db;margin:0 auto 17px}
.info-sheet h2{margin:0 0 15px;font-size:24px}
.info-row{padding:11px 0;border-bottom:1px solid #eceff1}.info-row small{display:block;color:#7d8790;margin-bottom:3px}.info-row strong{font-weight:650}
.sheet-button{margin-top:18px;width:100%;border:0;border-radius:999px;background:#121a31;color:#fff;padding:13px;cursor:pointer}
@media(min-width:700px){#skin-result-app{width:min(520px,100%);margin:0 auto;box-shadow:0 0 80px rgba(0,0,0,.45)}}
"""

JS = r"""
export default function(component) {
  const { data, parentElement } = component;
  const $ = (s) => parentElement.querySelector(s);

  const base = $("#result-base");
  const overlay = $("#result-overlay");
  const rail = $("#score-rail");
  const badge = $("#category-badge");
  const legendBar = $("#legend-bar");
  const legendTop = $("#legend-top");
  const legendBottom = $("#legend-bottom");
  const infoSheet = $("#info-sheet");
  const infoTitle = $("#info-title");
  const infoContent = $("#info-content");

  const categories = Array.isArray(data?.categories) ? data.categories : [];
  base.src = data?.base_image || "";

  function selectCategory(index) {
    const item = categories[index];
    if (!item) return;

    parentElement.querySelectorAll(".score-item").forEach((el, i) => {
      el.classList.toggle("active", i === index);
    });

    overlay.src = item.overlay || "";
    overlay.style.display = item.overlay ? "block" : "none";
    badge.textContent = item.label || item.key || "Analysis";
    badge.style.background = item.color || "#1dd4e5";
    legendTop.textContent = item.legend_top || "Higher";
    legendBottom.textContent = item.legend_bottom || "Lower";
    legendBar.style.background = item.gradient || "linear-gradient(#7bd9ff,#071263)";

    infoTitle.textContent = item.label || "Analysis details";
    const raw = item.raw_score == null ? "—" : Number(item.raw_score).toFixed(2);
    infoContent.innerHTML = `
      <div class="info-row"><small>Display score</small><strong>${Math.round(Number(item.score) || 0)}/100</strong></div>
      <div class="info-row"><small>Raw score</small><strong>${raw}</strong></div>
      <div class="info-row"><small>Note</small><strong>Cosmetic image analysis only.</strong></div>`;
  }

  rail.innerHTML = "";
  categories.forEach((item, index) => {
    const el = document.createElement("div");
    el.className = "score-item";
    el.style.setProperty("--item-color", item.color || "#61b9e8");
    el.innerHTML = `<div class="score-circle">${Math.round(Number(item.score) || 0)}</div><div class="score-label">${item.label || item.key || "Score"}</div>`;
    el.onclick = () => selectCategory(index);
    rail.appendChild(el);
  });

  $("#info-btn").onclick = () => infoSheet.classList.remove("hidden");
  $("#close-info").onclick = () => infoSheet.classList.add("hidden");
  infoSheet.onclick = (e) => { if (e.target === infoSheet) infoSheet.classList.add("hidden"); };

  selectCategory(0);
}
"""


result_viewer = st.components.v2.component(
    name="skin_scan_result_viewer",
    html=HTML,
    css=CSS,
    js=JS,
    isolate_styles=False,
)


def show_result_viewer(base_image: str, categories: list[dict], key: str = "skin_results"):
    return result_viewer(
        key=key,
        data={"base_image": base_image, "categories": categories},
        height=760,
        width="stretch",
    )
