from html import escape
import streamlit as st

CSS = '''
<style>
:root {--ink:#DFE7F1; --dim:#91A1B6; --teal:#6CDAC4; --panel:#121D2C;}
.stApp {background:#0B1320; color:var(--ink);}
[data-testid="stSidebar"] {background:#0F1928; border-right:1px solid #253145;}
[data-testid="stHeader"] {background:rgba(11,19,32,.95);}
.block-container {max-width:1550px; padding-top:2rem; padding-bottom:3rem;}
h1,h2,h3 {font-family:'Segoe UI',sans-serif; letter-spacing:-.025em; color:#F1F5FA;}
h1 {font-size:2rem!important;} h2 {font-size:1.25rem!important;} h3 {font-size:1.05rem!important;}
p,span,label {font-family:'Segoe UI',sans-serif;}
[data-testid="stMetric"] {border:1px solid #263448; border-radius:12px; padding:16px 18px; background:#121D2C;}
[data-testid="stMetricLabel"] {color:#98A9BE; font-size:.8rem;}
[data-testid="stMetricValue"] {font-size:1.8rem; color:#EFF5FB; font-weight:600;}
[data-testid="stCaptionContainer"] {color:#91A1B6;}
[data-testid="stExpander"] {border-color:#2B3A4F; background:#101B2A;}
.eyebrow {color:#6CDAC4; font-size:.68rem; font-weight:700; letter-spacing:.18em; margin-bottom:8px;}
.brand {font-size:1.13rem; font-weight:700; letter-spacing:.04em; color:#EDF5FC; margin-bottom:4px;}
.brand small {color:#6CDAC4; font-size:.7rem; letter-spacing:.2em; display:block; margin-top:4px;}
.hero {border-bottom:1px solid #263449; padding:0 0 20px; margin-bottom:22px;}
.hero h1 {margin:0 0 7px; padding:0;}
.hero p {color:#A9B7C9; max-width:900px; margin:0; font-size:.94rem;}
.status {display:inline-block; border:1px solid #30463F; background:#152B28; color:#91DDC7;
 padding:5px 10px; border-radius:30px; font-size:.7rem; letter-spacing:.06em; margin-bottom:14px;}
.panel {border:1px solid #2A384A; border-radius:12px; background:#131F30; padding:18px 22px; margin:12px 0;}
.panel strong {color:#E8F0F8;} .panel p {margin:7px 0 0; color:#A7B6C9; font-size:.88rem;}
.section-label {color:#8194AB; font-size:.7rem; letter-spacing:.13em; margin:22px 0 10px; font-weight:600;}
.risk-badge {display:inline-block; border:1px solid currentColor; padding:6px 13px; border-radius:6px; font-weight:650; font-size:.8rem;}
.architecture {display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin:20px 0;}
.architecture span {padding:11px 13px; background:#172738; border:1px solid #30445B; border-radius:7px; font-size:.8rem;}
.architecture i {color:#6CDAC4; font-style:normal;}
[data-testid="stTabs"] {margin-top:14px;}
@media(max-width:760px) {.block-container{padding:1rem;} h1{font-size:1.5rem!important;}}
</style>'''


def apply_theme():
    st.markdown(CSS, unsafe_allow_html=True)


def header(title, subtitle, active=False):
    status = 'REPLAY ACTIVE' if active else 'HISTORICAL DATASET • REPLAY READY'
    st.markdown(f'<div class="hero"><div class="eyebrow">TEMPORAL GNN / TRANSACTION RISK INTELLIGENCE</div>'
                f'<div class="status">● {status}</div><h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div>',
                unsafe_allow_html=True)


def panel(title, text):
    st.markdown(f'<div class="panel"><strong>{escape(title)}</strong><p>{escape(text)}</p></div>', unsafe_allow_html=True)


def section(text):
    st.markdown(f'<div class="section-label">{escape(text.upper())}</div>', unsafe_allow_html=True)


def table(frame):
    st.dataframe(frame, hide_index=True, width='stretch')


def chart(fig, key):
    st.plotly_chart(fig, width='stretch', key=key,
                    config={'displaylogo': False, 'scrollZoom': False})
