# Risikoanalyse-Tool für KMU

Dieses Tool unterstützt KMU bei der Identifizierung von Cybersicherheitsrisiken, der Durchführung einer strukturierten Risikoanalyse und der Generierung von passgenauen Handlungsempfehlungen auf Basis eigener Sicherheitsrichtlinien (Policies).

## Voraussetzungen

Stelle sicher, dass folgende Software installiert ist:
- **Python 3.9 oder höher**
- Ein **OpenAI API-Key** (für die Generierung der Empfehlungen)

## Installation & Einrichtung

Folge diesen Schritten, um das Tool lokal auszuführen:

### 1. Repository klonen oder herunterladen
Lade den Code herunter und entpacke ihn.

### 2. Virtuelle Umgebung erstellen (empfohlen)
Öffne ein Terminal im Projektordner und führe aus:
```powershell
python -m venv .venv
```
Aktiviere die Umgebung:
- **Windows:** `.venv\Scripts\activate`
- **Mac/Linux:** `source .venv/bin/activate`

### 3. Abhängigkeiten installieren
Installiere die benötigten Python-Bibliotheken:
```powershell
pip install -r requirements.txt
```

### 4. Konfiguration (WICHTIG)
Damit das Tool auf die KI zugreifen kann, muss man einen API-Key hinterlegen:
1. Suche die Datei `.env.example` im Hauptverzeichnis.
2. Kopiere diese Datei und nenne die Kopie `.env`.
3. Öffne die neue `.env` und ersetze durch deinen echten OpenAI API-Key:
   `OPENAI_API_KEY=dein-echter-key-hier`

Eine Anleitung zum Erstellen des API-Key findest man im Abschnitt "OpenAI API-Key erstellen".

### 5. Policies hinzufügen/OPTIONAL
Um eigene Policies hinzuzufügen lege deine eigenen Sicherheitsrichtlinien  als **PDF-Dateien** in den Ordner `policies/`. Das Tool nutzt diese Dokumente, um die Empfehlungen direkt an deine Vorgaben anzupassen. Achtung du musst anschließend im UI neu indexieren.

## Starten der Anwendung

Führe im Terminal folgenden Befehl aus:
```powershell
streamlit run app.py
```
Die Anwendung öffnet sich automatisch in deinem Browser (meist unter `http://localhost:8501`).


## Methodik & Risikoberechnung

### 1. Die Risikoformel
Das Risiko wird für jede Kombination aus Bedrohung, Schwachstelle und Asset berechnet:
**Risiko = Eintrittswahrscheinlichkeit (1-5) × Auswirkung (1-5)**

### 2. Berechnungsmodi
In der Risiko-Evaluation kann man zwischen zwei Ansätzen wählen:
- **📊 Durchschnitt (Average):** Berechnet das Risiko über den Durchschnitt aller Impact Werte verknüpften Assets. 
- **📈 Maximum-Prinzip:** Setzt bei mehreren Assets jeweils den höchsten Impact Wert an (Worst-Case). 

Wird im Fragebogen der Status als **Kritische Infrastruktur (KRITIS)** bestätigt, schaltet das System automatisch auf das **Maximum-Prinzip** um. 

## Bedienungsanleitung & UI-Struktur

Die Anwendung ist in drei Tabs unterteilt, die nacheinander durchlaufen werden sollten:

### 📥 Datenverwaltung (Sidebar)
In der linken Seitenleiste findet man die zentralen Werkzeuge:
- **Import/Export:** Man kann den aktuellen Fragebogen als `.json`-Datei sichern oder bestehende Profile hochladen (json). So kann man Daten zwischen "Kompakt-Check" und "Vollständiger Analyse" übertragen.
- **Policy-Index:** Hier sieht man alle geladenen PDFs. Nach dem Hinzufügen neuer Dateien in den `policies/`-Ordner kann man den Index hier neu aufbauen.

### 1. Tab: Fragebogen (Datenerhebung)
Hier erfassen Sie den Ist-Zustand Ihrer IT-Sicherheit.
- **Modus wählen:** Man kann oben zwischen "Kompakt-Check" (schneller Überblick) und "Vollständige Analyse" (tiefgehende Prüfung) wählen.
- **Bearbeiten:** Auf "Bearbeiten" klicken, um Felder freizuschalten. Die Fragen sind nach Themen (z.B. Identitätsmanagement, Cloud, Backup) gruppiert.
- **Speichern:** Auf"Speichern" klicken, um die Daten zu sichern. Das Tool berechnet im Hintergrund sofort die neuen Risikowerte.

### 2. Tab: Risiko-Evaluation (Analyse)
In diesem Bereich werden die Ergebnisse visualisiert.
- **Risiko-Matrix:** Hier sieht man welche Bedrohungen (Threats) oder Schwachstellen (Vulnerabilities) oder Assets welches Risiko aufweisen.
- **Detail-Ansichten:** Man kann in den Unter-Tabs (Vulnerabilities, Threats, Assets) tiefer in die Berechnungen einsehen.
- **Feintuning:** Über die Schaltfläche "Assets & Threats anpassen" kann man Basiswerte manuell korrigieren oder Gewichtungen anpassen oder den Berechnungsansatz wählen.

### 3. Tab: Handlungsempfehlungen (Behebung)
Hier erhält man konkrete Hilfe zur Risikoreduzierung.
- **KI-Generierung:** Das Tool analysiert die Antworten und sucht in den unter `policies/` hochgeladenen PDFs nach passenden Vorgaben.
- **Struktur:** Jede Empfehlung enthält eine Begründung, einen konkreten Umsetzungsplan und die zugehörige Quelle aus Ihren Richtlinien.
- **Fortschritt:** Man kann Maßnahmen als "umgesetzt" markieren, wodurch sich das Risiko in der Evaluation automatisch verringert. 
- **Export:** Ganz unten können Sie den gesamten Bericht als PDF generieren und herunterladen.

---

## OpenAI API-Key erstellen

Falls man keinen API-Key hat, muss man folgendes:

1.  **Registrierung:** Erstellen Sie ein Konto auf [platform.openai.com](https://platform.openai.com/).
2.  **Guthaben aufladen:** Die API-Nutzung ist kostenpflichtig. Hinterlegen Sie unter *Settings > Billing* ein Startguthaben (z.B. 5€).
3.  **Key generieren:** Gehen Sie zu *API Keys* und klicken Sie auf **"Create new secret key"**.
4.  **Kopieren:** Kopieren Sie den Key sofort und fügen Sie ihn in Ihre `.env`-Datei ein.

---

## Struktur
```
risk-tool/
├─ app.py             
├─ llm.py               
├─ intake_flow.py        
├─ risk_engine.py      
├─ policy_search.py      
├─ recommender.py     
├─ data/
│  └─ risk_catalog.yaml 
├─ policies/
│  └─ README.txt        
├─ requirements.txt
├─ .env.example
└─ README.md