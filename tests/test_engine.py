"""
test_engine.py
==============
Clinical validation test suite for the ABG engine.

Each test is a recognised acid-base teaching case with a known answer.
Run with:  python -m pytest tests/  (or)  python tests/test_engine.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abg_engine import analyze_abg
from validation import ValidationError


# --------------------------------------------------------------------------- #
#  Helper
# --------------------------------------------------------------------------- #
def run(**kw):
    base = dict(sample_type="ABG", clinical_context="OTHER",
                na=140, cl=104, on_vent="no")
    base.update(kw)
    return analyze_abg(**base)


PASS, FAIL = 0, 0
def check(desc, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {desc}")
    else:
        FAIL += 1
        print(f"  FAIL  {desc}")


# --------------------------------------------------------------------------- #
#  1. Simple acid-base cases
# --------------------------------------------------------------------------- #
print("\n[1] Simple acid-base disorders")

# High anion gap metabolic acidosis (DKA-like), appropriately compensated:
# pH 7.15, CO2 20, HCO3 8, Na 140, Cl 100. Winter's expected = 1.5*8+8 = 20 (18-22).
r = run(ph=7.15, pco2=20, hco3=8, po2=95, na=140, cl=100)
check("HAGMA: primary = Metabolic Acidosis", "Metabolic Acidosis" in r["primary_disorder"])
check("HAGMA: anion gap high", r["anion_gap"] > 12)
check("HAGMA: Winter's compensation appropriate",
      "appropriately compensated" in r["final_interpretation"].lower())

# Same numbers but CO2 = 30 (above Winter's range) -> superimposed respiratory acidosis
r = run(ph=7.05, pco2=30, hco3=8, po2=95, na=140, cl=100)
check("HAGMA + inadequate resp compensation detected",
      r["secondary_disorder"] == "Respiratory Acidosis")

# Normal anion gap metabolic acidosis (diarrhoea): pH 7.30, CO2 34, HCO3 16, Na 140, Cl 114
r = run(ph=7.30, pco2=34, hco3=16, po2=95, na=140, cl=114)
check("NAGMA: anion gap normal", 8 <= r["anion_gap"] <= 12)

# Respiratory acidosis, acute: pH 7.25, CO2 60, HCO3 26
r = run(ph=7.25, pco2=60, hco3=26, po2=90)
check("Acute resp acidosis: primary correct", r["primary_disorder"] == "Respiratory Acidosis")
check("Acute resp acidosis: labelled acute", "Acute" in r["final_interpretation"])

# Respiratory acidosis, chronic (COPD): pH 7.34, CO2 60, HCO3 31
r = run(ph=7.34, pco2=60, hco3=31, po2=70, clinical_context="COPD")
check("Chronic resp acidosis: labelled chronic", "Chronic" in r["final_interpretation"])

# Respiratory alkalosis: pH 7.52, CO2 28, HCO3 22
r = run(ph=7.52, pco2=28, hco3=22, po2=98)
check("Resp alkalosis: primary correct", r["primary_disorder"] == "Respiratory Alkalosis")

# Metabolic alkalosis: pH 7.50, CO2 46, HCO3 34
r = run(ph=7.50, pco2=46, hco3=34, po2=95)
check("Metabolic alkalosis: primary correct", r["primary_disorder"] == "Metabolic Alkalosis")
check("Metabolic alkalosis: compensation computed", r["compensation"] != "")


# --------------------------------------------------------------------------- #
#  2. Mixed / triple disorders
# --------------------------------------------------------------------------- #
print("\n[2] Mixed disorders (delta ratio & compensation)")

# HAGMA + concurrent metabolic alkalosis: high AG but HCO3 not as low as expected
# pH 7.40, CO2 40, HCO3 24, Na 140, Cl 90 -> AG = 26 (high) but HCO3 normal -> delta>2
r = run(ph=7.40, pco2=40, hco3=24, po2=95, na=140, cl=90)
check("Triple: high anion gap detected", r["anion_gap"] > 20)

# Met acidosis with superimposed resp acidosis (inadequate compensation)
# pH 7.15, CO2 40 (should be ~23 by Winter's), HCO3 15
r = run(ph=7.15, pco2=40, hco3=15, po2=95, na=140, cl=110)
check("Met acidosis + resp acidosis detected",
      r["secondary_disorder"] == "Respiratory Acidosis")


# --------------------------------------------------------------------------- #
#  3. Ventilated / ARDS / oxygenation
# --------------------------------------------------------------------------- #
print("\n[3] Ventilated patient / ARDS / P-F ratio")

# Severe ARDS: PaO2 60, FiO2 80% -> P/F = 75
r = run(ph=7.30, pco2=48, hco3=23, po2=60, na=140, cl=104,
        clinical_context="ARDS", on_vent="yes",
        mode="PCV", rr=24, tv=400, peep=12, fio2=80,
        height_cm=170, sex="male")
check("ARDS: P/F ratio = 75", r["pf_ratio"] == 75.0)
check("ARDS: staged severe", "Severe ARDS" in r["context_interpretation"])
check("ARDS: priority IMMEDIATE", r["priority_level"] == "IMMEDIATE ICU ACTION")
check("ARDS: severity score 10", r["severity_score"] == 10)
check("ARDS: critical hypoxemia flag", "Critical Hypoxemia" in r["clinical_flags"])
check("ARDS: IBW computed", r["ibw_kg"] is not None)
check("ARDS: TV/kg computed", r["tv_per_kg"] is not None)
check("ARDS: prone position suggested", any("prone" in s.lower() for s in r["ventilator_suggestions"]))

# Lung-protective check: 170cm male IBW ~66kg, TV 400 -> ~6 mL/kg = protective
check("ARDS: lung-protective label present", r["lung_protective"] != "")

# Non-protective TV: TV 700 on same IBW -> ~10.6 mL/kg
r2 = run(ph=7.30, pco2=48, hco3=23, po2=60, na=140, cl=104,
         clinical_context="ARDS", on_vent="yes",
         mode="VCV", rr=20, tv=700, peep=10, fio2=60, height_cm=170, sex="male")
check("High TV flagged NOT lung-protective", r2["lung_protective"].startswith("NOT"))


# --------------------------------------------------------------------------- #
#  4. RSBI weaning
# --------------------------------------------------------------------------- #
print("\n[4] RSBI weaning index")

# RR 30, TV 300 mL -> RSBI = 30/0.3 = 100 (<105 favourable)
r = run(ph=7.40, pco2=40, hco3=24, po2=90, na=140, cl=104,
        on_vent="yes", mode="PSV", rr=30, tv=300, peep=5, fio2=40)
check("RSBI = 100", r["rsbi"] == 100.0)
check("RSBI favourable", "favourable" in r["rsbi_interpretation"])

# RR 35, TV 250 -> RSBI = 140 (>105 failure)
r = run(ph=7.40, pco2=40, hco3=24, po2=90, na=140, cl=104,
        on_vent="yes", mode="PSV", rr=35, tv=250, peep=5, fio2=40)
check("RSBI = 140 -> failure likely", r["rsbi"] == 140.0 and "failure" in r["rsbi_interpretation"])


# --------------------------------------------------------------------------- #
#  5. Validation / safety
# --------------------------------------------------------------------------- #
print("\n[5] Input validation & safety")

# Impossible pH -> invalid
r = run(ph=8.5, pco2=40, hco3=24, po2=95)
check("Impossible pH rejected", r["valid"] is False and "error" in r)

# FiO2 as fraction (0.5) auto-corrected with warning
r = run(ph=7.40, pco2=40, hco3=24, po2=90, na=140, cl=104,
        on_vent="yes", mode="VCV", rr=15, tv=450, peep=5, fio2=0.5)
check("FiO2 fraction auto-scaled to 50", r["valid"] and r["pf_ratio"] == 180.0)

# Henderson-Hasselbalch inconsistency warning
r = run(ph=7.60, pco2=60, hco3=15, po2=90)  # internally inconsistent
check("H-H inconsistency warned",
      any("inconsistency" in w.lower() for w in r.get("warnings", [])))

# Albumin correction: low albumin raises corrected AG
r = run(ph=7.30, pco2=34, hco3=16, po2=95, na=140, cl=110, albumin=2.0)
check("Albumin-corrected AG > raw AG", r["anion_gap_corrected"] > r["anion_gap"])

# Safety note always present
r = run(ph=7.40, pco2=40, hco3=24, po2=95)
check("Safety note present", r["safety_note"] and r["safety_note_ar"])


# --------------------------------------------------------------------------- #
#  Summary
# --------------------------------------------------------------------------- #
print(f"\n{'='*50}")
print(f"  RESULTS:  {PASS} passed, {FAIL} failed")
print(f"{'='*50}")
sys.exit(1 if FAIL else 0)
