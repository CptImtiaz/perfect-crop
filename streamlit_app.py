from __future__ import annotations

import base64
import os
from typing import Any

import streamlit as st

from src.result_component import show_result_viewer
from src.skin_api import SkinAPIError, output_items, run_skin_analysis

st.set_page_config(page_title="AI Skin Analysis", page_icon="✨", layout="centered", initial_sidebar_state="collapsed")

st.markdown(r"""
<style>
:root{--ink:#19364f;--muted:#718596;--line:#dce9ef;--aqua:#5fc3ca;--blue:#4e93c2;--soft:#f4fafb}
html,body,[data-testid="stAppViewContainer"]{background:linear-gradient(#f7fbfd,#eef7f8)!important;color:var(--ink)}
[data-testid="stHeader"],[data-testid="stToolbar"],footer{display:none!important}
[data-testid="stAppViewBlockContainer"],.block-container{max-width:560px!important;padding:0 0 36px!important}
.topbar{display:flex;justify-content:space-between;align-items:center;padding:18px 22px 10px;background:#fff}
.logo{display:flex;align-items:center;gap:10px;font-weight:800;color:var(--ink)}
.logo-dot{width:34px;height:34px;border-radius:50%;background:linear-gradient(145deg,#72d2d5,#78afe1);box-shadow:0 7px 18px rgba(65,153,176,.22)}
.pill{font-size:11px;color:#427486;background:#edf8f8;border:1px solid #d7eeee;padding:7px 10px;border-radius:999px;font-weight:700}
.hero{text-align:center;padding:16px 24px 18px;background:linear-gradient(#fff,#f4fbfc)}
.hero small{display:inline-block;color:#338b94;background:#e8f7f6;border:1px solid #d3eeee;padding:7px 11px;border-radius:999px;font-weight:750;letter-spacing:.04em}
.hero h1{font-size:31px;line-height:1.08;letter-spacing:-.045em;margin:12px auto 8px;color:var(--ink)}
.hero p{font-size:14px;line-height:1.5;color:var(--muted);margin:0 auto;max-width:420px}
.stepper{display:grid;grid-template-columns:repeat(3,1fr);margin:0 22px 18px;position:relative}
.stepper:before{content:"";position:absolute;left:16%;right:16%;top:16px;height:2px;background:#dce8ee}
.step{text-align:center;font-size:11px;color:#8a9dab;z-index:1}.step b{display:grid;place-items:center;width:32px;height:32px;margin:auto auto 6px;border-radius:50%;background:#fff;border:2px solid #d5e3e9}
.step.active{color:#318b94;font-weight:700}.step.active b{background:var(--aqua);border-color:var(--aqua);color:#fff}.step.done b{background:#e7f6f2;border-color:#82cfc4;color:#328d7d}
.guide-title{padding:0 22px 10px;font-size:15px;font-weight:760}
.guides{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;padding:0 18px 16px}.guide{background:#f8fbfc;border:1px solid #e1edf1;border-radius:16px;padding:12px 7px;text-align:center;min-height:92px}.guide i{display:grid;place-items:center;width:34px;height:34px;margin:0 auto 6px;border-radius:50%;background:#e7f6f7;color:#358c99;font-style:normal}.guide strong{display:block;font-size:12px}.guide span{display:block;font-size:10px;color:#8194a3;margin-top:2px}
.camera-copy{display:flex;justify-content:space-between;padding:10px 20px 8px;font-size:13px}.camera-copy span{color:#7b91a0;font-size:11px}.hint{margin:0 18px 10px;padding:9px 12px;text-align:center;border-radius:999px;background:#f2f7f9;color:#6e8493;font-size:11px}
.stTabs{padding:0 14px}.stTabs [data-baseweb="tab-list"]{background:#edf4f6;border-radius:999px;padding:4px;gap:4px}.stTabs [data-baseweb="tab"]{flex:1;border-radius:999px;height:40px;color:#708596;font-size:12px;font-weight:700}.stTabs [aria-selected="true"]{background:#fff!important;color:#25495e!important;box-shadow:0 3px 10px rgba(35,70,90,.08)}.stTabs [data-baseweb="tab-highlight"]{display:none}
div[data-testid="stCameraInput"]{margin:10px 14px;padding:0;background:#edf4f6;border:1px solid #dce7eb;border-radius:26px;overflow:hidden}div[data-testid="stCameraInput"] label{display:none}div[data-testid="stCameraInput"] video,div[data-testid="stCameraInput"] img{width:100%!important;min-height:400px;max-height:520px;object-fit:cover;border-radius:26px!important}div[data-testid="stCameraInput"] button{border-radius:999px!important;min-height:46px!important;font-weight:700!important}
[data-testid="stFileUploader"]{margin:10px 14px}[data-testid="stFileUploaderDropzone"]{background:#f7fafb!important;border:1px dashed #b9d1da!important;border-radius:20px!important;min-height:150px}
.ready{margin:8px 18px;padding:10px;border-radius:13px;background:#e8f7f1;border:1px solid #d2eee3;color:#2d7b66;text-align:center;font-size:12px;font-weight:700}
.mode{margin:10px 18px 0;padding:10px 12px 4px;background:#f7fafb;border:1px solid #e3edf1;border-radius:16px;font-size:11px;color:#6e8392;font-weight:700}
.stButton{padding:10px 18px 2px}.stButton>button{width:100%;min-height:54px;border:0!important;border-radius:999px!important;background:linear-gradient(90deg,var(--aqua),var(--blue))!important;color:#fff!important;font-weight:760!important;font-size:15px!important;box-shadow:0 10px 24px rgba(60,137,162,.23)}.stButton>button:disabled{background:#cbd8de!important;box-shadow:none}
.note{text-align:center;color:#8798a5;font-size:10px;padding:6px 28px 18px}
.scan{position:relative;height:680px;overflow:hidden;background:#071521;color:#fff}.scan img{width:100%;height:100%;object-fit:cover}.scan:after{content:"";position:absolute;inset:0;background:radial-gradient(ellipse at 50% 44%,transparent 28%,rgba(5,24,36,.68) 100%)}.oval{position:absolute;z-index:2;width:69%;height:62%;left:50%;top:47%;transform:translate(-50%,-50%);border:2px solid rgba(190,248,245,.9);border-radius:50%}.line{position:absolute;z-index:3;left:22%;width:56%;height:3px;top:34%;background:#baffff;box-shadow:0 0 22px #9ff;animation:scan 1.45s ease-in-out infinite alternate}@keyframes scan{to{top:61%}}.scantext{position:absolute;z-index:4;left:20px;right:20px;bottom:48px;text-align:center}.scantext strong{display:block;font-size:19px;margin-bottom:5px}.scantext span{font-size:12px;color:#d7edf0}
[data-testid="stAlert"],[data-testid="stExpander"]{margin-left:18px!important;margin-right:18px!important;border-radius:14px!important}
@media(max-width:699px){.hero h1{font-size:28px}div[data-testid="stCameraInput"] video,div[data-testid="stCameraInput"] img{min-height:360px}}
</style>
""", unsafe_allow_html=True)


def api_key() -> str | None:
    try:
        value = st.secrets.get("SKIN_API_KEY")
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv("SKIN_API_KEY") or None


def data_url(data: bytes, mime: str) -> str:
    mime = "image/jpeg" if mime in {"image/jpg", "image/jpeg"} else (mime or "image/jpeg")
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def key_name(name: str) -> str:
    value = str(name or "").lower().replace("hd_", "").replace("_v2", "")
    return {"moisture":"hydration","age_spot":"pigment","pore":"pores","dark_circle":"dark_circles","eye_bag":"eye_bags"}.get(value, value)


def title(name: str) -> str:
    key = key_name(name)
    return {"hydration":"Hydration","pigment":"Dark Spots","pores":"Pores","dark_circles":"Dark Circles","eye_bags":"Eye Bags","oiliness":"Oiliness / Shine","radiance":"Radiance","firmness":"Firmness","redness":"Redness","texture":"Texture","wrinkle":"Wrinkles","acne":"Blemishes","skin_type":"Skin Type"}.get(key,key.replace("_"," ").title())


def score(item: dict[str, Any]) -> float | None:
    value = item.get("ui_score")
    if isinstance(value,(int,float)):
        return float(value)
    vals=[float(v["ui_score"]) for v in item.values() if isinstance(v,dict) and isinstance(v.get("ui_score"),(int,float))]
    return sum(vals)/len(vals) if vals else None


def masks(item: dict[str, Any]) -> list[str]:
    found=[]
    def walk(v):
        if isinstance(v,dict):
            for k,c in v.items():
                if k=="mask_urls" and isinstance(c,list): found.extend(str(x) for x in c if isinstance(x,str))
                else: walk(c)
        elif isinstance(v,list):
            for c in v: walk(c)
    walk(item)
    return list(dict.fromkeys(found))


STYLES={
    "hydration":("#4ebfc6","More hydrated","Less hydrated","linear-gradient(#4e80ce,#4dc8cb,#8bd4a7,#f0cf6a,#e88363,#cf5658)"),
    "redness":("#ea8377","Less visible","More visible","linear-gradient(#fbe7e3,#eb9b8d,#c34d50)"),
    "oiliness":("#e4b45e","Balanced","More shine","linear-gradient(#fff1c8,#deb65e,#bc762d)"),
    "pigment":("#729bc5","Less visible","More visible","linear-gradient(#d9e8f5,#7aa3cc,#384f78)"),
    "texture":("#a98bc5","Smoother","More uneven","linear-gradient(#f1e8f7,#b094ca,#69527f)"),
    "pores":("#cf90ba","Less visible","More visible","linear-gradient(#f6e6f0,#ce91b8,#875072)"),
    "dark_circles":("#c88c98","Less visible","More visible","linear-gradient(#f0dfe2,#c7929d,#745a6c)"),
    "acne":("#86bb83","Less visible","More visible","linear-gradient(#ecf5d9,#dfb667,#c65b52)"),
    "wrinkle":("#6fa4c8","Less visible","More visible","linear-gradient(#e6f2f8,#8ab5d3,#4a687e)"),
    "radiance":("#e3c260","More radiant","Less radiant","linear-gradient(#fff7d6,#e9c86e,#b58b35)"),
    "firmness":("#75b8a8","Higher","Lower","linear-gradient(#e2f6f0,#80c2b1,#3d786d)"),
}


def categories(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out=[]
    for i,item in enumerate(items):
        s=score(item)
        if s is None: continue
        k=key_name(item.get("type",""))
        c,t,b,g=STYLES.get(k,("#75a9c1","Higher","Lower","linear-gradient(#dcecf3,#79a8be,#486777)"))
        mm=masks(item)
        out.append({"key":k or f"result_{i}","label":title(item.get("type","")),"score":round(s,1),"raw_score":item.get("raw_score"),"overlay":mm[0] if mm else "","color":c,"legend_top":t,"legend_bottom":b,"gradient":g})
    return out


def header(step: int):
    st.markdown('<div class="topbar"><div class="logo"><div class="logo-dot"></div><span>Skin Insight</span></div><div class="pill">AI skin check</div></div>',unsafe_allow_html=True)
    html='<div class="stepper">'
    for n,label in [(1,"Take a selfie"),(2,"Analyze"),(3,"Your report")]:
        cls="active" if n==step else ("done" if n<step else "")
        html+=f'<div class="step {cls}"><b>{n}</b>{label}</div>'
    st.markdown(html+'</div>',unsafe_allow_html=True)


result=st.session_state.get("skin_result")
if result:
    header(3)
    st.markdown('<div class="hero"><small>YOUR SKIN REPORT</small><h1 style="font-size:27px">Explore your results</h1><p>Tap a score to view its overlay and details.</p></div>',unsafe_allow_html=True)
    cats=categories(output_items(result))
    base=st.session_state.get("scan_preview_url","")
    if cats and base: show_result_viewer(base,cats,key="skin_results")
    else: st.warning("The analysis completed, but no displayable scores were returned.")
    if st.button("Start a new scan",type="primary",use_container_width=True):
        for k in ("skin_result","scan_image_bytes","scan_image_type","scan_image_name","scan_preview_url"): st.session_state.pop(k,None)
        st.rerun()
    with st.expander("Technical response"): st.json(result)
    st.markdown('<div class="note">Cosmetic image analysis only. Results are not a medical diagnosis.</div>',unsafe_allow_html=True)
    st.stop()

header(1)
st.markdown('<div class="hero"><small>PERSONALIZED SKIN ANALYSIS</small><h1>Discover your skin profile in a few steps</h1><p>Take a clear selfie to generate a visual skin report.</p></div>',unsafe_allow_html=True)
st.markdown('<div class="guide-title">For the clearest scan</div>',unsafe_allow_html=True)
st.markdown('<div class="guides"><div class="guide"><i>☀</i><strong>Even lighting</strong><span>Avoid strong shadows</span></div><div class="guide"><i>◉</i><strong>Look straight</strong><span>Face the camera</span></div><div class="guide"><i>⌖</i><strong>Center your face</strong><span>Keep your full face visible</span></div></div>',unsafe_allow_html=True)
st.markdown('<div class="camera-copy"><strong>Take your selfie</strong><span>No beauty filters</span></div><div class="hint">Relax your expression and keep the camera at eye level</div>',unsafe_allow_html=True)

camera_tab,upload_tab=st.tabs(["Use camera","Upload photo"])
selected=None
with camera_tab:
    x=st.camera_input("Camera",label_visibility="collapsed")
    if x is not None: selected=x
with upload_tab:
    x=st.file_uploader("Upload a selfie",type=["jpg","jpeg","png"],label_visibility="collapsed")
    if x is not None: selected=x

if selected is not None:
    image_bytes=selected.getvalue(); image_name=getattr(selected,"name","skin_scan.jpg") or "skin_scan.jpg"; image_type=getattr(selected,"type","image/jpeg") or "image/jpeg"
    st.session_state["scan_image_bytes"]=image_bytes; st.session_state["scan_image_type"]=image_type; st.session_state["scan_image_name"]=image_name; st.session_state["scan_preview_url"]=data_url(image_bytes,image_type)
    st.markdown('<div class="ready">✓ Photo ready for analysis</div>',unsafe_allow_html=True)
else:
    image_bytes=st.session_state.get("scan_image_bytes"); image_type=st.session_state.get("scan_image_type","image/jpeg"); image_name=st.session_state.get("scan_image_name","skin_scan.jpg")

st.markdown('<div class="mode">Analysis quality</div>',unsafe_allow_html=True)
quality=st.radio("Analysis quality",["Standard","HD"],horizontal=True,label_visibility="collapsed")
hd=quality=="HD"

if st.button("Analyze my skin",type="primary",disabled=image_bytes is None,use_container_width=True):
    key=api_key()
    if not key:
        st.error("The server API key is not configured. Add `SKIN_API_KEY` to your deployment variables or `.streamlit/secrets.toml`, then try again.")
    else:
        preview=st.session_state.get("scan_preview_url") or data_url(image_bytes,image_type)
        scan_slot=st.empty(); status=st.empty()
        scan_slot.markdown(f'<div class="scan"><img src="{preview}"/><div class="oval"></div><div class="line"></div><div class="scantext"><strong>Analyzing your skin</strong><span>Preparing your visual report…</span></div></div>',unsafe_allow_html=True)
        def on_poll(attempt:int,state:str): status.caption(f"Analysis status: {state} · check {attempt}")
        try:
            res=run_skin_analysis(key,image_bytes,hd=hd,filename=image_name,content_type=image_type,on_poll=on_poll)
            st.session_state["skin_result"]=res; st.session_state["scan_preview_url"]=preview; st.rerun()
        except SkinAPIError as exc:
            scan_slot.empty(); status.empty(); st.error(str(exc))
        except Exception as exc:
            scan_slot.empty(); status.empty(); st.error(f"Analysis failed: {type(exc).__name__}: {exc}")

st.markdown('<div class="note">Your image is used only to run the analysis request for this session.</div>',unsafe_allow_html=True)
