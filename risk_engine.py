
# Risiko-Logik & Berechnungen
import yaml
from typing import Optional, Union
from pydantic import BaseModel, field_validator

# Datenmodell Fragebogen
class ProfileView(BaseModel):
    has_mfa: Optional[Union[float, bool]] = None
    has_password_rules: Optional[Union[float, bool]] = None
    has_password_manager: Optional[Union[float, bool]] = None
    inactive_accounts_removed: Optional[Union[float, bool]] = None
    has_least_privilege: Optional[Union[float, bool]] = None
    has_security_role: Optional[Union[float, bool]] = None
    has_security_policies: Optional[Union[float, bool]] = None
    has_incident_plan: Optional[Union[float, bool]] = None
    access_list_exists: Optional[Union[float, bool]] = None
    access_list_reviewed: Optional[Union[float, bool]] = None
    audits_done: Optional[Union[float, bool]] = None
    has_account_lifecycle: Optional[Union[float, bool]] = None
    admin_accounts_protected: Optional[Union[float, bool]] = None
    has_sso: Optional[Union[float, bool]] = None
    login_monitoring: Optional[Union[float, bool]] = None

    has_patch_mgmt: Optional[Union[float, bool]] = None
    has_vuln_scans: Optional[Union[float, bool]] = None
    has_edr: Optional[Union[float, bool]] = None
    has_firewall: Optional[Union[float, bool]] = None
    network_segmented: Optional[Union[float, bool]] = None
    has_mdm: Optional[Union[float, bool]] = None
    logging_enabled: Optional[Union[float, bool]] = None
    logs_reviewed: Optional[Union[float, bool]] = None
    has_ids_ips: Optional[Union[float, bool]] = None

    daily_backups: Optional[Union[float, bool]] = None
    has_offsite_backup: Optional[Union[float, bool]] = None
    backup_tested: Optional[Union[float, bool]] = None
    device_loss_protection: Optional[Union[float, bool]] = None

    uses_cloud: Optional[Union[float, bool]] = None
    cloud_config_secure: Optional[Union[float, bool]] = None
    cloud_mfa_enabled: Optional[Union[float, bool]] = None
    cloud_logging: Optional[Union[float, bool]] = None
    cloud_shares_controlled: Optional[Union[float, bool]] = None
    cloud_permissions_reviewed: Optional[Union[float, bool]] = None
    cloud_policy_exists: Optional[Union[float, bool]] = None
    cloud_config_tested: Optional[Union[float, bool]] = None
    cloud_dlp: Optional[Union[float, bool]] = None

    has_training: Optional[Union[float, bool]] = None
    has_phishing_tests: Optional[Union[float, bool]] = None
    email_awareness: Optional[Union[float, bool]] = None
    has_incident_reporting: Optional[Union[float, bool]] = None
    has_byod_rules: Optional[Union[float, bool]] = None
    has_mobile_device_policy: Optional[Union[float, bool]] = None

    has_data_classification: Optional[Union[float, bool]] = None
    gdpr_compliant: Optional[Union[float, bool]] = None
    data_retention_rules: Optional[Union[float, bool]] = None
    data_encrypted_at_rest: Optional[Union[float, bool]] = None
    data_encrypted_in_transit: Optional[Union[float, bool]] = None
    vendors_checked: Optional[Union[float, bool]] = None
    vendors_have_avv: Optional[Union[float, bool]] = None

    has_asset_inventory: Optional[Union[float, bool]] = None

    # Werte-Gewichtung
    def get_weight(self, field_name: str) -> Optional[float]:
        val = getattr(self, field_name, None)
        if val is None:
            return None
        if isinstance(val, bool):
            return 0.0 if val else 1.0
        return float(val)


# Katalog laden
with open("data/risk_catalog.yaml", "r", encoding="utf-8") as f:
    CATALOG = yaml.safe_load(f)

# Indizes für schnellen Zugriff
ASSET_INDEX = {a["id"]: a for a in CATALOG["assets"]}
THREAT_INDEX = {t["id"]: t for t in CATALOG["threats"]}
VULN_INDEX = {v["id"]: v for v in CATALOG["vulnerabilities"]}


# Basis-Werte (Impact/Likelihood)
def base_scores(asset_id: str, threat_id: str, vuln_id: str, 
                custom_assets: dict = None, custom_threats: dict = None):
    asset = ASSET_INDEX[asset_id]
    threat = THREAT_INDEX[threat_id]
    vuln = VULN_INDEX[vuln_id]

    impact = custom_assets.get(asset_id, asset["impact"]) if custom_assets else asset["impact"]
    likelihood = custom_threats.get(threat_id, threat["likelihood"]) if custom_threats else threat["likelihood"]

    return {
        "likelihood": likelihood,
        "impact": impact,
        "likelihood_mod": vuln.get("likelihood_mod", 0),
        "impact_mod": vuln.get("impact_mod", 0),
    }


# Wert-Begrenzung
def clamp(x, lo, hi):
    return max(lo, min(hi, x))

# Modifikatoren anwenden
def apply_modifiers(base: dict, profile: ProfileView, threat_id: str, vuln_id: str, control_weight: Optional[float] = None):
    l0 = base["likelihood"]
    i0 = base["impact"]

    lm = base["likelihood_mod"]
    im = base["impact_mod"]

    if control_weight is not None:
        likelihood = (l0 * control_weight) + (lm * control_weight)
        impact = (i0 * control_weight) + (im * control_weight)
    else:
        likelihood = l0 + lm
        impact = i0 + im

    return {
        "likelihood": clamp(likelihood, 0.1, 5),
        "impact": clamp(impact, 0.1, 5)
    }




def risk_score(likelihood, impact):
    return likelihood * impact



# Check ob Schwachstelle aktiv
def question_vuln_triggered(vuln_id: str, profile: ProfileView) -> bool:
    v = VULN_INDEX[vuln_id]
    controls = v.get("controls", [])

    if not controls:
        return True

    any_answer = False
    for field in controls:
        weight = profile.get_weight(field)

        if weight is None:
            continue

        any_answer = True

        if weight > 0:
            return True

    if not any_answer:
        return False

    return False



# Relevanz-Prüfung
def vuln_relevant_for(vuln_id: str, asset_id: str, threat_id: str) -> bool:
    vuln = VULN_INDEX[vuln_id]

    allowed_assets = vuln.get("assets", [])
    allowed_threats = vuln.get("threats", [])

    if not allowed_assets and not allowed_threats:
        return True

    if allowed_assets and asset_id not in allowed_assets:
        return False

    if allowed_threats and threat_id not in allowed_threats:
        return False

    return True
