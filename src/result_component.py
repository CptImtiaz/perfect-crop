from __future__ import annotations

import streamlit as st


HTML = r"""
<div id="skin-result-app">
  <div class="report-card">
    <div class="result-stage">
      <img id="result-base" class="result-base" alt="Skin analysis" />
      <img id="result-overlay" class="result-overlay" alt="Analysis overlay" />
      <div class="result-shade"></div>
      <button id="info-btn" class="info-button" type="button">i</button>
      <div class="legend-panel">
        <div id="category-badge" class="category-badge">Hydration</div>
        <div id="legend-top" class="legend-caption legend-top">Higher</div>
        <div id="legend-bar" class="legend-bar"></div>
        <div id="legend-bottom" class="legend-caption legend-bottom">Lower</div>
      </div>
    </div>
    <div class="score-title">Your skin scores</div>
    <div id="score-rail" class="score-rail"></div>
  </div>

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
*{box-sizing:border-box}
#skin-result-app{
  width:100%;height:760px;position:relative;overflow:hidden;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  color:#19364f;background:#f4fafb;
}
.report-card{height:100%;background:#fff;border-radius:26px;overflow:hidden;border:1px solid #dfeaf0;box-shadow:0 16px 44px rgba(42,82,108,.10)}
.result-stage{position:absolute;left:0;right:0;top:0;height:555px;overflow:hidden;background:#e9f1f4}
.result-base,.result-overlay{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.result-overlay{opacity:.62;transition:opacity .2s ease}
.result-shade{position:absolute;inset:0;pointer-events:none;background:linear-gradient(90deg,rgba(16,44,62,.06),transparent 45%,rgba(16,44,62,.12))}
.info-button{position:absolute;left:18px;top:18px;z-index:8;width:38px;height:38px;border-radius:50%;border:1px solid rgba(255,255,255,.72);background:rgba(21,61,82,.45);backdrop-filter:blur(8px);color:#fff;font-family:Georgia,serif;font-size:24px;cursor:pointer}
.legend-panel{position:absolute;right:14px;top:16%;width:110px;height:57%;z-index:7;pointer-events:none}
.category-badge{position:absolute;right:0;top:0;min-width:108px;padding:9px 10px;font-size:13px;font-weight:750;text-align:center;background:#4ebfc6;color:#fff;border-radius:999px;box-shadow:0 5px 15px rgba(0,0,0,.14)}
.legend-bar{position:absolute;right:22px;top:101px;width:23px;height:51%;border-radius:999px;background:linear-gradient(#7bd9ff,#071263);box-shadow:0 4px 13px rgba(0,0,0,.12)}
.legend-caption{position:absolute;right:0;min-width:86px;padding:5px 8px;border-radius:999px;background:rgba(255,255,255,.9);color:#4d6475;font-size:10px;text-align:center;box-shadow:0 3px 10px rgba(0,0,0,.08)}
.legend-top{top:67px}.legend-bottom{bottom:2px}
.score-title{position:absolute;left:0;right:0;top:555px;height:36px;padding:13px 22px 0;background:#fff;color:#24465a;font-size:13px;font-weight:760}
.score-rail{position:absolute;left:0;right:0;bottom:0;height:169px;background:#fff;color:#19364f;display:flex;gap:14px;align-items:flex-start;overflow-x:auto;overflow-y:hidden;padding:13px 22px 20px;scroll-snap-type:x proximity;-webkit-overflow-scrolling:touch;border-top:1px solid #eef3f5}
.score-rail::-webkit-scrollbar{display:none}
.score-item{min-width:82px;text-align:center;scroll-snap-align:center;cursor:pointer;user-select:none}
.score-circle{width:70px;height:70px;margin:0 auto 8px;border-radius:50%;border:2px solid var(--item-color);display:grid;place-items:center;background:#fff;font-size:25px;font-weight:700;color:#274a5f;transition:.18s ease;box-shadow:0 6px 15px rgba(40,80,105,.07)}
.score-item.active .score-circle{background:var(--item-color);color:#fff;transform:scale(1.04);box-shadow:0 8px 18px color-mix(in srgb,var(--item-color) 35%,transparent)}
.score-label{font-size:11px;line-height:1.18;color:#5f7585;white-space:normal}
.score-item.active .score-label{color:#2c5267;font-weight:700}
.sheet-backdrop{position:absolute;inset:0;z-index:40;background:rgba(20,45,61,.38);display:flex;align-items:flex-end}
.sheet-backdrop.hidden{display:none}
.info-sheet{width:100%;max-height:72%;overflow:auto;background:#fff;color:#19364f;border-radius:24px 24px 0 0;padding:10px 22px 22px;box-shadow:0 -18px 50px rgba(26,56,76,.14)}
.sheet-handle{width:44px;height:5px;border-radius:999px;background:#d5e2e8;margin:0 auto 17px}
.info-sheet h2{margin:0 0 15px;font-size:23px;letter-spacing:-.02em}
.info-row{padding:12px 0;border-bottom:1px solid #edf2f4}.info-row small{display:block;color:#8093a0;margin-bottom:3px}.info-row strong{font-weight:700;color:#294c60}
.sheet-button{margin-top:18px;width:100%;border:0;border-radius:999px;background:linear-gradient(90deg,#5fc3ca,#4e93c2);color:#fff;padding:13px;font-weight:750;cursor:pointer}
@media(max-width:699px){#skin-result-app{height:735px}.result-stage{height:530px}.score-title{top:530px}.score-rail{height:169px}}
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
    parentElement.querySelectorAll(".score-item").forEach((el, i) => el.classList.toggle("active", i === index));
    overlay.src = item.overlay || "";
    overlay.style.display = item.overlay ? "block" : "none";
    badge.textContent = item.label || item.key || "Analysis";
    badge.style.background = item.color || "#4ebfc6";
    legendTop.textContent = item.legend_top || "Higher";
    legendBottom.textContent = item.legend_bottom || "Lower";
    legendBar.style.background = item.gradient || "linear-gradient(#8edbe0,#476a8d)";
    infoTitle.textContent = item.label || "Analysis details";
    const raw = item.raw_score == null ? "—" : Number(item.raw_score).toFixed(2);
    infoContent.innerHTML = `
      <div class="info-row"><small>Display score</small><strong>${Math.round(Number(item.score) || 0)}/100</strong></div>
      <div class="info-row"><small>Raw score</small><strong>${raw}</strong></div>
      <div class="info-row"><small>About this result</small><strong>Cosmetic image analysis only.</strong></div>`;
  }

  rail.innerHTML = "";
  categories.forEach((item, index) => {
    const el = document.createElement("div");
    el.className = "score-item";
    el.style.setProperty("--item-color", item.color || "#70a9c4");
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
