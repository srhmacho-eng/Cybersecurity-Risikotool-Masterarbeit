
import streamlit as st
import matplotlib as mpl

# FARBEN

PALETTE_DARK = {
    "bg":        "#0b1020",
    "panel":     "#11182a",
    "panel2":    "#0e1526",
    "text":      "#e6e9ef",
    "muted":     "#a0abc0",
    "border":    "#2b3a55",
    "accent":    "#4ea1ff",
    "accent2":   "#7bd88f",
    "warning":   "#ffd166",
    "danger":    "#ff7b7b",
}

PALETTE_LIGHT = {
    "bg":        "#f8f9fb",
    "panel":     "#ffffff",
    "panel2":    "#f1f3f6",
    "text":      "#1e293b",
    "muted":     "#64748b",
    "border":    "#cbd5e1",
    "accent":    "#0066cc",
    "accent2":   "#27ae60",
    "warning":   "#d97706",
    "danger":    "#dc2626",
}

def get_css(p):
    return f"""
<style>
:root {{
  --bg: {p["bg"]};
  --panel: {p["panel"]};
  --panel2: {p["panel2"]};
  --text: {p["text"]};
  --muted: {p["muted"]};
  --border: {p["border"]};
  --accent: {p["accent"]};
  --accent2: {p["accent2"]};
  --warning: {p["warning"]};
  --danger: {p["danger"]};
}}

html, body, .stApp {{
  background-color: var(--bg) !important;
  color: var(--text) !important;
}}

h1, h2, h3, h4, h5, h6 {{ color: var(--text) !important; }}
hr {{ border-color: var(--border) !important; }}

/* Sidebar */
section[data-testid="stSidebar"] {{
  background: var(--panel) !important;
  color: var(--text) !important;
  border-right: 1px solid var(--border);
}}

section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] span {{
  color: var(--text) !important;
}}

/* Cards / Container / Expander */
div[role="group"] > div[style*="border: 1px"],
section .stExpander,
.stExpander {{
  background: var(--panel) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}}

.stExpander details {{
     background-color: var(--panel) !important;
     border-radius: 12px !important;
}}
.stExpander summary {{
     background-color: var(--panel) !important;
     color: var(--text) !important;
}}
.stExpander summary:hover {{
     color: var(--accent) !important;
}}
.stExpander details > div {{
     background-color: var(--panel) !important;
     color: var(--text) !important;
}}

/* Form-Container */
form[data-testid="stForm"] {{
  background: var(--panel) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  padding: .5rem !important;
}}

div[role="button"][data-baseweb="accordion"] > div {{ background: transparent !important; }}

.streamlit-expanderHeader {{ color: var(--text) !important; background-color: var(--panel) !important; }}
.streamlit-expanderHeader:hover {{ color: var(--accent2) !important; }}

/* Text, Labels, Captions */
p, label, .stMarkdown, .stCaption, .stText {{ color: var(--text) !important; }}
small, .stCaption {{ color: var(--muted) !important; }}

/* Inputs */
div[data-baseweb="input"],
div[data-baseweb="textarea"],
div[data-baseweb="select"],
div[data-testid="stSelectbox"] > div > div {{
  background-color: var(--panel2) !important;
  color: var(--text) !important;
  border-color: var(--border) !important;
  border-radius: 10px !important;
}}

div[data-baseweb="select"] > div {{
    background-color: transparent !important;
    color: var(--text) !important;
}}

ul[data-baseweb="menu"],
div[data-baseweb="popover"] {{
    background-color: var(--panel) !important;
    border: 1px solid var(--border) !important;
}}
li[data-baseweb="menu-itemBase"] {{
    background-color: var(--panel) !important;
    color: var(--text) !important;
}}
li[data-baseweb="menu-itemBase"]:hover {{
   background-color: var(--border) !important;
}}

div[data-baseweb="select"] svg {{
    fill: var(--text) !important;
}}

/* Disabled Fields */
input:disabled,
textarea:disabled,
select:disabled {{
  color: var(--text) !important;
  -webkit-text-fill-color: var(--text) !important;
  opacity: 1 !important;
}}

[data-testid="stNumberInput"] input:disabled {{
  color: var(--text) !important;
  -webkit-text-fill-color: var(--text) !important;
  opacity: 1 !important;
}}

input, textarea, select {{
  background: transparent !important;
  color: var(--text) !important;
}}

[data-testid="stNumberInput"] {{
  background: var(--panel2) !important;
  border-radius: 10px !important;
  border: 1px solid var(--border) !important;
}}

[data-testid="stNumberInput"] * {{
  background-color: transparent !important;
  box-shadow: none !important;
}}

[data-testid="stNumberInput"] input[type="number"] {{
  color: var(--text) !important;
  border: none !important;
}}

[data-testid="stNumberInput"] button {{
  background: var(--panel) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}}
[data-testid="stNumberInput"] button:hover {{
  filter: brightness(1.08);
}}

/* Radio Buttons */
div[role="radiogroup"] label {{
  background: transparent !important;
  border: 1px solid var(--border) !important;
  border-radius: 20px !important;
  padding: 4px 10px !important;
  margin-right: 6px !important;
  color: var(--text) !important;
}}

div[role="radiogroup"] label:hover {{
  border-color: var(--accent) !important;
}}

div[role="radiogroup"] label.radio-option-ja {{
  border-color: #4caf50 !important;
}}
div[role="radiogroup"] label.radio-option-ja:has(input:checked),
div[role="radiogroup"] label.radio-option-ja[data-checked="true"] {{
  background: #4caf50 !important;
  border-color: #4caf50 !important;
  color: white !important;
}}

div[role="radiogroup"] label.radio-option-teilweise {{
  border-color: #ffc107 !important;
}}
div[role="radiogroup"] label.radio-option-teilweise:has(input:checked),
div[role="radiogroup"] label.radio-option-teilweise[data-checked="true"] {{
  background: #ffc107 !important;
  border-color: #ffc107 !important;
  color: #000 !important;
}}

div[role="radiogroup"] label.radio-option-nein {{
  border-color: #f44336 !important;
}}
div[role="radiogroup"] label.radio-option-nein:has(input:checked),
div[role="radiogroup"] label.radio-option-nein[data-checked="true"] {{
  background: #f44336 !important;
  border-color: #f44336 !important;
  color: white !important;
}}

div[role="radiogroup"] label.radio-option-keine-angabe {{
  border-color: #9e9e9e !important;
}}
div[role="radiogroup"] label.radio-option-keine-angabe:has(input:checked),
div[role="radiogroup"] label.radio-option-keine-angabe[data-checked="true"] {{
  background: #9e9e9e !important;
  border-color: #9e9e9e !important;
  color: white !important;
}}

div[role="radiogroup"] label:has(input:checked):not(.radio-option-ja):not(.radio-option-teilweise):not(.radio-option-nein):not(.radio-option-keine-angabe) {{
  background: var(--accent) !important;
  border-color: var(--accent) !important;
  color: #ffffff !important;
}}

/* File Uploader */
[data-testid="stFileUploader"] {{
  background: var(--panel2) !important;
  border: 1px dashed var(--border) !important;
  border-radius: 12px !important;
}}
[data-testid="stFileUploader"] * {{
  color: var(--text) !important;
}}

[data-testid="stFileUploaderDropzone"] {{
  background: var(--panel2) !important;
  border: 1px dashed var(--border) !important;
  border-radius: 12px !important;
}}
[data-testid="stFileUploaderDropzone"] div {{
  background: transparent !important;
}}
[data-testid="stFileUploader"] section {{
  background: transparent !important;
}}

[data-testid="stFileUploader"] button {{
  background: var(--panel2) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
}}

/* Buttons */
.stButton>button,
.stDownloadButton>button {{
  background: var(--panel) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  transition: transform .08s ease, filter .15s ease;
}}
.stButton>button:hover,
.stDownloadButton>button:hover {{
  filter: brightness(0.95);
  border-color: var(--accent) !important;
}}

div[data-testid="stFormSubmitButton"] button {{
  background: var(--panel) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
}}

/* Scrollbar */
::-webkit-scrollbar {{ width: 8px; height: 8px; }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 4px; }}

header, [data-testid="stHeader"] {{
    visibility: hidden !important;
    height: 0 !important;
}}

.stTabs [data-baseweb="tab-list"] {{ background-color: transparent !important; }}
.stTabs [data-baseweb="tab"] {{
    background-color: var(--panel2) !important; 
    color: var(--muted) !important;
}}
.stTabs [data-baseweb="tab"][aria-selected="true"] {{
    background-color: var(--panel) !important;
    color: var(--accent) !important;
    border-bottom: 3px solid var(--accent) !important;
}}
</style>
"""

def init_theme_state():
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True

def render_toggle(position_col=None, button_key="theme_toggle"):
    init_theme_state()
    label = "🌙 Dark Mode" if not st.session_state.dark_mode else "☀️ Light Mode"
    
    if position_col is None:
        new_val = st.toggle(label, value=st.session_state.dark_mode, key=button_key)
        if new_val != st.session_state.dark_mode:
            st.session_state.dark_mode = new_val
            st.rerun()
    else:
        with position_col:
            new_val = st.toggle(label, value=st.session_state.dark_mode, key=button_key)
            if new_val != st.session_state.dark_mode:
                st.session_state.dark_mode = new_val
                st.rerun()
    return False

def apply_theme():
    init_theme_state()
    p = PALETTE_DARK if st.session_state.dark_mode else PALETTE_LIGHT
    st.markdown(get_css(p), unsafe_allow_html=True)

def apply_matplotlib_theme():
    init_theme_state()
    p = PALETTE_DARK if st.session_state.dark_mode else PALETTE_LIGHT
    mpl.rcParams.update({
        "figure.facecolor": p["bg"],
        "axes.facecolor":   p["panel"],
        "axes.edgecolor":   p["border"],
        "axes.labelcolor":  p["text"],
        "xtick.color":      p["text"],
        "ytick.color":      p["text"],
        "grid.color":       p["border"],
        "text.color":       p["text"],
    })
