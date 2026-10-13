from html import escape
import streamlit as st
import plotly.graph_objects as go

# Preserve the existing dark design; translate its presentation colours for light mode.
LIGHT_COLORS = {
    '#DFE7F1':'#22354A', '#91A1B6':'#52667C', '#6CDAC4':'#087F70',
    '#121D2C':'#FFFFFF', '#0B1320':'#F5F7FA', '#0F1928':'#EBF0F5',
    '#253145':'#D3DDE7', '#F1F5FA':'#172D43', '#263448':'#D6E0E9',
    '#98A9BE':'#52667C', '#EFF5FB':'#172D43', '#2B3A4F':'#D3DDE7',
    '#101B2A':'#FFFFFF', '#EDF5FC':'#172D43', '#263449':'#D3DDE7',
    '#A9B7C9':'#52667C', '#30463F':'#AACDC5', '#152B28':'#E4F3EE',
    '#91DDC7':'#176856', '#2A384A':'#D3DDE7', '#131F30':'#FFFFFF',
    '#E8F0F8':'#172D43', '#A7B6C9':'#52667C', '#8194AB':'#52667C',
    '#172738':'#EEF3F7', '#30445B':'#CCD9E5', '#101B2B':'#FFFFFF',
    '#B5C4D7':'#354E65', '#23354A':'#F0F4F8', '#223147':'#E1E8EF',
    '#ECF4FC':'#172D43', '#233246':'#E1E8EF', '#1A3A38':'#DAEEE6',
    '#45302C':'#F7E2D9', '#D8E5F3':'#243F55', '#52657B':'#75899C',
    '#3B5065':'#A0AFBE', '#DCE9F7':'#243F55', '#FFFFFF':'#172D43',
    '#162738':'#EDF5F4', '#3A9D90':'#218578', '#789ECB':'#466FA1',
    '#59BFA6':'#16826B', '#D7B45A':'#8A680D', '#E9985E':'#B7571D',
    '#E56F7C':'#B23E55', '#8E9BAE':'#617489',
    'RGBA(11,19,32,.95)':'rgba(245,247,250,.95)',
    'RGBA(108,218,196,.07)':'rgba(8,127,112,.07)',
}


def is_light():
    return st.get_option('theme.base') == 'light'


def light_value(value):
    if isinstance(value, str):
        return LIGHT_COLORS.get(value.upper(), value)
    if isinstance(value, dict):
        return {key:light_value(item) for key,item in value.items()}
    if isinstance(value, (list,tuple)):
        return [light_value(item) for item in value]
    return value

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
    css=CSS
    if is_light():
        # One substitution pass prevents replacement colours being translated again.
        import re
        css=re.sub(r'#[0-9A-Fa-f]{6}|rgba\([^)]*\)',
                   lambda match:light_value(match.group()),css)
        # The existing risk badge uses an inline colour; adapt it without changing views.
        overrides=''.join(
            f'.risk-badge[style*="{old}"] {{color:{LIGHT_COLORS[old]} !important;}}'
            for old in ('#59BFA6','#D7B45A','#E9985E','#E56F7C'))
        css=css.replace('</style>',overrides+'</style>')
    st.markdown(css, unsafe_allow_html=True)


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
    if is_light():
        fig=go.Figure(light_value(fig.to_plotly_json()))
        fig.update_layout(template='plotly_white')
    st.plotly_chart(fig, width='stretch', key=key,
                    config={'displaylogo': False, 'scrollZoom': False})
