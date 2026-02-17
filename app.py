# Hauptanwendung Streamlit
import os
import json
from io import BytesIO
from datetime import datetime

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Eigene Module laden
from intake_flow import (
    render_small_questionnaire,
    render_large_questionnaire,
    make_profile,
    PROFILE_FIELDS,
    SMALL_FIELDS,
)
from risk_engine import base_scores, apply_modifiers, risk_score, ProfileView
from pdf_export import HAS_REPORTLAB, build_pdf_report

from recommender import (
    load_catalog,
    enrich_with_policies,
    llm_actions_from_policy_hits,
    build_query_for_policy
)
from policy_search import PolicySearch
import theme

# Speicher-Status (Session)
if "small_profile" not in st.session_state:
    st.session_state.small_profile = {}

if "large_profile" not in st.session_state:
    st.session_state.large_profile = {}

if "analysis_mode" not in st.session_state:
    st.session_state.analysis_mode = "small"

if "edit_small" not in st.session_state:
    st.session_state.edit_small = False

if "edit_large" not in st.session_state:
    st.session_state.edit_large = False

if "rec_cache" not in st.session_state:
    st.session_state.rec_cache = {}
if "completed_actions" not in st.session_state:
    st.session_state.completed_actions = set()

if "save_success_trigger" not in st.session_state:
    st.session_state.save_success_trigger = False

if "risk_calculation_mode" not in st.session_state:
    st.session_state.risk_calculation_mode = "average"

if "risk_weight_likelihood" not in st.session_state:
    st.session_state.risk_weight_likelihood = 50
if "risk_weight_impact" not in st.session_state:
    st.session_state.risk_weight_impact = 50

if "fine_tuning_assets" not in st.session_state:
    st.session_state.fine_tuning_assets = {}
if "fine_tuning_threats" not in st.session_state:
    st.session_state.fine_tuning_threats = {}
if "show_fine_tuning" not in st.session_state:
    st.session_state.show_fine_tuning = False
if "widget_version" not in st.session_state:
    st.session_state.widget_version = 0
if "fine_tuning_version" not in st.session_state:
    st.session_state.fine_tuning_version = 0


# PDF-Libs 
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        Image as RLImage,
    )
    from reportlab.lib.styles import getSampleStyleSheet
    HAS_REPORTLAB = True
except:
    HAS_REPORTLAB = False


# Grundlayout 
st.set_page_config(page_title="Risikoanalyse", layout="wide")
theme.init_theme_state()


# Hilfsfunktion für Export
def _export_answers(profile_dict: dict):
    return json.dumps(profile_dict, indent=2, ensure_ascii=False).encode("utf-8")


@st.cache_data(show_spinner=False)
def cached_catalog():
    return load_catalog()

@st.cache_resource(show_spinner=False)
def cached_policy():
    os.makedirs("policies", exist_ok=True)
    return PolicySearch("policies")

catalog = cached_catalog()
policy_search = cached_policy()

# SIDEBAR
st.sidebar.title("📁 Datenverwaltung")

mode = st.session_state.get("analysis_mode", "small")
active_profile = (
    st.session_state.small_profile
    if mode == "small"
    else st.session_state.large_profile
)

st.sidebar.markdown(
    f"**Aktives Profil:** { 'Kleiner Fragebogen' if mode=='small' else 'Großer Fragebogen' }"
)
st.sidebar.markdown("---")


# EXPORT / IMPORT
with st.sidebar.expander("📤  Import & Export", expanded=False):
    st.subheader("Profil exportieren")
    
    st.download_button(
        "📤 Profil exportieren (.json)",
        data=_export_answers(active_profile),
        file_name="profil.json",
        mime="application/json",
        use_container_width=True,
    )
    
    st.markdown("---")
    st.subheader("Profil importieren")
    
    imp = st.file_uploader("JSON-Datei auswählen", type=["json"])
    
    import_target = st.radio(
        "Import-Ziel:",
        ["Kleiner Fragebogen", "Großer Fragebogen", "Beide"],
        index=2,
        help="Legen Sie fest, in welches Profil die Daten importiert werden sollen. 'Beide' übernimmt die Daten für den kleinen und großen Fragebogen."
    )
    
    if st.button("📥 Import laden", use_container_width=True, disabled=(imp is None)):
        try:
            raw = imp.read().decode("utf-8")
            payload = json.loads(raw)
    
            new_profile = {fid: None for fid in PROFILE_FIELDS}
    
            INT_MIN_1_FIELDS = {"employees"}
            for fid, meta in PROFILE_FIELDS.items():
                raw_val = payload.get(fid, None)
    
                if meta["type"] in ("int", "float"):
                    if fid in INT_MIN_1_FIELDS:
                        minval = 1
                        if raw_val in (None, "", "None"):
                            new_profile[fid] = minval
                        else:
                            try:
                                v = int(float(raw_val))
                                new_profile[fid] = v if v >= minval else minval
                            except Exception:
                                new_profile[fid] = minval
                    else:
                        if raw_val in (None, "", "None"):
                            new_profile[fid] = 0
                        elif isinstance(raw_val, str) and raw_val.lower() in ("ja", "yes"):
                            new_profile[fid] = 0
                        elif isinstance(raw_val, str) and raw_val.lower() in ("nein", "no"):
                            new_profile[fid] = 1
                        elif isinstance(raw_val, str) and raw_val.lower() in ("teilweise", "partly", "teilw.", "teilw"):
                            new_profile[fid] = 0.5
                        else:
                            try:
                                v = float(raw_val)
                                new_profile[fid] = v if v in (1, 0.5, 0) else 0
                            except Exception:
                                new_profile[fid] = 0
                else:
                    new_profile[fid] = raw_val
    
           
            targets = []
            if import_target == "Beide":
                targets = ["small", "large"]
            elif import_target == "Kleiner Fragebogen":
                targets = ["small"]
            elif import_target == "Großer Fragebogen":
                targets = ["large"]

            for t in targets:
                st.session_state[f"{t}_profile"] = new_profile.copy()
                st.session_state[f"edit_{t}"] = True
            
            
            st.session_state.completed_actions = set()
            st.session_state.rec_cache = {}
            st.session_state.risk_results = {}
            st.session_state.widget_version += 1
    
            st.session_state.save_success_trigger = "Profil importiert – bitte im Fragebogen auf 'Speichern' drücken."
            st.rerun()
    
        except Exception as e:
            st.error(f"Import fehlgeschlagen: {e}")

# POLICY-INDEX / LIST
with st.sidebar.expander("📚 Policies & Index", expanded=False):
    st.subheader("Policy-Index aktualisieren")
    
    if st.button("🔄 Index neu aufbauen", use_container_width=True):
        try:
            st.session_state.pop("policy_search", None)
            st.cache_resource.clear()
    
            policy_search = cached_policy()
    
            st.success("Policy-Index erfolgreich aktualisiert.")
            st.rerun()
    
        except Exception as e:
            st.error(f"Fehler beim Aktualisieren: {e}")
            
    st.markdown("---")
    st.subheader("Geladene Policies")
    
    try:
        ps = policy_search  
    except:
        ps = cached_policy()
    
    policy_files = ps.list_files() if hasattr(ps, "list_files") else None
    
    if not policy_files:
        st.info("Keine Policies gefunden.")
    else:
        for f in policy_files:
            st.markdown(f"- **{f}**")


col_head, col_theme = st.columns([7, 1])
with col_head:
    st.markdown("""
        <div style="padding: 1rem 0; margin-bottom: 1rem;">
            <h1 style="
                font-family: 'Outfit', 'Inter', sans-serif;
                font-size: 3rem;
                font-weight: 800;
                background: linear-gradient(90deg, #4ea1ff 0%, #7bd88f 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0;
                letter-spacing: -1px;
            ">
                Risikoanalyse <span style="font-weight: 300; opacity: 0.8;">für KMU</span>
            </h1>
            <p style="
                color: var(--muted);
                font-size: 1.1rem;
                margin-top: -5px;
                font-weight: 400;
            ">
                Schwachstellenerhebung, Risikoanalyse und Handlungsempfehlungen für KMU
            </p>
        </div>
    """, unsafe_allow_html=True)
theme.render_toggle(position_col=col_theme)
theme.apply_theme()
theme.apply_matplotlib_theme()


st.markdown("""
<style>
div.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #4ea1ff 0%, #3498db 100%) !important;
    border: none !important;
    color: white !important;
    box-shadow: 0px 4px 10px rgba(78, 161, 255, 0.3) !important;
}
div.stButton > button[kind="secondary"] {
    background-color: var(--panel2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
}
div.stButton > button:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px);
}
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1,1])

with col1:
    type_small = "primary" if st.session_state.analysis_mode == "small" else "secondary"
    label_small = "Kompakt-Check" if st.session_state.analysis_mode == "small" else "Kompakt-Check"
    if st.button(label_small, use_container_width=True, type=type_small, key="mode_select_small"):
        st.session_state.analysis_mode = "small"
        st.rerun()

with col2:
    type_large = "primary" if st.session_state.analysis_mode == "large" else "secondary"
    label_large = "Vollständige Analyse" if st.session_state.analysis_mode == "large" else "Vollständige Analyse"
    if st.button(label_large, use_container_width=True, type=type_large, key="mode_select_large"):
        st.session_state.analysis_mode = "large"
        st.rerun()

st.markdown("---")

# HAUPTNAVIGATION: TABS
tab_questionnaire, tab_evaluation, tab_recommendations = st.tabs([
    "📝 Fragebogen", 
    "📊 Risiko-Evaluation", 
    "🛠 Handlungsempfehlungen"
])

# TAB 1: FRAGEBOGEN
with tab_questionnaire:
    mode = st.session_state.analysis_mode

    if st.session_state.save_success_trigger:
        msg = st.session_state.save_success_trigger
        if msg is True: msg = "Gespeichert"
        st.success(msg)
        st.session_state.save_success_trigger = False

    if mode == "small":
        st.markdown(f"### <span style='color: #4ea1ff;'>📋</span> Kleiner Fragebogen", unsafe_allow_html=True)
        st.caption("Einfach & schnell.")

        if not st.session_state.edit_small:
            if st.button("Bearbeiten"):
                st.session_state.edit_small = True
                st.rerun()

        with st.form("form_small"):
            newvals = render_small_questionnaire(
                st.session_state.small_profile,
                st.session_state.edit_small
            )
            submitted = st.form_submit_button("Speichern")
            if submitted:
                st.session_state.edit_small = False
                for fid, val in newvals.items():
                    st.session_state.small_profile[fid] = val
                st.session_state.save_success_trigger = True
                st.rerun()

    elif mode == "large":
        st.markdown(f"### <span style='color: #7bd88f;'>📑</span> Großer Fragebogen", unsafe_allow_html=True)
        st.caption("Alle Aspekte der Cybersicherheit.")

        if not st.session_state.edit_large:
            if st.button("Bearbeiten"):
                st.session_state.edit_large = True
                st.rerun()

        with st.form("form_large"):
            newvals = render_large_questionnaire(
                st.session_state.large_profile,
                st.session_state.edit_large
            )
            submitted = st.form_submit_button("Speichern")
            if submitted:
                st.session_state.edit_large = False
                for fid, val in newvals.items():
                    st.session_state.large_profile[fid] = val
                st.session_state.save_success_trigger = True
                st.rerun()


# BERECHNUNG
mode = st.session_state.analysis_mode

profile_raw = (
    st.session_state.small_profile 
    if mode == "small"
    else st.session_state.large_profile
)

profile_calc = make_profile(profile_raw)
pview = ProfileView(**profile_calc)

is_critical = profile_raw.get("is_critical_infrastructure")
if (is_critical == 0.0 or is_critical is True) and st.session_state.risk_calculation_mode != "maximum":
    st.session_state.risk_calculation_mode = "maximum"

# Szenarien generieren 
rows = []
vulns = catalog["vulnerabilities"]
assets = catalog["assets"]
threats = catalog["threats"]

VULN_FIELD_MAP = {
    "V_SECURITY_ROLE_MISSING": "has_security_role",
    "V_SECURITY_POLICIES_MISSING": "has_security_policies",
    "V_POLICIES_NOT_REVIEWED": "policies_reviewed",
    "V_NO_ASSET_INVENTORY": "has_asset_inventory",
    "V_NO_INCIDENT_PLAN": "has_incident_plan",
    "V_NO_ACCESS_LIST": "access_list_exists",
    "V_ACCESS_LIST_NOT_REVIEWED": "access_list_reviewed",
    "V_NO_AUDITS": "audits_done",

    "V_MFA_MISSING": "has_mfa",
    "V_WEAK_PASSWORD_POLICY": "has_password_rules",
    "V_NO_PASSWORD_MANAGER": "has_password_manager",
    "V_NO_LEAST_PRIVILEGE": "has_least_privilege",
    "V_OLD_ACCOUNTS_ACTIVE": "inactive_accounts_removed",
    "V_NO_ACCOUNT_LIFECYCLE": "has_account_lifecycle",
    "V_ADMIN_ACCOUNTS_WEAK": "admin_accounts_protected",
    "V_NO_SSO": "has_sso",
    "V_LOGIN_MONITORING_MISSING": "login_monitoring",

    "V_PATCH_MISSING": "has_patch_mgmt",
    "V_NO_VULN_SCAN": "has_vuln_scans",
    "V_EDR_MISSING": "has_edr",
    "V_FIREWALL_MISSING": "has_firewall",
    "V_NO_SEGMENTATION": "network_segmented",
    "V_NO_MDM": "has_mdm",
    "V_LOGGING_DISABLED": "logging_enabled",
    "V_LOGS_NOT_REVIEWED": "logs_reviewed",
    "V_NO_IDS_IPS": "has_ids_ips",

    "V_BACKUP_DAILY_MISSING": "daily_backups",
    "V_NO_OFFSITE_BACKUP": "has_offsite_backup",
    "V_BACKUP_UNTESTED": "backup_tested",
    "V_DEVICE_NOT_PROTECTED": "device_loss_protection",

    "V_CLOUD_CONFIG_WEAK": "cloud_config_secure",
    "V_CLOUD_MFA_MISSING": "cloud_mfa_enabled",
    "V_CLOUD_LOGGING_MISSING": "cloud_logging",
    "V_CLOUD_PUBLIC_SHARES": "cloud_shares_controlled",
    "V_CLOUD_PERMISSIONS_UNCHECKED": "cloud_permissions_reviewed",
    "V_CLOUD_POLICY_MISSING": "cloud_policy_exists",
    "V_CLOUD_CONFIG_UNTESTED": "cloud_config_tested",
    "V_CLOUD_DLP_MISSING": "cloud_dlp",
    "V_CLOUD_NOT_USED": "uses_cloud",

    "V_NO_TRAINING": "has_training",
    "V_NO_PHISHING_TESTS": "has_phishing_tests",
    "V_LOW_AWARENESS": "email_awareness",
    "V_NO_INCIDENT_REPORTING": "has_incident_reporting",
    "V_NO_BYOD_RULES": "has_byod_rules",
    "V_NO_MOBILE_POLICY": "has_mobile_device_policy",

    "V_NO_DATA_CLASSIFICATION": "has_data_classification",
    "V_GDPR_NON_COMPLIANT": "gdpr_compliant",
    "V_NO_RETENTION_RULES": "data_retention_rules",
    "V_DATA_UNENCRYPTED_REST": "data_encrypted_at_rest",
    "V_DATA_UNENCRYPTED_TRANSIT": "data_encrypted_in_transit",
    "V_VENDOR_NOT_CHECKED": "vendors_checked",
    "V_VENDOR_NO_AVV": "vendors_have_avv",
}

for v in vulns:
    vid = v["id"]
    
    
    if vid in st.session_state.get("completed_actions", set()):
        continue

    field = VULN_FIELD_MAP.get(vid)
    control_weight = None
    
    if field is not None:
        val = profile_raw.get(field)
        if val is None:
            continue
        if val == 0.0 or val is True:
            continue
        elif val == 0.5:
            control_weight = 0.5
        elif val == 1.0 or val is False:
            control_weight = 1.0

    v_assets = v.get("assets", [])
    v_threats = v.get("threats", [])

    for a in assets:
        if a["id"] not in v_assets:
            continue

        for t in threats:
            if t["id"] not in v_threats:
                continue
            
            custom_assets = st.session_state.fine_tuning_assets if st.session_state.fine_tuning_assets else None
            custom_threats = st.session_state.fine_tuning_threats if st.session_state.fine_tuning_threats else None
            
            base = base_scores(a["id"], t["id"], vid, custom_assets, custom_threats)
            mod = apply_modifiers(base, pview, t["id"], vid, control_weight)
            score = risk_score(mod["likelihood"], mod["impact"])

            rows.append({
                "VulnID": vid,
                "Schwachstelle": v["name"],
                "AssetID": a["id"],
                "Asset": a["name"],
                "ThreatID": t["id"],
                "Threat": t["name"],
                "Likelihood": mod["likelihood"],
                "Impact": mod["impact"],
                "Risikoscore": score
            })

df = pd.DataFrame(rows)

def make_cell_expander(title, items):
    li_items = "".join([f"<li>{i}</li>" for i in items])
    html = f"<details><summary style='cursor:pointer; color:#4ea1ff; font-weight:500;'>{title}</summary><ul style='margin-left:15px;'>{li_items}</ul></details>"
    return html

def clean(x):
    return x.replace("\\n", "") if isinstance(x, str) else x

calc_mode = st.session_state.risk_calculation_mode

total_weight = st.session_state.risk_weight_likelihood + st.session_state.risk_weight_impact
if total_weight > 0:
    weight_likelihood_norm = st.session_state.risk_weight_likelihood / 100.0
    weight_impact_norm = st.session_state.risk_weight_impact / 100.0
else:
    weight_likelihood_norm = 0.5
    weight_impact_norm = 0.5

vuln_df = pd.DataFrame()
vuln_df_clean = pd.DataFrame()

if not df.empty:
    vuln_rows = []
    for vid in df["VulnID"].unique():
        sub = df[df["VulnID"] == vid]
        vuln_name = sub["Schwachstelle"].iloc[0]
        threat_pairs = sub[["Threat", "Likelihood"]].drop_duplicates().values
        threat_items = [f"{tname} (Wahrscheinlichkeit {tlh})" for tname, tlh in threat_pairs]
        avg_likelihood = sub["Likelihood"].mean()
        asset_pairs = sub[["Asset", "Impact"]].drop_duplicates().values
        asset_items = [f"{aname} (Impact {imp})" for aname, imp in asset_pairs]
        
        if calc_mode == "maximum":
            impact = sub["Impact"].max()
            impact_label = "Max_Impact"
        else:
            impact = sub["Impact"].mean()
            impact_label = "Avg_Impact"
        
        risk = (weight_likelihood_norm * avg_likelihood) + (weight_impact_norm * impact)

        vuln_rows.append({
            "VulnID": vid,
            "Schwachstelle": vuln_name,
            "Threats_cell": make_cell_expander("anzeigen", threat_items),
            "Assets_cell": make_cell_expander("anzeigen", asset_items),
            "ThreatNames": list(sub["Threat"].unique()),
            "AssetNames": list(sub["Asset"].unique()),
            "Avg_Likelihood": round(avg_likelihood, 2),
            impact_label: round(impact, 2),
            "Risk": round(risk, 2)
        })

    vuln_df = pd.DataFrame(vuln_rows)
    
    if "Max_Impact" in vuln_df.columns:
        vuln_df["Avg_Impact"] = vuln_df["Max_Impact"]
        vuln_df = vuln_df.drop(columns=["Max_Impact"])
    
    if not vuln_df.empty:
        vuln_df = vuln_df.sort_values("Risk", ascending=False)
        vuln_df.insert(0, "Nr", range(1, len(vuln_df) + 1))
        vuln_df_clean = vuln_df.applymap(clean)


# HTML CSS für Tabellen 
dark_mode = st.session_state.get("dark_mode", False)
if not dark_mode:
    table_css = """
    <style>
    table {
        border-collapse: collapse;
        width: 100%;
        font-size: 14px;
        background-color: #ffffff !important;
        color: #222222 !important;
    }
    th {
        background-color: #f2f2f2 !important;
        color: #222222 !important;
        padding: 8px !important;
        border-bottom: 2px solid #cccccc !important;
        text-align: left !important;
    }
    td {
        padding: 6px 8px;
        border-bottom: 1px solid #e0e0e0;
        color: #222222 !important;
    }
    tr:nth-child(even) { background-color: #fafafa; }
    tr:nth-child(odd)  { background-color: #ffffff; }
    tr:hover { background-color: #eeeeee; }
    details summary {
        color: #0066cc !important;
        font-weight: 500;
    }
    </style>
    """
else:
    table_css = """
    <style>
    table {
        border-collapse: collapse;
        width: 100%;
        font-size: 14px;
        background-color: #0f1626 !important;
        color: #d8dbe2 !important;
    }
    th {
        background-color: #141a2a !important;
        color: #e6e9ef !important;
        padding: 8px !important;
        border-bottom: 2px solid #2b3a55 !important;
        text-align: left !important;
    }
    td {
        padding: 6px 8px;
        border-bottom: 1px solid #2b3a55;
        color: #d8dbe2 !important;
    }
    tr:nth-child(even) { background-color: #0f1626; }
    tr:nth-child(odd)  { background-color: #111827; }
    tr:hover { background-color: #1e2a44; }
    details summary {
        color: #4ea1ff !important;
        font-weight: 500;
    }
    </style>
    """
st.markdown(table_css, unsafe_allow_html=True)


# Matrix-Render-Funktion 
def render_matrix(df, calc_mode="average"):
    import plotly.graph_objects as go
    import numpy as np

    zones = np.zeros((5, 5))
    for i in range(5):
        for j in range(5):
            val = (i + 1) * (j + 1)
            zones[i, j] = 2 if val >= 20 else (1 if val >= 12 else 0)
    
    colorscale = [
        [0.0, '#27ae60'],
        [0.33, '#2ecc71'],
        [0.5, '#f1c40f'],
        [0.66, '#e67e22'],
        [1.0, '#c0392b']
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Heatmap(
        z=zones,
        x=[1, 2, 3, 4, 5],
        y=[1, 2, 3, 4, 5],
        colorscale=colorscale,
        showscale=False,
        hoverinfo='skip',
        zmin=0,
        zmax=2
    ))
    
    cell_map = {}
    vuln_names = {}
    
    def round_05(v):
        return int(float(v) * 2 + 0.5) / 2.0

    for _, row in df.iterrows():
        impact_val = row.get("Max_Impact") if calc_mode == "maximum" and "Max_Impact" in row else row.get("Avg_Impact")
        
        if pd.isna(impact_val) or pd.isna(row["Avg_Likelihood"]):
            continue

        x = round_05(impact_val)
        y = round_05(row["Avg_Likelihood"])

        x = max(1, min(5, x))
        y = max(1, min(5, y))

        nr = int(row["Nr"])
        cell_map.setdefault((x, y), []).append(nr)
        vuln_names[nr] = row.get("Schwachstelle", row.get("Threat", row.get("Asset", f"Item {nr}")))
    
    for (x, y), nrs in cell_map.items():
        if len(nrs) == 1:
            hover_text = f"<b>#{nrs[0]}</b><br>{vuln_names[nrs[0]]}"
            label_text = str(nrs[0])
            font_size = 13
        elif len(nrs) == 2:
            hover_text = "<br>".join([f"<b>#{n}</b>: {vuln_names[n]}" for n in nrs])
            label_text = "&".join(str(n) for n in nrs)
            font_size = 10 if len(label_text) > 2 else 12
        else:
            hover_text = "<b>Mehrfachbelegung:</b><br>" + "<br>".join([f"<b>#{n}</b>: {vuln_names[n]}" for n in sorted(nrs)])
            label_text = f"{len(nrs)}×"
            font_size = 11
        
        fig.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode='markers+text',
            marker=dict(
                size=26, 
                color='white', 
                line=dict(color='#2c3e50', width=2.5),
                opacity=0.95
            ),
            text=label_text,
            textposition='middle center',
            textfont=dict(size=font_size, color='#2c3e50', family='Arial Black'),
            hovertext=hover_text,
            hoverinfo='text',
            hoverlabel=dict(
                bgcolor='#2c3e50',
                font=dict(size=13, color='white', family='Arial'),
                bordercolor='white'
            ),
            showlegend=False
        ))
    
    grid_color = '#d0d0d0' if not st.session_state.get("dark_mode", False) else '#555555'
    
    for i in [1.5, 2.5, 3.5, 4.5]:
        fig.add_shape(
            type="line",
            x0=i, x1=i,
            y0=0.5, y1=5.5,
            line=dict(color=grid_color, width=0.5),
            layer="above"
        )
    
    for i in [1.5, 2.5, 3.5, 4.5]:
        fig.add_shape(
            type="line",
            x0=0.5, x1=5.5,
            y0=i, y1=i,
            line=dict(color=grid_color, width=0.5),
            layer="above"
        )
    
    dark = st.session_state.get("dark_mode", False)
    if dark:
        bg_color = theme.PALETTE_DARK["bg"]
        text_color = theme.PALETTE_DARK["text"]
        grid_color = theme.PALETTE_DARK["border"]
    else:
        bg_color = theme.PALETTE_LIGHT["bg"]
        text_color = theme.PALETTE_LIGHT["text"]
        grid_color = theme.PALETTE_LIGHT["border"]
    
    impact_label = "Max Impact" if calc_mode == "maximum" else "Impact"
    
    fig.update_layout(
        xaxis=dict(
            title=dict(
                text=f"<b>Auswirkung ({impact_label})</b>",
                font=dict(size=15, color=text_color)
            ),
            tickmode='array',
            tickvals=[1, 2, 3, 4, 5],
            ticktext=['1', '2', '3', '4', '5'],
            range=[0.5, 5.5],
            color=text_color,
            showgrid=True,
            gridcolor=grid_color,
            gridwidth=0.5,
            zeroline=False,
            tickfont=dict(size=13),
            showline=True,
            linewidth=1.5,
            linecolor=grid_color,
            mirror=True,
            scaleanchor="y",
            scaleratio=1
        ),
        yaxis=dict(
            title=dict(
                text="<b>Eintrittswahrscheinlichkeit (Likelihood)</b>",
                font=dict(size=15, color=text_color)
            ),
            tickmode='array',
            tickvals=[1, 2, 3, 4, 5],
            ticktext=['1', '2', '3', '4', '5'],
            range=[0.5, 5.5],
            color=text_color,
            showgrid=True,
            gridcolor=grid_color,
            gridwidth=0.5,
            zeroline=False,
            tickfont=dict(size=13),
            showline=True,
            linewidth=1.5,
            linecolor=grid_color,
            mirror=True
        ),
        width=650,
        height=650,
        plot_bgcolor=bg_color,
        paper_bgcolor=bg_color,
        font=dict(color=text_color, family='Arial'),
        margin=dict(l=100, r=50, t=50, b=100),
        hovermode='closest'
    )
    
    return fig


def render_matrix_plt(df, calc_mode="average", dark_mode=False):
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    import numpy as np
    from io import BytesIO

   
    bg_data = np.zeros((5, 5))
    for r in range(5):
        for c in range(5):
            
            val = (r + 1) * (c + 1)
            if val >= 20: bg_data[r, c] = 3 
            elif val >= 12: bg_data[r, c] = 2 
            elif val >= 6: bg_data[r, c] = 1 
            else: bg_data[r, c] = 0 

    custom_cmap = mcolors.ListedColormap(['#2ecc71', '#f1c40f', '#e67e22', '#c0392b'])
    
    
    from matplotlib.figure import Figure
    fig = Figure(figsize=(6, 6), facecolor='white')
    ax = fig.add_subplot(111, facecolor='white')
  
    for spine in ax.spines.values():
        spine.set_edgecolor('black')
    ax.tick_params(colors='black', which='both')
    ax.xaxis.label.set_color('black')
    ax.yaxis.label.set_color('black')
    
    ax.imshow(bg_data, cmap=custom_cmap, origin='lower', extent=[0.5, 5.5, 0.5, 5.5], alpha=0.8)

   
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.grid(True, color='white', linestyle='-', linewidth=0.5, alpha=0.3)

    cell_map = {}
    
    def round_05(v):
        return int(float(v) * 2 + 0.5) / 2.0

    for _, row in df.iterrows():
      
        iv = row.get("Max_Impact") if calc_mode == "maximum" else None
        if iv is None:
            iv = row.get("Avg_Impact")
        if iv is None:
            iv = row.get("Impact")
        
        lv = row.get("Avg_Likelihood")
        if lv is None:
            lv = row.get("Likelihood")
            
        if iv is None or lv is None or pd.isna(iv) or pd.isna(lv):
            continue

        try:
            x = round_05(iv)
            y = round_05(lv)
            x = max(1, min(5, x))
            y = max(1, min(5, y))
            
            nr = int(row.get("Nr", 0))
            if nr > 0:
                cell_map.setdefault((x, y), []).append(nr)
        except (ValueError, TypeError):
            continue

    for (x, y), nrs in cell_map.items():
        if len(nrs) == 1:
            label = str(nrs[0])
            fs = 11
        elif len(nrs) <= 2:
            label = "&".join(str(n) for n in nrs)
            fs = 8 if len(label) > 2 else 10
        else:
            label = f"{len(nrs)}x"
            fs = 10
        
     
        ax.scatter(x, y, s=450, color='white', edgecolor='#2c3e50', linewidth=1.5, zorder=10)
        ax.text(x, y, label, ha='center', va='center', fontsize=fs, fontweight='bold', color='#2c3e50', zorder=11)

    impact_label = "Auswirkung (Maximum)" if calc_mode == "maximum" else "Auswirkung (Durchschnitt)"
    ax.set_xlabel(impact_label, fontsize=12, fontweight='bold')
    ax.set_ylabel("Eintrittswahrscheinlichkeit", fontsize=12, fontweight='bold')
    
    
    fig.tight_layout()
    
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150)
    return buf.getvalue()


# TAB 2: EVALUATION
with tab_evaluation:
    if df.empty:
        st.info("⚠️ Bitte füllen Sie zuerst den Fragebogen aus, um eine Risikoanalyse zu sehen.")
        unanswered = []
        if mode == "small":
            relevant_fields = SMALL_FIELDS
            for fid in relevant_fields:
                if profile_raw.get(fid) is None:
                    label = PROFILE_FIELDS[fid]["label"]
                    unanswered.append(label)
        else:
            for fid, meta in PROFILE_FIELDS.items():
                if profile_raw.get(fid) is None:
                    unanswered.append(meta["label"])

        if unanswered:
            with st.expander("❗ Nicht beantwortete Fragen anzeigen"):
                st.markdown("<br>".join(f"• {x}" for x in unanswered), unsafe_allow_html=True)
    else:

        st.header("📊 Risiko-Perspektiven")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("**Berechnungsmodus:**")
            current_mode = st.session_state.risk_calculation_mode
            is_critical = profile_raw.get("is_critical_infrastructure")
            is_critical_yes = (is_critical == 0.0 or is_critical is True)
            
            calc_mode_ui = st.selectbox(
                "Modus wählen",
                options=["average", "maximum"],
                index=0 if current_mode == "average" else 1,
                format_func=lambda x: "📊 Durchschnitt" if x == "average" else "📈 Maximum",
                key="calc_mode_selectbox",
                disabled=is_critical_yes,
                label_visibility="collapsed"
            )
            
            if is_critical_yes:
                st.info("⚠️ **Da Sie eine kritische Infrastruktur sind, wird der Maximum-Ansatz empfohlen.**")
            
            if not is_critical_yes and calc_mode_ui != current_mode:
                st.session_state.risk_calculation_mode = calc_mode_ui
                st.rerun()
            
            st.markdown("---")
            st.markdown("**Gewichtung für Risikoberechnung:**")
            
            col_weight1, col_weight2, col_weight3 = st.columns([1, 1, 1])
            with col_weight1:
                weight_likelihood = st.number_input(
                    "Wahrscheinlichkeit (%)", min_value=0, max_value=100, value=int(st.session_state.risk_weight_likelihood), step=1, key="weight_likelihood_input"
                )
            with col_weight2:
                weight_impact = st.number_input(
                    "Auswirkung (%)", min_value=0, max_value=100, value=int(st.session_state.risk_weight_impact), step=1, key="weight_impact_input"
                )
            with col_weight3:
                total = weight_likelihood + weight_impact
                if total != 100:
                    st.warning(f"Summe: {total}% (soll 100 sein)")
                else:
                    st.success(f"Summe: {total}%")
            
            if weight_likelihood != st.session_state.risk_weight_likelihood or weight_impact != st.session_state.risk_weight_impact:
                st.session_state.risk_weight_likelihood = weight_likelihood
                st.session_state.risk_weight_impact = weight_impact
                if total == 100:
                    st.rerun()

        st.markdown("---")

        if st.button("⚙️ Feintuning: Assets & Threats anpassen", use_container_width=True, key="btn_toggle_finetune"):
            st.session_state.show_fine_tuning = not st.session_state.get("show_fine_tuning", False)

        if st.session_state.get("show_fine_tuning", False):
            with st.expander("⚙️ Feintuning: Assets & Threats Parameter", expanded=True):
                st.markdown("**Individuelle Anpassung**")
                
                catalog = cached_catalog()
                temp_assets = {}
                temp_threats = {}

                st.markdown("### 📦 Assets (Impact)")
                acols = st.columns(2)
                cidx = 0
                for asset in catalog["assets"]:
                    aid = asset["id"]
                    curr = st.session_state.fine_tuning_assets.get(aid, asset["impact"])
                    with acols[cidx]:
                        val = st.number_input(f"{asset['name']}", 1.0, 5.0, float(curr), 0.1, key=f"ft_a_{aid}_v{st.session_state.fine_tuning_version}")
                        temp_assets[aid] = val
                    cidx = (cidx+1)%2
                
                st.markdown("### ⚠️ Threats (Likelihood)")
                tcols = st.columns(2)
                cidx = 0
                for threat in catalog["threats"]:
                    tid = threat["id"]
                    curr = st.session_state.fine_tuning_threats.get(tid, threat["likelihood"])
                    with tcols[cidx]:
                        val = st.number_input(f"{threat['name']}", 1.0, 5.0, float(curr), 0.1, key=f"ft_t_{tid}_v{st.session_state.fine_tuning_version}")
                        temp_threats[tid] = val
                    cidx = (cidx+1)%2

                c1, c2, c3 = st.columns(3)
                if c1.button("💾 Speichern", type="primary"):
                    st.session_state.fine_tuning_assets = temp_assets
                    st.session_state.fine_tuning_threats = temp_threats
                    st.session_state.show_fine_tuning = False
                    st.rerun()
                if c2.button("🔄 Zurücksetzen"):
                    st.session_state.fine_tuning_assets = {}
                    st.session_state.fine_tuning_threats = {}
                    st.session_state.fine_tuning_version += 1
                    st.rerun()
                if c3.button("❌ Abbruch"):
                    st.session_state.show_fine_tuning = False
                    st.rerun()

      
        subtab_vuln, subtab_threats, subtab_assets = st.tabs([
            "🛑 Vulnerabilities",
            "⚠️ Threats",
            "💼 Assets"
        ])
        
        with subtab_vuln:
            st.markdown("### 🛑 Schwachstellen-Analyse")
            st.markdown("#### 🎯 Risiko-Matrix (Schwachstellen)")
            
            c_mat, c_kpi = st.columns([2, 1])
            with c_mat:
                fig = render_matrix(vuln_df, calc_mode)
                st.plotly_chart(fig, use_container_width=False, config={'displayModeBar': False})
            
            with c_kpi:
                st.markdown("<br><br>", unsafe_allow_html=True)
                high_count = 0
                med_count = 0
                low_count = 0
                if not vuln_df.empty:
                    for _, r in vuln_df.iterrows():
                        iv = r.get("Avg_Impact", 0)
                        lv = r.get("Avg_Likelihood", 0)
                        sc = iv * lv
                        if sc >= 20: high_count += 1
                        elif sc >= 12: med_count += 1
                        else: low_count += 1
                
                st.markdown(f"""
                <div style="background: var(--panel2); padding: 1.5rem; border-radius: 12px; border: 1px solid var(--border);">
                    <h4 style="margin-top:0; margin-bottom:1rem; font-size:1.1rem; opacity:0.8;">Risiko-Verteilung</h4>
                    <div style="display: flex; flex-direction: column; gap: 1rem;">
                        <div style="background: rgba(192, 57, 43, 0.1); border-left: 4px solid #c0392b; padding: 0.8rem; border-radius: 4px;">
                            <span style="color: #e74c3c; font-weight: 800; font-size: 1.2rem;">{high_count}</span>
                            <span style="margin-left: 8px; opacity:0.9;">High Risk (Rot)</span>
                        </div>
                        <div style="background: rgba(230, 126, 34, 0.1); border-left: 4px solid #e67e22; padding: 0.8rem; border-radius: 4px;">
                            <span style="color: #f39c12; font-weight: 800; font-size: 1.2rem;">{med_count}</span>
                            <span style="margin-left: 8px; opacity:0.9;">Medium Risk (Gelb)</span>
                        </div>
                        <div style="background: rgba(39, 174, 96, 0.1); border-left: 4px solid #27ae60; padding: 0.8rem; border-radius: 4px;">
                            <span style="color: #2ecc71; font-weight: 800; font-size: 1.2rem;">{low_count}</span>
                            <span style="margin-left: 8px; opacity:0.9;">Low Risk (Grün)</span>
                        </div>
                    </div>
                    <div style="margin-top: 1.5rem; font-size: 0.85rem; opacity: 0.6; line-height: 1.4;">
                        Die Klassifizierung erfolgt basierend auf dem Matrix-Score (Auswirkung × Wahrscheinlichkeit).
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            df_display = vuln_df_clean.copy()
            rename_map = {
                "Threats_cell": "Bedrohungen",
                "Assets_cell": "Assets",
                "Avg_Likelihood": "Wahrscheinlichkeit",
                "Avg_Impact": "Auswirkung",
                "Risk": "Risiko"
            }
            if calc_mode == "maximum":
                rename_map["Max_Impact"] = "Max_Auswirkung"
                if "Max_Impact" in df_display.columns:
                    df_display = df_display.rename(columns={"Max_Impact": "Auswirkung"})
            else:
                 if "Avg_Impact" in df_display.columns:
                    df_display = df_display.rename(columns={"Avg_Impact": "Auswirkung"})

            df_display = df_display.rename(columns=rename_map)
            wanted_cols = ["Nr", "Schwachstelle", "Bedrohungen", "Assets", "Wahrscheinlichkeit", "Auswirkung", "Risiko"]
            final_cols = [c for c in wanted_cols if c in df_display.columns]
            st.markdown(df_display[final_cols].to_html(escape=False, index=False), unsafe_allow_html=True)

        with subtab_threats:
            st.markdown("### ⚠️ Bedrohungs-Analyse")
            t_rows_en = []
            for tid in df["ThreatID"].unique():
                sub = df[df["ThreatID"] == tid]
                name = sub["Threat"].iloc[0]
                avel = sub["Likelihood"].mean()
                imp = sub["Impact"].max() if calc_mode == "maximum" else sub["Impact"].mean()
                rsk = (weight_likelihood_norm * avel) + (weight_impact_norm * imp)
                
                t_rows_en.append({
                    "Threat": name,
                    "Vulns_cell": make_cell_expander("anzeigen", list(sub["Schwachstelle"].unique())),
                    "Assets_cell": make_cell_expander("anzeigen", list(sub["Asset"].unique())),
                    "Avg_Likelihood": round(avel, 2),
                    "Avg_Impact": imp,
                    "Risk": round(rsk, 2)
                })
            
            t_df_en = pd.DataFrame(t_rows_en).sort_values("Risk", ascending=False)
            t_df_en.insert(0, "Nr", range(1, len(t_df_en)+1))
            
            st.markdown("#### 🎯 Risiko-Matrix (Bedrohungen)")
            
            c_mat_t, c_kpi_t = st.columns([2, 1])
            with c_mat_t:
                fig = render_matrix(t_df_en, calc_mode)
                st.plotly_chart(fig, use_container_width=False, config={'displayModeBar': False})
            
            with c_kpi_t:
                st.markdown("<br><br>", unsafe_allow_html=True)
                high_count_t = 0
                med_count_t = 0
                low_count_t = 0
                if not t_df_en.empty:
                    for _, r in t_df_en.iterrows():
                        iv = r.get("Avg_Impact", 0)
                        lv = r.get("Avg_Likelihood", 0)
                        sc = iv * lv
                        if sc >= 20: high_count_t += 1
                        elif sc >= 12: med_count_t += 1
                        else: low_count_t += 1
                
                st.markdown(f"""
                <div style="background: var(--panel2); padding: 1.5rem; border-radius: 12px; border: 1px solid var(--border);">
                    <h4 style="margin-top:0; margin-bottom:1rem; font-size:1.1rem; opacity:0.8;">Risiko-Verteilung</h4>
                    <div style="display: flex; flex-direction: column; gap: 1rem;">
                        <div style="background: rgba(192, 57, 43, 0.1); border-left: 4px solid #c0392b; padding: 0.8rem; border-radius: 4px;">
                            <span style="color: #e74c3c; font-weight: 800; font-size: 1.2rem;">{high_count_t}</span>
                            <span style="margin-left: 8px; opacity:0.9;">High Risk (Rot)</span>
                        </div>
                        <div style="background: rgba(230, 126, 34, 0.1); border-left: 4px solid #e67e22; padding: 0.8rem; border-radius: 4px;">
                            <span style="color: #f39c12; font-weight: 800; font-size: 1.2rem;">{med_count_t}</span>
                            <span style="margin-left: 8px; opacity:0.9;">Medium Risk (Gelb)</span>
                        </div>
                        <div style="background: rgba(39, 174, 96, 0.1); border-left: 4px solid #27ae60; padding: 0.8rem; border-radius: 4px;">
                            <span style="color: #2ecc71; font-weight: 800; font-size: 1.2rem;">{low_count_t}</span>
                            <span style="margin-left: 8px; opacity:0.9;">Low Risk (Grün)</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            
            t_df_display = t_df_en.copy()
            t_df_display = t_df_display.rename(columns={
                "Threat": "Bedrohung",
                "Vulns_cell": "Schwachstellen",
                "Assets_cell": "Assets", 
                "Avg_Likelihood": "Wahrscheinlichkeit",
                "Avg_Impact": "Auswirkung",
                "Risk": "Risiko"
            })
            t_df_display["Auswirkung"] = t_df_display["Auswirkung"].round(2)
            t_df_display = t_df_display.applymap(clean)
            st.markdown(t_df_display[["Nr", "Bedrohung", "Schwachstellen", "Assets", "Wahrscheinlichkeit", "Auswirkung", "Risiko"]].to_html(escape=False, index=False), unsafe_allow_html=True)

        with subtab_assets:
            st.markdown("### 💼 Asset-Analyse")
            a_rows_en = []
            for aid in df["AssetID"].unique():
                sub = df[df["AssetID"] == aid]
                name = sub["Asset"].iloc[0]
                avel = sub["Likelihood"].mean()
                imp = sub["Impact"].max() if calc_mode == "maximum" else sub["Impact"].mean()
                rsk = (weight_likelihood_norm * avel) + (weight_impact_norm * imp)
                
                a_rows_en.append({
                    "Asset": name,
                    "Vulns_cell": make_cell_expander("anzeigen", list(sub["Schwachstelle"].unique())),
                    "Threats_cell": make_cell_expander("anzeigen", list(sub["Threat"].unique())),
                    "Avg_Likelihood": round(avel, 2),
                    "Avg_Impact": imp,
                    "Risk": round(rsk, 2)
                })

            a_df_en = pd.DataFrame(a_rows_en).sort_values("Risk", ascending=False)
            a_df_en.insert(0, "Nr", range(1, len(a_df_en)+1))
            
            st.markdown("#### 🎯 Risiko-Matrix (Assets)")
            
            c_mat_a, c_kpi_a = st.columns([2, 1])
            with c_mat_a:
                fig = render_matrix(a_df_en, calc_mode)
                st.plotly_chart(fig, use_container_width=False, config={'displayModeBar': False})
            
            with c_kpi_a:
                st.markdown("<br><br>", unsafe_allow_html=True)
                high_count_a = 0
                med_count_a = 0
                low_count_a = 0
                if not a_df_en.empty:
                    for _, r in a_df_en.iterrows():
                        iv = r.get("Avg_Impact", 0)
                        lv = r.get("Avg_Likelihood", 0)
                        sc = iv * lv
                        if sc >= 20: high_count_a += 1
                        elif sc >= 12: med_count_a += 1
                        else: low_count_a += 1
                
                st.markdown(f"""
                <div style="background: var(--panel2); padding: 1.5rem; border-radius: 12px; border: 1px solid var(--border);">
                    <h4 style="margin-top:0; margin-bottom:1rem; font-size:1.1rem; opacity:0.8;">Risiko-Verteilung</h4>
                    <div style="display: flex; flex-direction: column; gap: 1rem;">
                        <div style="background: rgba(192, 57, 43, 0.1); border-left: 4px solid #c0392b; padding: 0.8rem; border-radius: 4px;">
                            <span style="color: #e74c3c; font-weight: 800; font-size: 1.2rem;">{high_count_a}</span>
                            <span style="margin-left: 8px; opacity:0.9;">High Risk (Rot)</span>
                        </div>
                        <div style="background: rgba(230, 126, 34, 0.1); border-left: 4px solid #e67e22; padding: 0.8rem; border-radius: 4px;">
                            <span style="color: #f39c12; font-weight: 800; font-size: 1.2rem;">{med_count_a}</span>
                            <span style="margin-left: 8px; opacity:0.9;">Medium Risk (Gelb)</span>
                        </div>
                        <div style="background: rgba(39, 174, 96, 0.1); border-left: 4px solid #27ae60; padding: 0.8rem; border-radius: 4px;">
                            <span style="color: #2ecc71; font-weight: 800; font-size: 1.2rem;">{low_count_a}</span>
                            <span style="margin-left: 8px; opacity:0.9;">Low Risk (Grün)</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            
            a_df_display = a_df_en.copy()
            a_df_display = a_df_display.rename(columns={
                "Asset": "Asset",
                "Vulns_cell": "Schwachstellen",
                "Threats_cell": "Bedrohungen",
                "Avg_Likelihood": "Wahrscheinlichkeit",
                "Avg_Impact": "Auswirkung",
                "Risk": "Risiko"
            })
            a_df_display["Auswirkung"] = a_df_display["Auswirkung"].round(2)
            a_df_display = a_df_display.applymap(clean)
            st.markdown(a_df_display[["Nr", "Asset", "Schwachstellen", "Bedrohungen", "Wahrscheinlichkeit", "Auswirkung", "Risiko"]].to_html(escape=False, index=False), unsafe_allow_html=True)


# TAB 3: RECOMMENDATIONS 
with tab_recommendations:
    if vuln_df.empty:
        st.info("⚠️ Bitte füllen Sie zuerst den Fragebogen aus.")
    else:
        st.header("🛠 Handlungsempfehlungen")
        st.caption("Basierend auf den identifizierten Schwachstellen und Policies.")

        for _, row in vuln_df.iterrows():
            nr = int(row["Nr"])
            vuln_name = row["Schwachstelle"]
            vid = row["VulnID"]
            first_threat = row["ThreatNames"][0]
            first_asset = row["AssetNames"][0]

            with st.expander(f"#{nr} – {vuln_name}"):
                if st.checkbox("✅ Als umgesetzt markieren", key=f"comp_{vid}_{st.session_state.widget_version}"):
                    st.session_state.completed_actions.add(vid)
                    st.rerun()

                hits = enrich_with_policies(policy_search, first_threat, vuln_name, first_asset)
                
                cache_key = (vuln_name, first_threat, first_asset)
                if cache_key not in st.session_state.rec_cache:
                    ctx = {
                        "asset": first_asset, "threat": first_threat, "vuln": vuln_name,
                        "risk": float(row["Risk"]), "likelihood": float(row["Avg_Likelihood"]),
                        "impact": float(row["Avg_Impact"]) if "Avg_Impact" in row else 0.0
                    }
                    with st.spinner("Generiere Maßnahmen..."):
                        md, main_source = llm_actions_from_policy_hits(hits, ctx, max_chars=3000, return_hits=True)
                    st.session_state.rec_cache[cache_key] = (md, main_source)
                
                cached_md, cached_source = st.session_state.rec_cache[cache_key]
                st.markdown(cached_md)
                
                
                if cached_source:
                    st.markdown("---")
                    st.markdown(f"**📄 Quelle:** {cached_source['file']} (Seite {cached_source['page']})")
                    with st.expander("📖 Textauszug anzeigen"):
                        st.write(cached_source['snippet'])

        
      
        if st.session_state.completed_actions:
            st.markdown("---")
            with st.expander("✅ Umgesetzte Maßnahmen (manuell abgehakt)", expanded=False):
                st.info("Hier finden Sie Maßnahmen, die Sie manuell als erledigt markiert haben. Durch Abwählen werden sie wieder in die Risikoanalyse aufgenommen.")
                to_remove = []
                for cvid in list(st.session_state.completed_actions):
                    v_meta = next((v for v in catalog["vulnerabilities"] if v["id"] == cvid), None)
                    v_name = v_meta["name"] if v_meta else cvid
                    if not st.checkbox(f"Maßnahme erledigt: {v_name}", value=True, key=f"uncomp_{cvid}_{st.session_state.widget_version}"):
                        to_remove.append(cvid)
                
                if to_remove:
                    for rvid in to_remove:
                        st.session_state.completed_actions.discard(rvid)
                    st.rerun()

        st.markdown("---")
        st.subheader("📄 Bericht exportieren")
        if not HAS_REPORTLAB:
            st.warning("ReportLab nicht installiert.")
        else:
            calc_mode_val = st.session_state.risk_calculation_mode
            pdf_bytes = build_pdf_report(
                profile_raw=profile_raw,
                df=df,
                vuln_df=vuln_df,
                policy_search=policy_search,
                render_matrix=lambda d: render_matrix_plt(d, calc_mode=calc_mode_val),
                mode=mode,
                completed_actions=st.session_state.completed_actions,
            )
            st.download_button(
                "📄 PDF-Bericht laden",
                data=pdf_bytes,
                file_name="risiko_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
