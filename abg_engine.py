"""
abg_engine.py
=============
Core clinical engine for the ABG Clinical Decision Support tool.

Design principles:
  * Pure function `analyze_abg(...)` -> returns a structured dict. No input()/print()
    inside the engine, so it can be imported by a CLI, a web API, or unit tests.
  * Every clinical rule is traceable to `constants.py`.
  * Safety first: validation runs before any interpretation.

Clinical coverage (v1.0):
  1. Acid-base status & primary disorder
  2. Anion gap (+ albumin correction) and HAGMA/NAGMA classification
  3. Delta ratio (delta-delta) for triple/mixed disorders
  4. Full compensation checks for ALL four primary disorders
     (Winter's, metabolic-alkalosis, acute/chronic respiratory)
  5. Oxygenation: PaO2 (spontaneous) and P/F ratio (ventilated)
  6. Berlin-style ARDS staging (PEEP>=5 gated) with explicit limitations
  7. IBW (Devine) + lung-protective tidal-volume check
  8. RSBI weaning index
  9. Custom heuristic severity score + priority triage
 10. Context-aware ventilator suggestions (ARDS / COPD / general)

This is a rule-based system (NOT AI) intended for use BY a clinician.
"""

from typing import Optional
import constants as C
from validation import validate_abg_inputs, ValidationError


# --------------------------------------------------------------------------- #
#  Small clinical helpers
# --------------------------------------------------------------------------- #
def _anion_gap(na: float, cl: float, hco3: float) -> float:
    return round(na - (cl + hco3), 1)


def _corrected_anion_gap(ag: float, albumin: Optional[float]) -> Optional[float]:
    """Albumin-corrected AG: hypoalbuminaemia masks a raised gap."""
    if albumin is None:
        return None
    correction = C.ALBUMIN_CORRECTION_FACTOR * (C.ALBUMIN_NORMAL - albumin)
    return round(ag + correction, 1)


def _delta_ratio(ag: float, hco3: float) -> Optional[float]:
    """(AG - 12) / (24 - HCO3). Undefined when HCO3 ~ 24."""
    denom = C.HCO3_NORMAL - hco3
    if abs(denom) < 0.5:
        return None
    return round((ag - C.ANION_GAP_REFERENCE) / denom, 2)


def _ideal_body_weight(height_cm: float, sex: str) -> Optional[float]:
    """Devine formula (metric)."""
    if height_cm is None:
        return None
    base = C.IBW_MALE_BASE if sex.strip().lower().startswith("m") else C.IBW_FEMALE_BASE
    ibw = base + C.IBW_HEIGHT_COEFF * (height_cm - C.IBW_REFERENCE_HEIGHT_CM)
    return round(max(ibw, 0), 1)


# --------------------------------------------------------------------------- #
#  Main engine
# --------------------------------------------------------------------------- #
def analyze_abg(
    sample_type: str,
    clinical_context: str,
    ph: float,
    pco2: float,
    hco3: float,
    po2: float,
    na: float,
    cl: float,
    on_vent: str = "no",
    mode: str = "",
    rr=None,
    tv=None,
    peep=None,
    fio2=None,
    albumin: Optional[float] = None,
    height_cm: Optional[float] = None,
    sex: str = "male",
    resp_chronicity: str = "unknown",   # "acute" | "chronic" | "unknown"
) -> dict:
    """
    Interpret an arterial/venous/capillary blood gas with clinical context.

    Returns a structured results dict. If a hard validation error occurs, the
    dict has {"error": <message>, "valid": False} and no interpretation.
    """
    # ---- 0. Validation (safety gate) -------------------------------------- #
    try:
        cleaned, warnings = validate_abg_inputs(
            ph=ph, pco2=pco2, hco3=hco3, po2=po2, na=na, cl=cl,
            on_vent=on_vent, fio2=fio2, peep=peep, rr=rr, tv=tv,
            albumin=albumin, height_cm=height_cm,
        )
    except ValidationError as exc:
        return {"valid": False, "error": str(exc),
                "safety_note": C.SAFETY_NOTE, "safety_note_ar": C.SAFETY_NOTE_AR}

    ph = cleaned["ph"]; pco2 = cleaned["pco2"]; hco3 = cleaned["hco3"]
    po2 = cleaned["po2"]; na = cleaned["na"]; cl = cleaned["cl"]
    fio2 = cleaned["fio2"]; peep = cleaned["peep"]
    rr = cleaned["rr"]; tv = cleaned["tv"]
    albumin = cleaned["albumin"]; height_cm = cleaned["height_cm"]

    sample_type = str(sample_type).strip().upper()
    clinical_context = str(clinical_context).strip().upper()
    on_vent = str(on_vent).strip().lower()

    r = {
        "valid": True,
        "warnings": warnings,
        "acid_base_status": "",
        "primary_disorder": "",
        "compensation": "",
        "compensation_status": "",
        "secondary_disorder": "",
        "final_interpretation": "",
        "anion_gap": None,
        "anion_gap_corrected": None,
        "anion_gap_interpretation": "",
        "delta_ratio": None,
        "delta_ratio_interpretation": "",
        "oxygenation_note": "",
        "pf_ratio": None,
        "oxygenation_status": "",
        "ventilator_status": "",
        "ventilator_settings": {},
        "ibw_kg": None,
        "tv_per_kg": None,
        "lung_protective": "",
        "rsbi": None,
        "rsbi_interpretation": "",
        "context_interpretation": "",
        "context_notes": [],
        "ventilator_suggestions": [],
        "risk_flag": "",
        "severity_score": 0,
        "severity_label": C.SEVERITY_LABEL,
        "priority_level": "",
        "clinical_flags": [],
        "action_plan": [],
        "safety_note": C.SAFETY_NOTE,
        "safety_note_ar": C.SAFETY_NOTE_AR,
    }

    # ---- 1. Acid-base status --------------------------------------------- #
    if ph < C.PH_LOW:
        r["acid_base_status"] = "Acidemia"
    elif ph > C.PH_HIGH:
        r["acid_base_status"] = "Alkalemia"
    else:
        r["acid_base_status"] = "Normal pH (compensated or mixed possible)"

    # ---- 2. Primary disorder --------------------------------------------- #
    if ph < C.PH_LOW:
        if pco2 > C.PACO2_HIGH and hco3 < C.HCO3_LOW:
            r["primary_disorder"] = "Mixed Acidosis (Respiratory + Metabolic)"
        elif pco2 > C.PACO2_HIGH:
            r["primary_disorder"] = "Respiratory Acidosis"
        elif hco3 < C.HCO3_LOW:
            r["primary_disorder"] = "Metabolic Acidosis"
        else:
            r["primary_disorder"] = "Acidemia - pattern unclear (review)"
    elif ph > C.PH_HIGH:
        if pco2 < C.PACO2_LOW and hco3 > C.HCO3_HIGH:
            r["primary_disorder"] = "Mixed Alkalosis (Respiratory + Metabolic)"
        elif pco2 < C.PACO2_LOW:
            r["primary_disorder"] = "Respiratory Alkalosis"
        elif hco3 > C.HCO3_HIGH:
            r["primary_disorder"] = "Metabolic Alkalosis"
        else:
            r["primary_disorder"] = "Alkalemia - pattern unclear (review)"
    else:
        # normal pH but possibly deranged CO2/HCO3
        if pco2 > C.PACO2_HIGH or pco2 < C.PACO2_LOW or hco3 > C.HCO3_HIGH or hco3 < C.HCO3_LOW:
            r["primary_disorder"] = "Normal pH with abnormal CO2/HCO3 - fully compensated or mixed disorder"
        else:
            r["primary_disorder"] = "Normal acid-base status"

    # ---- 3. Anion gap ---------------------------------------------------- #
    ag = _anion_gap(na, cl, hco3)
    r["anion_gap"] = ag
    ag_corr = _corrected_anion_gap(ag, albumin)
    r["anion_gap_corrected"] = ag_corr

    effective_ag = ag_corr if ag_corr is not None else ag
    if effective_ag > C.ANION_GAP_NORMAL_HIGH:
        r["anion_gap_interpretation"] = (
            f"High anion gap ({effective_ag}) - suggests HAGMA "
            f"(e.g. lactate, ketones, toxins, uraemia)"
        )
    elif effective_ag < C.ANION_GAP_NORMAL_LOW:
        r["anion_gap_interpretation"] = (
            f"Low anion gap ({effective_ag}) - consider hypoalbuminaemia, "
            f"paraproteinaemia, or lab artefact"
        )
    else:
        r["anion_gap_interpretation"] = f"Normal anion gap ({effective_ag})"

    # ---- 4. Delta ratio (only meaningful with a metabolic acidosis) ------ #
    is_met_acidosis = "Metabolic Acidosis" in r["primary_disorder"] or \
                      "Mixed Acidosis" in r["primary_disorder"]
    if is_met_acidosis and effective_ag > C.ANION_GAP_NORMAL_HIGH:
        dr = _delta_ratio(effective_ag, hco3)
        r["delta_ratio"] = dr
        if dr is not None:
            if dr < C.DELTA_RATIO_NAGMA_MAX:
                r["delta_ratio_interpretation"] = "Delta ratio < 0.4: concurrent normal-AG metabolic acidosis (NAGMA)"
            elif dr < C.DELTA_RATIO_MIXED_MAX:
                r["delta_ratio_interpretation"] = "Delta ratio 0.4-1: mixed HAGMA + NAGMA"
            elif dr <= C.DELTA_RATIO_PURE_MAX:
                r["delta_ratio_interpretation"] = "Delta ratio 1-2: pure high-AG metabolic acidosis"
            else:
                r["delta_ratio_interpretation"] = "Delta ratio > 2: coexisting metabolic alkalosis or chronic respiratory acidosis"

    # ---- 5. Compensation (ALL four disorders) ---------------------------- #
    _assess_compensation(r, ph, pco2, hco3, resp_chronicity)

    # ---- 6. Oxygenation -------------------------------------------------- #
    if on_vent != "yes":
        if sample_type == "ABG":
            if po2 < C.PAO2_SEVERE_HYPOXEMIA:
                r["oxygenation_note"] = "Severe hypoxemia"
            elif po2 < C.PAO2_MILD_HYPOXEMIA:
                r["oxygenation_note"] = "Mild to moderate hypoxemia"
            elif po2 <= C.PAO2_NORMAL_UPPER:
                r["oxygenation_note"] = "PaO2 within normal range"
            else:
                r["oxygenation_note"] = "PaO2 above normal range (supplemental O2?)"
        elif sample_type == "VBG":
            r["oxygenation_note"] = "Oxygenation cannot be reliably assessed from VBG"
        elif sample_type == "CBG":
            r["oxygenation_note"] = "Oxygenation assessment from CBG is limited; ABG preferred"
        else:
            r["oxygenation_note"] = "Unknown sample type - oxygenation limited"
        r["oxygenation_status"] = r["oxygenation_note"]

    # P/F ratio (ventilated)
    if on_vent == "yes" and fio2 and fio2 > 0:
        pf = round(po2 / (fio2 / 100.0), 1)
        r["pf_ratio"] = pf
        if pf >= C.PF_NORMAL:
            r["oxygenation_status"] = "No significant impairment"
        elif pf >= C.PF_MILD:
            r["oxygenation_status"] = "Mild oxygenation impairment"
        elif pf >= C.PF_MODERATE:
            r["oxygenation_status"] = "Moderate oxygenation impairment"
        else:
            r["oxygenation_status"] = "Severe oxygenation impairment"

    # ---- 7. Ventilator settings + IBW + lung-protective check ------------ #
    if on_vent == "yes":
        r["ventilator_status"] = "On mechanical ventilation"
        r["ventilator_settings"] = {
            "Mode": mode, "RR": rr, "TV": tv, "PEEP": peep, "FiO2": fio2
        }
        ibw = _ideal_body_weight(height_cm, sex)
        r["ibw_kg"] = ibw
        if ibw and tv:
            tv_per_kg = round(tv / ibw, 1)
            r["tv_per_kg"] = tv_per_kg
            if tv_per_kg <= C.LUNG_PROTECTIVE_TV_HIGH:
                r["lung_protective"] = f"Lung-protective ({tv_per_kg} mL/kg IBW)"
            elif tv_per_kg <= C.LUNG_PROTECTIVE_TV_CEILING:
                r["lung_protective"] = f"Borderline ({tv_per_kg} mL/kg IBW) - aim 4-6 mL/kg"
            else:
                r["lung_protective"] = f"NOT lung-protective ({tv_per_kg} mL/kg IBW) - reduce TV"
        # RSBI
        if rr and tv:
            rsbi = round(rr / (tv / 1000.0), 1)
            r["rsbi"] = rsbi
            if rsbi > C.RSBI_FAILURE_THRESHOLD:
                r["rsbi_interpretation"] = f"RSBI {rsbi} > 105: weaning failure likely"
            else:
                r["rsbi_interpretation"] = f"RSBI {rsbi} <= 105: weaning may be favourable (clinical correlation required)"
    else:
        r["ventilator_status"] = "Not on mechanical ventilation"

    # ---- 8. Clinical context --------------------------------------------- #
    _assess_context(r, clinical_context, on_vent, peep)

    # ---- 9. Ventilator suggestions --------------------------------------- #
    _build_suggestions(r, clinical_context, on_vent)

    # ---- 10. Risk flag --------------------------------------------------- #
    _assess_risk(r, ph, po2, sample_type, on_vent)

    # ---- 11. Severity + priority + flags + action plan ------------------- #
    _assess_severity(r, ph, clinical_context, on_vent)

    return r


# --------------------------------------------------------------------------- #
#  Compensation engine (all four primary disorders)
# --------------------------------------------------------------------------- #
def _assess_compensation(r, ph, pco2, hco3, resp_chronicity):
    pd = r["primary_disorder"]

    if "Metabolic Acidosis" in pd and "Mixed" not in pd:
        expected = C.WINTERS_SLOPE * hco3 + C.WINTERS_INTERCEPT
        lo, hi = expected - C.WINTERS_TOLERANCE, expected + C.WINTERS_TOLERANCE
        r["compensation"] = f"Winter's expected PaCO2: {round(expected,1)} (range {round(lo,1)}-{round(hi,1)})"
        if pco2 < lo:
            r["secondary_disorder"] = "Respiratory Alkalosis"
            r["compensation_status"] = "PaCO2 lower than expected -> superimposed respiratory alkalosis"
            r["final_interpretation"] = "Metabolic Acidosis + Respiratory Alkalosis"
        elif pco2 > hi:
            r["secondary_disorder"] = "Respiratory Acidosis"
            r["compensation_status"] = "PaCO2 higher than expected -> superimposed respiratory acidosis"
            r["final_interpretation"] = "Metabolic Acidosis + Respiratory Acidosis"
        else:
            r["compensation_status"] = "Appropriate respiratory compensation"
            r["final_interpretation"] = "Metabolic Acidosis (appropriately compensated)"

    elif pd == "Metabolic Alkalosis":
        expected = C.MET_ALK_SLOPE * hco3 + C.MET_ALK_INTERCEPT
        lo, hi = expected - C.MET_ALK_TOLERANCE, expected + C.MET_ALK_TOLERANCE
        r["compensation"] = f"Expected PaCO2: {round(expected,1)} (range {round(lo,1)}-{round(hi,1)})"
        if pco2 < lo:
            r["secondary_disorder"] = "Respiratory Alkalosis"
            r["compensation_status"] = "PaCO2 lower than expected -> superimposed respiratory alkalosis"
            r["final_interpretation"] = "Metabolic Alkalosis + Respiratory Alkalosis"
        elif pco2 > hi:
            r["secondary_disorder"] = "Respiratory Acidosis"
            r["compensation_status"] = "PaCO2 higher than expected -> superimposed respiratory acidosis"
            r["final_interpretation"] = "Metabolic Alkalosis + Respiratory Acidosis"
        else:
            r["compensation_status"] = "Appropriate respiratory compensation"
            r["final_interpretation"] = "Metabolic Alkalosis (appropriately compensated)"

    elif pd == "Respiratory Acidosis":
        delta_co2 = pco2 - C.PACO2_NORMAL
        exp_acute = C.HCO3_NORMAL + C.HCO3_PER_10_ACUTE_RESP_ACIDOSIS * (delta_co2 / 10.0)
        exp_chronic = C.HCO3_NORMAL + C.HCO3_PER_10_CHRONIC_RESP_ACIDOSIS * (delta_co2 / 10.0)
        r["compensation"] = (
            f"Expected HCO3: acute ~{round(exp_acute,1)}, chronic ~{round(exp_chronic,1)}"
        )
        r["compensation_status"], r["final_interpretation"] = _resp_compensation_verdict(
            hco3, exp_acute, exp_chronic, "Respiratory Acidosis", raised=True)

    elif pd == "Respiratory Alkalosis":
        delta_co2 = C.PACO2_NORMAL - pco2
        exp_acute = C.HCO3_NORMAL - C.HCO3_PER_10_ACUTE_RESP_ALKALOSIS * (delta_co2 / 10.0)
        exp_chronic = C.HCO3_NORMAL - C.HCO3_PER_10_CHRONIC_RESP_ALKALOSIS * (delta_co2 / 10.0)
        r["compensation"] = (
            f"Expected HCO3: acute ~{round(exp_acute,1)}, chronic ~{round(exp_chronic,1)}"
        )
        r["compensation_status"], r["final_interpretation"] = _resp_compensation_verdict(
            hco3, exp_acute, exp_chronic, "Respiratory Alkalosis", raised=False)

    else:
        r["final_interpretation"] = pd


def _resp_compensation_verdict(hco3, exp_acute, exp_chronic, label, raised, tol=2.0):
    """
    Decide whether a respiratory disorder is acute, chronic, partially
    compensated, or has a superimposed metabolic process.
    """
    if abs(hco3 - exp_acute) <= tol:
        return "Consistent with an ACUTE process (minimal renal compensation)", f"Acute {label}"
    if abs(hco3 - exp_chronic) <= tol:
        return "Consistent with a CHRONIC process (renal compensation present)", f"Chronic {label}"
    if exp_acute < hco3 < exp_chronic or exp_chronic < hco3 < exp_acute:
        return "Partial compensation (between acute and chronic expected values)", f"{label} (partially compensated)"
    # HCO3 outside both -> superimposed metabolic disorder
    if raised:  # respiratory acidosis
        if hco3 > max(exp_acute, exp_chronic):
            return "HCO3 above expected -> superimposed metabolic ALKALOSIS", f"{label} + Metabolic Alkalosis"
        return "HCO3 below expected -> superimposed metabolic ACIDOSIS", f"{label} + Metabolic Acidosis"
    else:      # respiratory alkalosis
        if hco3 < min(exp_acute, exp_chronic):
            return "HCO3 below expected -> superimposed metabolic ACIDOSIS", f"{label} + Metabolic Acidosis"
        return "HCO3 above expected -> superimposed metabolic ALKALOSIS", f"{label} + Metabolic Alkalosis"


# --------------------------------------------------------------------------- #
#  Clinical context
# --------------------------------------------------------------------------- #
def _assess_context(r, clinical_context, on_vent, peep):
    if clinical_context == "ARDS":
        pf = r["pf_ratio"]
        if on_vent == "yes" and peep is not None and peep >= C.ARDS_MIN_PEEP and pf is not None:
            if pf < C.PF_MODERATE:
                r["context_interpretation"] = "Severe ARDS (P/F < 100)"
            elif pf < C.PF_MILD:
                r["context_interpretation"] = "Moderate ARDS (P/F 100-199)"
            elif pf < C.PF_NORMAL:
                r["context_interpretation"] = "Mild ARDS (P/F 200-299)"
            else:
                r["context_interpretation"] = "P/F >= 300 does not meet ARDS oxygenation threshold"
            r["context_notes"].append(
                "P/F-based staging only. Full Berlin criteria also require acute "
                "onset, bilateral infiltrates on imaging, and exclusion of a purely "
                "cardiogenic cause - confirm clinically."
            )
        else:
            r["context_interpretation"] = "ARDS context given, but data insufficient (need ventilation with PEEP>=5 and a valid P/F)"
        if r["pf_ratio"] is not None and r["pf_ratio"] < C.PF_CRITICAL:
            r["context_notes"].append("Critical hypoxemia - urgent escalation required")

    elif clinical_context == "COPD":
        r["context_interpretation"] = "COPD context"
        r["context_notes"].append("Prioritize pH and PaCO2 trend over absolute HCO3")
        if "Respiratory Acidosis" in r["primary_disorder"] or r["secondary_disorder"] == "Respiratory Acidosis":
            r["context_notes"].append("Hypercapnic ventilatory failure pattern present")
        if "Chronic Respiratory Acidosis" in r["final_interpretation"]:
            r["context_notes"].append(
                "Chronic compensated pattern - target the patient's OWN baseline pH/PaCO2, "
                "not textbook normals (avoid over-correction)."
            )
        r["context_notes"].append(
            "P/F ratio describes oxygenation severity but does not by itself drive COPD decisions."
        )
    else:
        r["context_interpretation"] = "General clinical interpretation"


# --------------------------------------------------------------------------- #
#  Ventilator suggestions
# --------------------------------------------------------------------------- #
def _build_suggestions(r, clinical_context, on_vent):
    if on_vent != "yes":
        return
    s = r["ventilator_suggestions"]

    if r["secondary_disorder"]:
        s.append("Mixed disorder present - treat the underlying cause first; avoid reflexive ventilator changes")

    if clinical_context == "ARDS":
        s.append("Apply lung-protective ventilation (target 4-6 mL/kg IBW)")
        s.append("Increase PEEP and optimize FiO2 before increasing minute ventilation")
        if r["pf_ratio"] is not None and r["pf_ratio"] < C.PF_MODERATE:
            s.append("Consider prone positioning (P/F < 100)")
        if r["pf_ratio"] is not None and r["pf_ratio"] < C.PF_CRITICAL:
            s.append("Consider ECMO referral if refractory hypoxemia")
    elif clinical_context == "COPD":
        s.append("Avoid aggressive ventilation increases (risk of dynamic hyperinflation / air trapping)")
        s.append("Prefer adjusting RR over large VT increases; allow permissive hypercapnia toward baseline")
    elif "Respiratory Acidosis" in r["primary_disorder"] and not r["secondary_disorder"]:
        s.append("Increase minute ventilation (raise RR first; adjust VT cautiously)")
    elif "Respiratory Alkalosis" in r["primary_disorder"] and not r["secondary_disorder"]:
        s.append("Reduce minute ventilation (lower RR first)")
    elif r["primary_disorder"] == "Metabolic Acidosis":
        s.append("Ensure adequate ventilation and address the metabolic cause (do not suppress compensation)")
    elif r["primary_disorder"] == "Metabolic Alkalosis":
        s.append("Reduce ventilation cautiously only if clinically indicated")

    if r["lung_protective"].startswith("NOT"):
        s.append("Current tidal volume exceeds lung-protective range - reduce toward 4-6 mL/kg IBW")


# --------------------------------------------------------------------------- #
#  Risk flag
# --------------------------------------------------------------------------- #
def _assess_risk(r, ph, po2, sample_type, on_vent):
    pf = r["pf_ratio"]
    if pf is not None and pf < C.PF_CRITICAL:
        r["risk_flag"] = "Critical - life-threatening hypoxemia"
    elif ph < C.PH_CRIT_LOW:
        r["risk_flag"] = "High - severe acidemia"
    elif ph > C.PH_CRIT_HIGH:
        r["risk_flag"] = "High - severe alkalemia"
    elif sample_type == "ABG" and po2 < C.PAO2_SEVERE_HYPOXEMIA and on_vent != "yes":
        r["risk_flag"] = "High - severe hypoxemia"
    elif "mixed" in r["primary_disorder"].lower() or r["secondary_disorder"]:
        r["risk_flag"] = "Moderate to High - mixed disorder"
    elif on_vent == "yes":
        r["risk_flag"] = "Moderate - ventilated patient requires close monitoring"
    else:
        r["risk_flag"] = "Moderate/Low - clinical correlation required"


# --------------------------------------------------------------------------- #
#  Severity / priority / flags / action plan
# --------------------------------------------------------------------------- #
def _assess_severity(r, ph, clinical_context, on_vent):
    pf = r["pf_ratio"]
    if pf is not None:
        if pf < C.PF_MODERATE:
            r["severity_score"] = 10
        elif pf < C.PF_MILD:
            r["severity_score"] = 8
        elif pf < C.PF_NORMAL:
            r["severity_score"] = 5
        else:
            r["severity_score"] = 2
    else:
        if ph < C.PH_CRIT_LOW or ph > C.PH_CRIT_HIGH:
            r["severity_score"] = 7
        elif ph < 7.30 or ph > 7.50:
            r["severity_score"] = 5
        else:
            r["severity_score"] = 2

    s = r["severity_score"]
    if s >= 9:
        r["priority_level"] = "IMMEDIATE ICU ACTION"
    elif s >= 7:
        r["priority_level"] = "URGENT REVIEW"
    elif s >= 4:
        r["priority_level"] = "MODERATE"
    else:
        r["priority_level"] = "STABLE"

    if clinical_context == "ARDS":
        r["clinical_flags"].append("ARDS")
    if pf is not None and pf < C.PF_MODERATE:
        r["clinical_flags"].append("Critical Hypoxemia")
    if on_vent == "yes":
        r["clinical_flags"].append("Ventilated Patient")
    if r["secondary_disorder"]:
        r["clinical_flags"].append("Mixed Disorder")

    if r["priority_level"] == "IMMEDIATE ICU ACTION":
        r["action_plan"] += [
            "Increase PEEP (stepwise, titrated strategy)",
            "Optimize FiO2 to target SpO2 88-95%",
            "Apply lung-protective ventilation (4-6 mL/kg IBW)",
            "Consider prone positioning",
            "Evaluate for ECMO referral if refractory hypoxemia",
        ]
    if "Respiratory Acidosis" in r["primary_disorder"] and not r["secondary_disorder"]:
        r["action_plan"].append("Increase minute ventilation (raise RR carefully)")
