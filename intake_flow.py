# Fragebogen-Definitionen & UI
import streamlit as st

# Alle verfügbaren Felder

PROFILE_FIELDS = {

    "employees": {
        "type": "int", 
        "label": "Wie viele Mitarbeiter*innen hat das Unternehmen?",
        "help": "Die Gesamtzahl der Angestellten hilft dabei, die Komplexität der Infrastruktur einzuschätzen.",
        "category": "Unternehmensprofil"
    },
    "is_critical_infrastructure": {
        "type": "yn_required", 
        "label": "Ist Ihr Unternehmen eine kritische Infrastruktur?",
        "help": "Kritische Infrastrukturen (KRITIS) sind Organisationen mit wichtiger Bedeutung für das staatliche Gemeinwesen (z.B. Energie, Wasser, Gesundheit). Hier gelten oft strengere gesetzliche Vorgaben.",
        "category": "Unternehmensprofil"
    },

    "has_security_role": {
        "type": "yn", 
        "label": "Gibt es jemanden, der sich um IT-Sicherheit kümmert?",
        "help": "Dies kann ein interner IT-Sicherheitsbeauftragter oder ein externer Dienstleister sein, der explizit für die Sicherheit (nicht nur IT-Support) zuständig ist.",
        "category": "Sicherheitsorganisation"
    },
    "has_security_policies": {
        "type": "yn", 
        "label": "Gibt es schriftliche Regeln zur IT-Sicherheit?",
        "help": "Schriftliche Richtlinien (z.B. Passwortrichtlinie, Richtlinie zur E-Mail-Nutzung), an die sich alle Mitarbeiter halten müssen.",
        "category": "Sicherheitsorganisation"
    },
    "policies_reviewed": {
        "type": "yn", 
        "label": "Werden die Regeln regelmäßig überprüft?",
        "help": "IT-Sicherheit ist ein Prozess. Regeln müssen mindestens einmal jährlich auf Aktualität geprüft werden.",
        "category": "Sicherheitsorganisation"
    },
    "has_asset_inventory": {
        "type": "yn", 
        "label": "Gibt es eine Übersicht über Geräte/Software/Daten?",
        "help": "Man kann nur schützen, was man kennt. Eine Bestandsliste umfasst Laptops, Server, Cloud-Dienste und wichtige Software.",
        "category": "Sicherheitsorganisation"
    },
    "has_incident_plan": {
        "type": "yn", 
        "label": "Gibt es einen Plan für Sicherheitsvorfälle?",
        "help": "Ein Dokument, das festlegt: 'Was tun wir, wenn wir gehackt wurden?' (Notfallkontakte, erste Schritte).",
        "category": "Sicherheitsorganisation"
    },
    "access_list_exists": {
        "type": "yn", 
        "label": "Gibt es eine Liste mit allen Zugriffsrechten?",
        "help": "Eine Übersicht, welcher Mitarbeiter auf welche Ordner, Programme oder Datenbanken zugreifen darf.",
        "category": "Sicherheitsorganisation"
    },
    "access_list_reviewed": {
        "type": "yn", 
        "label": "Werden Zugriffsrechte regelmäßig überprüft?",
        "help": "Ein regelmäßiger Abgleich (z.B. alle 6 Monate), ob Mitarbeiter noch die Rechte haben, die sie für ihre aktuelle Rolle brauchen.",
        "category": "Sicherheitsorganisation"
    },
    "audits_done": {
        "type": "yn", 
        "label": "Gibt es interne oder externe Sicherheitsüberprüfungen?",
        "help": "Unabhängige Prüfungen (Audits), um festzustellen, ob die Sicherheitsmaßnahmen effektiv sind und eingehalten werden.",
        "category": "Sicherheitsorganisation"
    },

    "has_mfa": {
        "type": "yn", 
        "label": "Müssen sich Mitarbeiter*innen mit einem Zusatzcode anmelden (MFA)?",
        "help": "Multi-Faktor-Authentifizierung (MFA) bedeutet, dass man neben dem Passwort einen zweiten Faktor braucht (z.B. Code per App oder SMS).",
        "category": "Identitäts- & Zugriffsschutz"
    },
    "has_password_rules": {
        "type": "yn", 
        "label": "Gibt es Regeln für sichere Passwörter?",
        "help": "Vorgaben wie Mindestlänge (z.B. 12 Zeichen) und Komplexität.",
        "category": "Identitäts- & Zugriffsschutz"
    },
    "has_password_manager": {
        "type": "yn", 
        "label": "Wird ein Passwort-Manager verwendet?",
        "help": "Ein Programm, das Passwörter sicher speichert, damit Mitarbeiter sich keine unsicheren Notizen machen müssen.",
        "category": "Identitäts- & Zugriffsschutz"
    },
    "has_least_privilege": {
        "type": "yn", 
        "label": "Dürfen Mitarbeiter*innen nur auf das zugreifen, was sie brauchen (Least Privilege)?",
        "help": "Das Prinzip besagt, dass jeder Nutzer nur so viele Rechte haben sollte, wie für seine Arbeit notwendig sind (kein Standard-Admin-Zugriff für alle).",
        "category": "Identitäts- & Zugriffsschutz"
    },
    "inactive_accounts_removed": {
        "type": "yn", 
        "label": "Werden alte/inaktive Benutzerkonten entfernt?",
        "help": "Konten von ehemaligen Mitarbeitern oder nicht mehr genutzte Test-Accounts sind ein Sicherheitsrisiko und sollten sofort gelöscht werden.",
        "category": "Identitäts- & Zugriffsschutz"
    },
    "admin_accounts_protected": {
        "type": "yn", 
        "label": "Sind wichtige/admin Konten besonders geschützt?",
        "help": "Administratoren haben weitreichende Rechte. Diese Konten sollten nur für Admin-Aufgaben genutzt werden und besonders stark (z.B. nur mit MFA) gesichert sein.",
        "category": "Identitäts- & Zugriffsschutz"
    },
    "has_sso": {
        "type": "yn", 
        "label": "Gibt es eine zentrale Anmeldung (SSO)?",
        "help": "Single Sign-On (SSO) erlaubt es, sich mit nur einem Satz Zugangsdaten an vielen verschiedenen Diensten anzumelden.",
        "category": "Identitäts- & Zugriffsschutz"
    },
    "login_monitoring": {
        "type": "yn", 
        "label": "Werden Anmeldeaktivitäten überwacht?",
        "help": "Aufzeichnung von Anmeldeversuchen, um auffällige Muster (z.B. 100 falsche Passwörter in einer Minute) zu erkennen.",
        "category": "Identitäts- & Zugriffsschutz"
    },

    "has_patch_mgmt": {
        "type": "yn", 
        "label": "Werden Programme regelmäßig aktualisiert (Updates/Patches)?",
        "help": "Updates schließen oft Sicherheitslücken. Wichtig ist, dass diese zeitnah (automatisch) eingespielt werden.",
        "category": "Infrastruktur & Netzwerksicherheit"
    },
    "has_vuln_scans": {
        "type": "yn", 
        "label": "Werden Systeme auf Schwachstellen geprüft?",
        "help": "Automatisierte Scans, die nach bekannten Sicherheitslücken in Ihrer Software oder Hardware suchen.",
        "category": "Infrastruktur & Netzwerksicherheit"
    },
    "has_edr": {
        "type": "yn", 
        "label": "Gibt es einen aktuellen Virenschutz/EDR?",
        "help": "Endpoint Detection and Response (EDR) ist ein moderner Virenschutz, der auch verdächtiges Verhalten erkennt.",
        "category": "Infrastruktur & Netzwerksicherheit"
    },
    "has_firewall": {
        "type": "yn", 
        "label": "Gibt es eine Firewall?",
        "help": "Eine digitale Mauer, die den Netzwerkverkehr zwischen dem Internet and Ihrem Firmennetz kontrolliert.",
        "category": "Infrastruktur & Netzwerksicherheit"
    },
    "network_segmented": {
        "type": "yn", 
        "label": "Ist das Netzwerk in Bereiche aufgeteilt (z. B. Gäste-WLAN getrennt)?",
        "help": "Trennung von sensiblen Bereichen (z.B. Buchhaltung) von weniger sicheren Bereichen (z.B. Gäste-WLAN), damit ein infiziertes Gerät nicht das ganze Netz erreicht.",
        "category": "Infrastruktur & Netzwerksicherheit"
    },
    "has_mdm": {
        "type": "yn", 
        "label": "Werden Geräte (PCs, Laptops, Smartphones) zentral verwaltet (MDM)?",
        "help": "Mobile Device Management (MDM) erlaubt es, Firmengeräte aus der Ferne zu konfigurieren, zu updaten oder bei Verlust zu sperren.",
        "category": "Infrastruktur & Netzwerksicherheit"
    },
    "logging_enabled": {
        "type": "yn", 
        "label": "Werden wichtige Systemereignisse aufgezeichnet (Logging)?",
        "help": "Protokollierung hilft im Nachhinein festzustellen, wie ein Angreifer ins System gelangt ist.",
        "category": "Infrastruktur & Netzwerksicherheit"
    },
    "logs_reviewed": {
        "type": "yn", 
        "label": "Werden Logs regelmäßig ausgewertet?",
        "help": "Es reicht nicht, Ereignisse aufzuzeichnen; jemand muss (evtl. automatisiert) prüfen, ob Warnungen oder Angriffsspuren vorliegen.",
        "category": "Infrastruktur & Netzwerksicherheit"
    },
    "has_ids_ips": {
        "type": "yn", 
        "label": "Gibt es Systeme zur Angriffserkennung (IDS/IPS)?",
        "help": "Intrusion Detection/Prevention Systeme überwachen den Datenstrom auf typische Angriffsmuster und blockieren diese ggf. automatisch.",
        "category": "Infrastruktur & Netzwerksicherheit"
    },
    "daily_backups": {
        "type": "yn", 
        "label": "Werden täglich von allen relevanten Daten Backups erstellt?",
        "help": "Regelmäßige Sicherungen sind die letzte Rettung bei einem Ransomware-Angriff (Verschlüsselungstrojaner).",
        "category": "Datensicherung & Kontinuität"
    },
    "has_offsite_backup": {
        "type": "yn", 
        "label": "Werden die Backups an einem anderen Ort gespeichert?",
        "help": "Backups sollten physisch oder logisch getrennt vom Hauptnetzwerk liegen (z.B. Cloud oder Tresor), um bei einem Brand oder totalem Netzbefall geschützt zu sein.",
        "category": "Datensicherung & Kontinuität"
    },
    "backup_tested": {
        "type": "yn", 
        "label": "Wird getestet, ob alle Backups funktionieren?",
        "help": "Regelmäßige Wiederherstellungs-Tests stellen sicher, dass die gesicherten Daten im Ernstfall auch wirklich lesbar sind.",
        "category": "Datensicherung & Kontinuität"
    },
    "device_loss_protection": {
        "type": "yn", 
        "label": "Sind Geräte gegen Verlust geschützt?",
        "help": "Maßnahmen wie Festplattenverschlüsselung (BitLocker/FileVault) oder die Möglichkeit zur Fernlöschung bei Diebstahl.",
        "category": "Datensicherung & Kontinuität"
    },

    "uses_cloud": {
        "type": "yn", 
        "label": "Nutzt das Unternehmen Cloud-Dienste (OneDrive, M365, Google)?",
        "help": "Speichern von Daten oder Nutzung von Diensten über das Internet statt auf eigenen Servern im Gebäude.",
        "category": "Cloud-Sicherheit"
    },
    "cloud_config_secure": {
        "type": "yn", 
        "label": "Sind Cloud-Dienste sicher konfiguriert?",
        "help": "Wurden Standardpasswörter geändert? Ist der Zugriff beschränkt oder sind Daten öffentlich im Netz?",
        "category": "Cloud-Sicherheit"
    },
    "cloud_mfa_enabled": {
        "type": "yn", 
        "label": "Ist MFA in der Cloud aktiviert?",
        "help": "Stellt sicher, dass der Zugang zu Cloud-Diensten (wie Microsoft 365) durch einen zweiten Faktor geschützt ist.",
        "category": "Cloud-Sicherheit"
    },
    "cloud_logging": {
        "type": "yn", 
        "label": "Werden Cloud-Aktivitäten aufgezeichnet (Cloud-Logs)?",
        "help": "Überwachung, wer wann auf welche Dateien in der Cloud zugegriffen hat.",
        "category": "Cloud-Sicherheit"
    },
    "cloud_shares_controlled": {
        "type": "yn", 
        "label": "Wird verhindert, dass Cloud-Ordner öffentlich werden?",
        "help": "Technische Sperren, damit Mitarbeiter nicht versehentlich interne Dokumente für 'Jeden mit dem Link' freigeben.",
        "category": "Cloud-Sicherheit"
    },
    "cloud_permissions_reviewed": {
        "type": "yn", 
        "label": "Werden Cloud-Berechtigungen regelmäßig überprüft?",
        "help": "Kontrolle, ob Freigaben für externe Partner oder Ex-Mitarbeiter noch aktiv sind.",
        "category": "Cloud-Sicherheit"
    },
    "cloud_policy_exists": {
        "type": "yn", 
        "label": "Gibt es Regeln zur Nutzung von Cloud-Diensten?",
        "help": "Vorgaben, welche Daten in der Cloud gespeichert werden dürfen und welche Dienste (z.B. nur genehmigte Anbieter) erlaubt sind.",
        "category": "Cloud-Sicherheit"
    },
    "cloud_config_tested": {
        "type": "yn", 
        "label": "Werden Cloud-Einstellungen getestet?",
        "help": "Regelmäßige Prüfung der Sicherheits-Konfiguration des Cloud-Anbieters.",
        "category": "Cloud-Sicherheit"
    },
    "cloud_dlp": {
        "type": "yn", 
        "label": "Gibt es Schutzmaßnahmen gegen versehentliches Teilen (DLP)?",
        "help": "Data Loss Prevention (DLP) verhindert technisch, dass z.B. Kreditkartennummern oder Konstruktionspläne per E-Mail das Haus verlassen.",
        "category": "Cloud-Sicherheit"
    },

    "has_training": {
        "type": "yn", 
        "label": "Werden Mitarbeiter*innen regelmäßig geschult?",
        "help": "Sicherheitsschulungen sensibilisieren das Personal für Gefahren wie verdächtige Anhänge oder Betrugsversuche.",
        "category": "Sensibilisierung & Mobiles Arbeiten"
    },
    "has_phishing_tests": {
        "type": "yn", 
        "label": "Werden Phishing-Tests durchgeführt?",
        "help": "Simulierte, harmlose Phishing-Mails, um die Wachsamkeit der Mitarbeiter trainieren und Wissenslücken aufzudecken.",
        "category": "Sensibilisierung & Mobiles Arbeiten"
    },
    "email_awareness": {
        "type": "yn", 
        "label": "Wissen Mitarbeiter*innen, wie verdächtige E-Mails aussehen?",
        "help": "Erkennung von Phishing-Merkmalen wie falsche Absenderadressen, dringende Handlungsaufforderungen oder kryptische Links.",
        "category": "Sensibilisierung & Mobiles Arbeiten"
    },
    "has_incident_reporting": {
        "type": "yn", 
        "label": "Gibt es klare Meldewege für Vorfälle?",
        "help": "Mitarbeiter müssen wissen, wen sie anrufen oder informieren, wenn sie etwas Verdächtiges (z.B. verschlüsselte Dateien) bemerken.",
        "category": "Sensibilisierung & Mobiles Arbeiten"
    },
    "has_byod_rules": {
        "type": "yn", 
        "label": "Gibt es Regeln für private Geräte (BYOD)?",
        "help": "Bring Your Own Device (BYOD) Bedarf klarer Regeln: Welche Sicherheits-Apps müssen installiert sein? Darf auf Firmenmails zugegriffen werden?",
        "category": "Sensibilisierung & Mobiles Arbeiten"
    },
    "has_mobile_device_policy": {
        "type": "yn", 
        "label": "Gibt es Regeln für Firmenhandys/Laptops?",
        "help": "Verhaltensregeln für die Nutzung von Mobilgeräten außerhalb des Büros (z.B. VPN-Pflicht in öffentlichen WLANs).",
        "category": "Sensibilisierung & Mobiles Arbeiten"
    },

    "has_data_classification": {
        "type": "yn", 
        "label": "Werden Daten nach Sensibilität eingestuft?",
        "help": "Unterscheidung zwischen Daten, die jeder sehen darf (öffentlich), und solchen, die streng geheim sind (z.B. Personalakten).",
        "category": "Datenschutz & Compliance"
    },
    "gdpr_compliant": {
        "type": "yn", 
        "label": "Werden Datenschutzvorgaben (DSGVO) berücksichtigt?",
        "help": "Einhaltung der gesetzlichen Regeln zum Schutz personenbezogener Daten (von Kunden und Mitarbeitern).",
        "category": "Datenschutz & Compliance"
    },
    "data_retention_rules": {
        "type": "yn", 
        "label": "Gibt es Regeln für Aufbewahrung & Löschung?",
        "help": "Festgelegte Fristen, wann Daten gelöscht werden müssen, um das Risiko bei einem Datenleck zu minimieren.",
        "category": "Datenschutz & Compliance"
    },
    "data_encrypted_at_rest": {
        "type": "yn", 
        "label": "Sind sensible Daten verschlüsselt gespeichert?",
        "help": "Verschlüsselung von Datenbanken oder Festplatten, damit die Daten bei Diebstahl für Angreifer unlesbar sind.",
        "category": "Datenschutz & Compliance"
    },
    "data_encrypted_in_transit": {
        "type": "yn", 
        "label": "Werden Daten beim Versenden verschlüsselt (HTTPS/TLS)?",
        "help": "Schutz der Datenübertragung, damit niemand die Informationen auf dem Weg durch das Internet mitlesen kann.",
        "category": "Datenschutz & Compliance"
    },
    "vendors_checked": {
        "type": "yn", 
        "label": "Werden externe Firmen überprüft, bevor sie Zugriff bekommen?",
        "help": "Prüfung der IT-Sicherheit bei Partnern oder Dienstleistern, die Zugang zu Ihren Systemen erhalten.",
        "category": "Datenschutz & Compliance"
    },
    "vendors_have_avv": {
        "type": "yn", 
        "label": "Haben externe Dienstleister Verträge (AVV)?",
        "help": "Auftragsverarbeitungs-Verträge (AVV) sind rechtlich vorgeschrieben, wenn externe Firmen Ihre Daten verarbeiten.",
        "category": "Datenschutz & Compliance"
    }
}

# Auswahlfelder für Kompakt-Check

SMALL_FIELDS = [
    "employees",
    "is_critical_infrastructure",
    "has_security_role",
    "has_security_policies",
    "has_incident_plan",
    "has_least_privilege",

    "has_mfa",
    "has_patch_mgmt",
    "daily_backups",
    "has_offsite_backup",
    "has_edr",

    "has_firewall",
    "logging_enabled",
    "has_password_rules",

    "has_training",
    "email_awareness",

    "uses_cloud",
    "cloud_config_secure",
    "has_data_classification",
    "cloud_dlp"
]

LARGE_FIELDS = list(PROFILE_FIELDS.keys())


# Radio-Pflichtfeld (Ja/Nein)
def _render_yn_required(label, current_value, disabled, help_text=None, key=None):
    options = ["🟢 Ja", "🔴 Nein"]
    
    if current_value is True or current_value == 0.0:
        idx = 0
    elif current_value is False or current_value == 1.0:
        idx = 1
    else:
        idx = 1
    
    radio_key = key if key else f"radio_req_{label.replace(' ', '_').replace('?', '').replace('!', '').replace('.', '')}"
    choice = st.radio(label, options, index=idx, horizontal=True, disabled=disabled, key=radio_key, help=help_text)
    
    if "🟢 Ja" in choice or choice == "🟢 Ja":
        return 0.0
    return 1.0


# Standard Ja/Nein Auswahl
def _render_yn(label, current_value, disabled, help_text=None, key=None):
    options = ["🟢 Ja", "🟡 Teilweise", "🔴 Nein", "⚪ Keine Angabe"]

    if current_value is True or current_value == 0.0:
        idx = 0
    elif current_value == 0.5:
        idx = 1
    elif current_value is False or current_value == 1.0:
        idx = 2
    else:
        idx = 3

    radio_key = key if key else f"radio_{label.replace(' ', '_').replace('?', '').replace('!', '').replace('.', '')}"
    
    st.markdown("""
    <style>
    div[role="radiogroup"] label {
        cursor: pointer !important;
        padding: 8px 12px !important;
        border-radius: 8px !important;
        transition: all 0.2s !important;
    }
    div[role="radiogroup"] label:hover {
        background-color: rgba(0,0,0,0.05) !important;
    }
    div[role="radiogroup"] label span {
        font-size: 1.1em !important;
        font-weight: 500 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    choice = st.radio(label, options, index=idx, horizontal=True, disabled=disabled, key=radio_key, help=help_text)
    
    if "🟢 Ja" in choice or choice == "🟢 Ja":
        return 0.0
    if "🟡 Teilweise" in choice or choice == "🟡 Teilweise":
        return 0.5
    if "🔴 Nein" in choice or choice == "🔴 Nein":
        return 1.0
    return None


# Haupt-Renderer
def render_questionnaire(fields: list, state: dict, edit_mode: bool):
    new_state = {}

    st.markdown("""
    <style>
    .category-header {
        font-family: 'Outfit', sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: #4ea1ff;
        margin-top: 2.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(78, 161, 255, 0.2);
    }
    
    div.stVerticalBlock > div.stHorizontalBlock {
        align-items: flex-start !important;
        margin-bottom: 10px !important;
    }
    
    div[data-testid="stTooltipIcon"], 
    .stTooltipIcon {
        color: #ccd0d8 !important;
        opacity: 0.8 !important;
        transform: scale(1.1) !important; 
        transition: opacity 0.2s ease !important;
    }
    
    div[data-testid="stTooltipIcon"] svg,
    .stTooltipIcon svg {
        fill: #ccd0d8 !important;
    }

    div[data-testid="stTooltipIcon"]:hover,
    .stTooltipIcon:hover {
        opacity: 1 !important;
        color: #4ea1ff !important;
    }
    
    div[data-testid="stTooltipIcon"]:hover svg,
    .stTooltipIcon:hover svg {
        fill: #4ea1ff !important;
    }
    
    div[data-testid="stTooltipContent"], 
    [data-testid="stTooltipContent"] {
        background-color: #1a2234 !important;
        color: #e6e9ef !important;
        border: 1px solid #2b3a55 !important;
        padding: 12px !important;
        border-radius: 8px !important;
        box-shadow: 0px 5px 15px rgba(0,0,0,0.4) !important;
        max-width: 350px !important;
    }
    </style>
    """, unsafe_allow_html=True)

  
    categories = {}
    for fid in fields:
        cat = PROFILE_FIELDS[fid].get("category", "Allgemein")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(fid)

    
    category_order = [
        "Unternehmensprofil",
        "Sicherheitsorganisation",
        "Identitäts- & Zugriffsschutz",
        "Infrastruktur & Netzwerksicherheit",
        "Datensicherung & Kontinuität",
        "Cloud-Sicherheit",
        "Sensibilisierung & Mobiles Arbeiten",
        "Datenschutz & Compliance"
    ]
    

    sorted_cats = [c for c in category_order if c in categories]
    for c in categories:
        if c not in sorted_cats:
            sorted_cats.append(c)

    for cat in sorted_cats:
        cat_fields = categories[cat]
        st.markdown(f'<div class="category-header">{cat}</div>', unsafe_allow_html=True)
        
        for i in range(0, len(cat_fields), 3):
            row_fields = cat_fields[i:i+3]
            cols = st.columns(3)
            
            for col_idx, fid in enumerate(row_fields):
                meta = PROFILE_FIELDS[fid]
                label = meta["label"]
                help_text = meta.get("help")

                with cols[col_idx]:
                    if meta["type"] == "int":
                        current_val = state.get(fid)
                        new_state[fid] = st.number_input(
                            label,
                            min_value=1,
                            value=1 if current_val is None else current_val,
                            disabled=not edit_mode,
                            help=help_text,
                            key=f"field_{fid}"
                        )

                    elif meta["type"] == "yn":
                        current_val = state.get(fid)
                        new_state[fid] = _render_yn(label, current_val, not edit_mode, help_text, key=f"field_{fid}")
                    
                    elif meta["type"] == "yn_required":
                        current_val = state.get(fid)
                        new_state[fid] = _render_yn_required(label, current_val, not edit_mode, help_text, key=f"field_{fid}")

            st.markdown("---")

    return new_state


# Kompakt-Version
def render_small_questionnaire(state, edit_mode):
    return render_questionnaire(SMALL_FIELDS, state, edit_mode)


# Vollst. Version
def render_large_questionnaire(state, edit_mode):
    return render_questionnaire(LARGE_FIELDS, state, edit_mode)


# Profil-Dict erstellen
def make_profile(state_dict):
    out = {}
    for fid in PROFILE_FIELDS:
        v = state_dict.get(fid)
        out[fid] = v
    return out
