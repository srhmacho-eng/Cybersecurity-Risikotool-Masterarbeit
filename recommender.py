from typing import List, Dict
import yaml
from policy_search import PolicySearch, PolicyHit
from llm import chat
import re



def load_catalog(path="data/risk_catalog.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# Schlagworte für Suche
SYN_GROUPS = {
    "mfa": ["mfa", "2fa", "multi factor", "multi-faktor", "auth", "identity", "Multi Faktor"],
    "password": ["password", "passwort", "pw", "credential"],
    "backup": ["backup", "sicherung", "datensicherung", "recovery", "offsite"],
    "patch": ["patch", "update", "vulnerability management", "security update"],
    "cloud": ["cloud", "saas", "onedrive", "sharepoint", "microsoft 365", "google"],
    "firewall": ["firewall", "netzwerk", "network security"],
    "logging": ["logging", "logs", "audit", "überwachung"],
    "edr": ["antivirus", "virenschutz", "endpoint detection", "edr", "xdr"],
    "phishing": ["phishing", "social engineering", "email fraud"],
    "encryption": ["verschlüsselung", "encryption", "crypto"],
    "classification": ["klassifizierung", "classification", "sensitive data"],
    "dlp": ["dlp", "data loss prevention", "shared files"],
}

AWARENESS_KEYWORDS = [
    "schulung",
    "training",
    "sensibilisierung",
    "awareness",
    "phishing",
    "social engineering",
]


# Suchbegriffe extrahieren
def extract_terms(text: str) -> List[str]:

    if not text:
        return []

    raw = re.findall(r"[A-Za-zÄÖÜäöüß0-9\-]{4,}", text.lower())
    uniq = set(raw)

    for tok in raw:
        for key, syns in SYN_GROUPS.items():
            if key in tok:
                uniq.update(syns)

    return list(uniq)[:20]


def build_query_for_policy(threat_name: str, vuln_name: str, asset_name: str) -> str:
    parts: List[str] = []
    ln = (vuln_name or "").lower()

    parts.extend(extract_terms(vuln_name))

    if "patch" in ln or "update" in ln:
        parts.extend(["patch", "update", "patchmanagement", "vulnerability management", "security update"])

    if "backup" in ln or "sicherung" in ln:
        parts.extend(["backup", "recovery", "restore", "offsite"])

    if "mfa" in ln or "2fa" in ln or "authent" in ln:
        parts.extend(["mfa", "2fa", "strong authentication"])

    if "firewall" in ln or "netz" in ln:
        parts.extend(["firewall", "network security"])

    if "phish" in ln or "social engineering" in ln or "awareness" in ln or "schulung" in ln:
        parts.extend(["phishing", "social engineering", "awareness"])

    if "encrypt" in ln or "verschlüssel" in ln:
        parts.extend(["encryption", "crypto", "tls"])

    if "dlp" in ln:
        parts.extend(["dlp", "data loss prevention"])

    parts.extend(extract_terms(threat_name)[:2])
    parts.extend(extract_terms(asset_name)[:2])

    uniq: List[str] = []
    for p in parts:
        if p not in uniq:
            uniq.append(p)

    return " ".join(uniq[:12])


# Verknüpfung mit PDF-Inhalten
def enrich_with_policies(
    search: PolicySearch,
    threat_name: str,
    vuln_name: str,
    asset_name: str,
    k: int = 7
) -> List[PolicyHit]:
    query = build_query_for_policy(threat_name, vuln_name, asset_name)
    hits = search.search(query, k=k)

    vuln_lower = (vuln_name or "").lower()

    is_awareness_vuln = any(word in vuln_lower for word in [
        "schulung",
        "training",
        "awareness",
        "phishing",
        "social engineering",
        "mitarbeiter",
    ])

    cleaned: List[PolicyHit] = []
    for h in hits:
        txt = (h.snippet or "") + " " + (h.file or "")
        txt = txt.lower()

        awareness_hit = any(aw in txt for aw in AWARENESS_KEYWORDS)

        if awareness_hit and not is_awareness_vuln:
            continue

        cleaned.append(h)

        if len(cleaned) == 3:
            break

    if not cleaned:
        cleaned = list(hits or [])[:3]

    return cleaned


# KI-Maßnahmen generieren
def llm_actions_from_policy_hits(
    hits: List[PolicyHit],
    risk_context: Dict[str, str],
    max_chars: int = 2000,
    return_hits: bool = False
) -> str:
    if not hits:
        if return_hits:
            return ("ℹ️ Keine relevanten Policy-Dokumente gefunden.", [])
        return "ℹ️ Keine relevanten Policy-Dokumente gefunden."
    
    all_policies = []
    for h in hits:
        file = getattr(h, "file", "Unbekannt")
        page = getattr(h, "page", "?")
        snippet = getattr(h, "snippet", "") or ""
        all_policies.append({
            "file": file,
            "page": page,
            "snippet": snippet
        })
    
    policy_context = "\n\n".join([
        f"**Quelle {i+1}:** {p['file']} (Seite {p['page']})\n{p['snippet']}"
        for i, p in enumerate(all_policies)
    ])
    
    vuln = risk_context.get('vuln', 'Unbekannte Schwachstelle')
    threat = risk_context.get('threat', '')
    asset = risk_context.get('asset', '')
    risk_score = risk_context.get('risk', 0)
    
  
    doc_names = ", ".join([p['file'] for p in all_policies])
    
    prompt = f"""Du bist ein Experte für Cybersicherheits-Risikomanagement in KMU.

**AUFGABE:**
Analysiere die folgenden Policy-Auszüge und erstelle **GENAU EINE ganzheitliche Handlungsempfehlung** zur Behebung der Schwachstelle "{vuln}".

**WICHTIGE REGELN:**
1. **Quellen-Treue**: Deine Empfehlung muss STRENG auf den Inhalten der unten aufgeführten `POLICY-QUELLEN` basieren. Nutze konkrete Vorgaben aus diesen Texten.
2. **KEINE Quellenangaben im Text**: Schreibe KEINE Quellenverweise wie "vgl. Dokument, S. X" in deine Empfehlung. Die Quelle wird automatisch am Ende angezeigt.
3. **Keine Erfindungen**: Erfinde keine technischen Details, Systeme oder Prozesse, die nicht in den Quellen erwähnt werden. Wenn die Quellen vage sind ("Es muss ein Backup geben"), bleibe auch in der Empfehlung auf diesem Abstraktionsniveau ("Definition und Implementierung eines Backup-Konzepts gemäß Richtlinie").
4. **Fokus**: Bleibe STRENG beim Thema der Schwachstelle ({vuln}).
5. **Umsetzungsplan**: Erstelle 3-4 logische Schritte, die sich direkt aus den Richtlinien ableiten lassen.
6. **Fallback**: Falls die bereitgestellten Quellen absolut keine relevanten Informationen für diese Schwachstelle enthalten, schreibe dies explizit: "Hinweis: In den vorliegenden Richtlinien wurden keine spezifischen Vorgaben zu diesem Thema gefunden. Die folgende Empfehlung basiert auf allgemeinen Best Practices."
7. **WICHTIG - Hauptquelle identifizieren**: Am Ende deiner Antwort, nach einem "---" Separator, schreibe in einer neuen Zeile "HAUPTQUELLE:" gefolgt von der Nummer der Quelle (1, 2, oder 3), die die KERNAUSSAGE oder das HAUPTPRINZIP deiner Empfehlung enthält (nicht nur unterstützende Details). Wähle die Quelle, die am direktesten die Schwachstelle "{vuln}" adressiert.

**FORMAT:**
### [Titel der Maßnahme]

**Warum ist das wichtig?**
[2-3 Sätze zur Risikoreduktion, basierend auf der Richtlinien-Logik. KEINE Quellenverweise!]

**Umsetzungsplan:**
1. [Schritt aus der Richtlinie - OHNE Quellenverweis]
2. [Weiterer Schritt aus der Richtlinie - OHNE Quellenverweis]
3. [Kontrollschritt/Abschluss - OHNE Quellenverweis]

---
HAUPTQUELLE: [1, 2, oder 3]

---

**KONTEXT:**
- Schwachstelle: {vuln}
- Relevante Bedrohung: {threat}
- Asset: {asset}
- Risikoscore: {risk_score}/5

**VERFÜGBARE POLICY-QUELLEN:**
{policy_context}

**DEINE ANTWORT:**
"""
    
    msg = chat([{"role": "user", "content": prompt}], temperature=0.3)
    result_text = msg.content.strip()
    

    main_source_idx = 0 
    if "HAUPTQUELLE:" in result_text:
        parts = result_text.split("HAUPTQUELLE:")
        result_text = parts[0].strip()
        if len(parts) > 1:
            try:
                source_num = int(parts[1].strip().split()[0])
                main_source_idx = max(0, min(source_num - 1, len(all_policies) - 1))
            except:
                pass
    
   
    result_text = result_text.rstrip("-").strip()
    
   
    if return_hits:
        main_source = all_policies[main_source_idx] if all_policies else None
        return (result_text, main_source)
    
    if all_policies:
        main_source = all_policies[main_source_idx]
        source_section = f"\n\n---\n\n**📄 Quelle:** {main_source['file']} (Seite {main_source['page']})\n\n"
        source_section += f"```\n{main_source['snippet']}\n```"
        result_text += source_section
    
    return result_text
