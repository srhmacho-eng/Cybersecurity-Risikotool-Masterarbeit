from io import BytesIO
from datetime import datetime
import traceback

import pandas as pd
import re

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
except Exception:
    HAS_REPORTLAB = False

from intake_flow import PROFILE_FIELDS, SMALL_FIELDS
from recommender import enrich_with_policies, llm_actions_from_policy_hits
# PDF-Export Logik

# Hauptfunktion PDF
def build_pdf_report(profile_raw, df, vuln_df, policy_search, render_matrix, mode="small", completed_actions=None):
    if not HAS_REPORTLAB:
        return None
    
    if completed_actions is None:
        completed_actions = set()

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        title="Risikoanalyse-Bericht",
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )

   
    styles = getSampleStyleSheet()

    title_style = styles["Heading1"]
    title_style.fontSize = 18
    title_style.leading = 22
    title_style.textColor = colors.HexColor("#1f6feb")
    title_style.alignment = 1 

    h2 = styles["Heading2"]
    h2.fontSize = 14
    h2.leading = 17
    h2.textColor = colors.HexColor("#388bfd")
    h2.spaceBefore = 12
    h2.spaceAfter = 6
    h2.borderPadding = 5
    
    
    h3 = styles["Heading3"]
    h3.fontSize = 11
    h3.leading = 13
    h3.textColor = colors.HexColor("#0969da")
    h3.spaceBefore = 10
    h3.spaceAfter = 5

    normal = styles["BodyText"]
    normal.fontSize = 9
    normal.leading = 11
    
    source_style = styles["Italic"]
    source_style.fontSize = 8
    source_style.leading = 10
    source_style.textColor = colors.grey
    source_style.leftIndent = 10

    story = []

  
    story.append(Paragraph("Risikoanalyse-Bericht", title_style))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(f"Erstellt am {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}", styles["Normal"]))
    story.append(Spacer(1, 0.8 * cm))

   
    story.append(Paragraph("1. Fragebogen-Antworten", h2))
    story.append(Spacer(1, 0.2 * cm))

    profile_data = [["Frage", "Antwort"]]
    
    if mode == "small":
        relevant_fields = SMALL_FIELDS
    else:
        relevant_fields = list(PROFILE_FIELDS.keys())
    
    for fid in relevant_fields:
        meta = PROFILE_FIELDS.get(fid)
        if not meta:
            continue
            
        label = meta.get("label", fid)
        val = profile_raw.get(fid, None)
        
        if meta.get("type") == "yn_required":
            if val is True or val == 0.0:
                val_str = "Ja"
            elif val is False or val == 1.0:
                val_str = "Nein"
            else:
                val_str = "Nein"
        elif meta.get("type") == "yn":
            if val is True or val == 0.0:
                val_str = "Ja"
            elif val == 0.5:
                val_str = "Teilweise"
            elif val is False or val == 1.0:
                val_str = "Nein"
            elif val is None:
                val_str = "Keine Angabe"
            else:
                val_str = str(val)
        elif meta.get("type") == "int":
            val_str = str(val) if val is not None else "Keine Angabe"
        else:
            val_str = str(val) if val is not None else "Keine Angabe"
        
        profile_data.append([Paragraph(label, normal), val_str])

    if len(profile_data) > 1:
        profile_table = Table(
            profile_data,
            colWidths=[11.5 * cm, 4.0 * cm],
            repeatRows=1,
        )
        profile_table.setStyle(TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B1020")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#f7f7f7")],
                    ),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(profile_table)
    else:
        story.append(Paragraph("Keine Profildaten vorhanden.", normal))

    story.append(Spacer(1, 1.0 * cm))

    # 2. Risiko-Analyse
    story.append(Paragraph("2. Risiko-Analyse", h2))
    story.append(Spacer(1, 0.4 * cm))

   
    threat_rows = []
    for tid in df["ThreatID"].unique():
        sub = df[df["ThreatID"] == tid]
        name = sub["Threat"].iloc[0]
        avg_likelihood = sub["Likelihood"].mean()
        avg_impact = sub["Impact"].mean()
        avg_risk = sub["Risikoscore"].mean()
        threat_rows.append(
            {
                "Threat": name,
                "Avg_Likelihood": round(avg_likelihood, 2),
                "Avg_Impact": round(avg_impact, 2),
                "Risk": round(avg_risk, 2),
            }
        )

    threat_df_pdf = pd.DataFrame(threat_rows)
    if not threat_df_pdf.empty:
        threat_df_pdf = threat_df_pdf.sort_values("Risk", ascending=False)
        if "Nr" not in threat_df_pdf.columns:
            threat_df_pdf.insert(0, "Nr", range(1, len(threat_df_pdf) + 1))

    asset_rows = []
    for aid in df["AssetID"].unique():
        sub = df[df["AssetID"] == aid]
        name = sub["Asset"].iloc[0]
        avg_likelihood = sub["Likelihood"].mean()
        avg_impact = sub["Impact"].mean()
        avg_risk = sub["Risikoscore"].mean()
        asset_rows.append(
            {
                "Asset": name,
                "Avg_Likelihood": round(avg_likelihood, 2),
                "Avg_Impact": round(avg_impact, 2),
                "Risk": round(avg_risk, 2),
            }
        )

    asset_df_pdf = pd.DataFrame(asset_rows)
    if not asset_df_pdf.empty:
        asset_df_pdf = asset_df_pdf.sort_values("Risk", ascending=False)
        if "Nr" not in asset_df_pdf.columns:
            asset_df_pdf.insert(0, "Nr", range(1, len(asset_df_pdf) + 1))

   
    # Tabelle generieren
    def add_table_from_df(title, df_src, cols, col_labels=None):
        story.append(Paragraph(title, h3))
        story.append(Spacer(1, 0.15 * cm))
        if df_src is None or df_src.empty:
            story.append(Paragraph("Keine Daten vorhanden.", normal))
            story.append(Spacer(1, 0.4 * cm))
            return

        labels = col_labels or cols
        table_data = [labels]
        for _, r in df_src.iterrows():
            row_vals = []
            for c in cols:
                v = r[c]
                if isinstance(v, float):
                    row_vals.append(f"{v:.2f}")
                else:
                    row_vals.append(str(v))
            table_data.append(row_vals)

        if len(cols) == 6:
            col_widths = [1.0 * cm, 4.0 * cm, 7.5 * cm, 1.5 * cm, 1.5 * cm, 1.5 * cm]
        elif len(cols) == 5:
            col_widths = [1.0 * cm, 8.0 * cm, 1.5 * cm, 1.5 * cm, 1.5 * cm]
        else:
            col_widths = None

        tbl = Table(table_data, repeatRows=1, colWidths=col_widths)
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B1020")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#f7f7f7")],
                    ),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story.append(tbl)
        story.append(Spacer(1, 0.5 * cm))

    add_table_from_df(
        "Top Schwachstellen",
        vuln_df.sort_values("Risk", ascending=False),
        ["Nr", "VulnID", "Schwachstelle", "Avg_Likelihood", "Avg_Impact", "Risk"],
        ["Nr", "ID", "Schwachstelle", "Likel.", "Imp.", "Risiko"],
    )

    add_table_from_df(
        "Relevante Bedrohungen",
        threat_df_pdf,
        ["Nr", "Threat", "Avg_Likelihood", "Avg_Impact", "Risk"],
        ["Nr", "Bedrohung", "Likel.", "Imp.", "Risiko"],
    )

    add_table_from_df(
        "Betroffene Assets",
        asset_df_pdf,
        ["Nr", "Asset", "Avg_Likelihood", "Avg_Impact", "Risk"],
        ["Nr", "Asset", "Likel.", "Imp.", "Risiko"],
    )

    # Risiko-Matrizen

    def add_matrix(title, df_src):
        story.append(Paragraph(title, h3))
        story.append(Spacer(1, 0.2 * cm))
        try:
            png_bytes = render_matrix(df_src)
            img = RLImage(BytesIO(png_bytes), width=15 * cm, height=15 * cm)
            img.hAlign = 'CENTER'
            story.append(img)
            
            story.append(Spacer(1, 0.4 * cm))
            story.append(Paragraph("Legende zur Matrix (Position = [Auswirkung | Wahrscheinlichkeit]):", styles["Italic"]))
            
            name_col = "Schwachstelle" if "Schwachstelle" in df_src.columns else (
                "Threat" if "Threat" in df_src.columns else "Asset"
            )
            
            imp_col = "Avg_Impact" if "Avg_Impact" in df_src.columns else (
                "Impact" if "Impact" in df_src.columns else "Risk"
            )
            lik_col = "Avg_Likelihood" if "Avg_Likelihood" in df_src.columns else (
                "Likelihood" if "Likelihood" in df_src.columns else "Risk"
            )

            legend_data = [["Nr.", "Pos.", name_col]]
            for _, r in df_src.sort_values("Nr").iterrows():
                try:
                    def round_05(v):
                        return int(float(v) * 2 + 0.5) / 2.0
                    
                    p_imp = round_05(r.get(imp_col, 0))
                    p_lik = round_05(r.get(lik_col, 0))
                    pos_str = f"[{p_imp:.1f}|{p_lik:.1f}]".replace(".0", "")
                except:
                    pos_str = "n/a"
                
                legend_data.append([str(int(r["Nr"])), pos_str, Paragraph(str(r[name_col]), normal)])
            
            ltbl = Table(legend_data, colWidths=[1.2 * cm, 2.0 * cm, 12.3 * cm], repeatRows=1)
            ltbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B1020")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (1, 0), (1, -1), "CENTER"),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f7")]),
                    ]
                )
            )
            story.append(ltbl)

        except Exception as e:
            traceback.print_exc()
            story.append(Paragraph(f"Matrix konnte nicht erzeugt werden: {e}", normal))
        story.append(Spacer(1, 0.8 * cm))

    add_matrix("Risikomatrix – Vulnerabilities", vuln_df)
    
    if not threat_df_pdf.empty:
        add_matrix("Risikomatrix – Threats", threat_df_pdf)
    
    if not asset_df_pdf.empty:
        add_matrix("Risikomatrix – Assets", asset_df_pdf)

    # 3. Handlungsempfehlungen
    story.append(Paragraph("3. Handlungsempfehlungen", h2))
    story.append(Spacer(1, 0.4 * cm))

    def md_to_rl_xml(text):
        """Simplistic markdown to reportlab xml tags."""
        import re
      
        text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
      
        text = re.sub(r"^### (.*)", r"<font size='10'><b>\1</b></font>", text, flags=re.MULTILINE)
        return text


    # KI-Empfehlungen
    open_vulns = vuln_df[~vuln_df["VulnID"].isin(completed_actions)].copy()
    completed_vulns = vuln_df[vuln_df["VulnID"].isin(completed_actions)].copy()

    if open_vulns.empty:
        story.append(Paragraph("Alle identifizierten Maßnahmen wurden bereits als umgesetzt markiert.", normal))
    else:
        for _, r in open_vulns.sort_values("Risk", ascending=False).iterrows():
            nr = int(r["Nr"])
            vuln_name = str(r["Schwachstelle"])

            story.append(Paragraph(f"Empfehlung #{nr}: {vuln_name}", h3))
            story.append(Spacer(1, 0.1 * cm))

            threat_names = r.get("ThreatNames", []) or []
            asset_names = r.get("AssetNames", []) or []
            first_threat = threat_names[0] if threat_names else ""
            first_asset = asset_names[0] if asset_names else ""

            try:
                hits = enrich_with_policies(policy_search, first_threat, vuln_name, first_asset)
            except Exception:
                hits = []

            ctx = {
                "asset": first_asset, "threat": first_threat, "vuln": vuln_name,
                "risk": float(r["Risk"]), "likelihood": float(r["Avg_Likelihood"]),
                "impact": float(r.get("Avg_Impact", 0))
            }

            try:
                md = llm_actions_from_policy_hits(hits, ctx, max_chars=1800)
            except Exception:
                md = "Keine Empfehlung verfügbar."

            parts = md.split("---")
            main_text = parts[0].strip()
            source_info = parts[1].strip() if len(parts) > 1 else ""

            for line in main_text.split("\n"):
                if not line.strip():
                    story.append(Spacer(1, 0.15 * cm))
                    continue
                story.append(Paragraph(md_to_rl_xml(line), normal))

            if source_info:
                story.append(Spacer(1, 0.2 * cm))
                clean_source = re.sub(r"```.*?```", "", source_info, flags=re.DOTALL)
                clean_source = re.sub(r"\*\*📄 Quelle:\*\*", "Quelle:", clean_source)
                story.append(Paragraph(md_to_rl_xml(clean_source.strip()), source_style))

            story.append(Spacer(1, 0.6 * cm))

    # Erledigte Maßnahmen
    if not completed_vulns.empty:
        story.append(Paragraph("4. Bereits umgesetzte Maßnahmen", h2))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("Folgende Maßnahmen wurden im Rahmen der Analyse als bereits umgesetzt markiert:", normal))
        story.append(Spacer(1, 0.2 * cm))
        
        comp_data = [["Nr.", "Schwachstelle", "Status"]]
        for _, r in completed_vulns.iterrows():
            comp_data.append([str(int(r["Nr"])), r["Schwachstelle"], "✓ Erledigt"])
            
        ctbl = Table(comp_data, colWidths=[1.5 * cm, 11.0 * cm, 3.0 * cm])
        ctbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0B1020")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
            ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
            ("TEXTCOLOR", (2,1), (2,-1), colors.darkgreen),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(ctbl)

    # PDF generieren
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
