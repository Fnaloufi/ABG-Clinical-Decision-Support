# ABG Clinical Decision Support Tool – V5
# Product Layer v1
# For educational and clinical support use only

import json


def analyze_abg(
    sample_type,
    clinical_context,
    ph,
    pco2,
    hco3,
    po2,
    on_vent,
    mode="",
    rr="",
    tv="",
    peep=None,
    fio2=None
):
    results = {
        "acid_base_status": "",
        "primary_disorder": "",
        "compensation": "",
        "secondary_disorder": "",
        "final_interpretation": "",
        "oxygenation_note": "",
        "pf_ratio": None,
        "oxygenation_status": "",
        "ventilator_status": "",
        "ventilator_settings": {},
        "context_interpretation": "",
        "context_notes": [],
        "ventilator_suggestions": [],
        "risk_flag": "",
        "safety_note": "This tool is for educational and clinical support purposes only. Clinical correlation and professional review are required."
    }

    # Step 1: Acid-base status
    if ph < 7.35:
        results["acid_base_status"] = "Acidosis"
    elif ph > 7.45:
        results["acid_base_status"] = "Alkalosis"
    else:
        results["acid_base_status"] = "Near normal / compensated"

    # Step 2: Primary disorder
    if ph < 7.35:
        if pco2 > 45 and hco3 < 22:
            results["primary_disorder"] = "Mixed Acidosis (Respiratory + Metabolic)"
        elif pco2 > 45:
            results["primary_disorder"] = "Respiratory Acidosis"
        elif hco3 < 22:
            results["primary_disorder"] = "Metabolic Acidosis"
        else:
            results["primary_disorder"] = "Mixed or unclear"

    elif ph > 7.45:
        if pco2 < 35 and hco3 > 26:
            results["primary_disorder"] = "Mixed Alkalosis (Respiratory + Metabolic)"
        elif pco2 < 35:
            results["primary_disorder"] = "Respiratory Alkalosis"
        elif hco3 > 26:
            results["primary_disorder"] = "Metabolic Alkalosis"
        else:
            results["primary_disorder"] = "Mixed or unclear"

    else:
        results["primary_disorder"] = "Possible compensation or mixed disorder"

    # Step 3: Compensation
    if results["primary_disorder"] == "Metabolic Acidosis":
        expected_pco2 = (1.5 * hco3) + 8
        low_range = expected_pco2 - 2
        high_range = expected_pco2 + 2

        results["compensation"] = f"Expected pCO2: {round(expected_pco2, 1)} (range {round(low_range, 1)}-{round(high_range, 1)})"

        if pco2 < low_range:
            results["secondary_disorder"] = "Respiratory Alkalosis"
            results["final_interpretation"] = "Metabolic Acidosis + Respiratory Alkalosis"
        elif pco2 > high_range:
            results["secondary_disorder"] = "Respiratory Acidosis"
            results["final_interpretation"] = "Metabolic Acidosis + Respiratory Acidosis"
        else:
            results["final_interpretation"] = "Metabolic Acidosis with appropriate compensation"

    elif results["primary_disorder"] == "Respiratory Acidosis":
        if hco3 > 26:
            results["compensation"] = "Metabolic compensation present"
            results["final_interpretation"] = "Respiratory Acidosis (compensated)"
        else:
            results["compensation"] = "Uncompensated"
            results["final_interpretation"] = "Respiratory Acidosis"

    elif results["primary_disorder"] == "Respiratory Alkalosis":
        if hco3 < 22:
            results["compensation"] = "Metabolic compensation present"
            results["final_interpretation"] = "Respiratory Alkalosis (compensated)"
        else:
            results["compensation"] = "Uncompensated"
            results["final_interpretation"] = "Respiratory Alkalosis"

    elif results["primary_disorder"] == "Metabolic Alkalosis":
        results["compensation"] = "Evaluate clinically"
        results["final_interpretation"] = "Metabolic Alkalosis"

    else:
        results["final_interpretation"] = results["primary_disorder"]

    # Step 4: Oxygenation note
    if on_vent != "yes":
        if sample_type == "ABG":
            if po2 < 60:
                results["oxygenation_note"] = "Severe hypoxemia"
            elif po2 < 80:
                results["oxygenation_note"] = "Mild to moderate hypoxemia"
            elif po2 <= 100:
                results["oxygenation_note"] = "PaO2 within normal range"
            else:
                results["oxygenation_note"] = "PaO2 above normal range"

        elif sample_type == "VBG":
            results["oxygenation_note"] = "Oxygenation cannot be reliably assessed from VBG"

        elif sample_type == "CBG":
            results["oxygenation_note"] = "Oxygenation assessment from CBG is limited"

        else:
            results["oxygenation_note"] = "Unknown sample type"

    # Step 5: P/F ratio
    if on_vent == "yes" and fio2 is not None and fio2 > 0:
        pf_ratio = po2 / (fio2 / 100)
        results["pf_ratio"] = round(pf_ratio, 1)

        if pf_ratio >= 300:
            results["oxygenation_status"] = "No significant impairment"
        elif 200 <= pf_ratio < 300:
            results["oxygenation_status"] = "Mild oxygenation impairment"
        elif 100 <= pf_ratio < 200:
            results["oxygenation_status"] = "Moderate oxygenation impairment"
        else:
            results["oxygenation_status"] = "Severe oxygenation impairment"
    else:
        results["oxygenation_status"] = results["oxygenation_note"]

    # Step 6: Ventilator settings
    if on_vent == "yes":
        results["ventilator_status"] = "On mechanical ventilation"
        results["ventilator_settings"] = {
            "Mode": mode,
            "RR": rr,
            "TV": tv,
            "PEEP": peep,
            "FiO2": fio2
        }
    else:
        results["ventilator_status"] = "Not on mechanical ventilation"

    # Step 7: Clinical context
    if clinical_context == "ARDS":
        if results["pf_ratio"] is not None:
            if results["pf_ratio"] < 100:
                results["context_interpretation"] = "Severe ARDS"
            elif results["pf_ratio"] < 200:
                results["context_interpretation"] = "Moderate ARDS"
            elif results["pf_ratio"] < 300:
                results["context_interpretation"] = "Mild ARDS"

        if results["pf_ratio"] is not None and results["pf_ratio"] < 80:
            results["context_notes"].append("Critical hypoxemia - urgent escalation required")

    elif clinical_context == "COPD":
        results["context_interpretation"] = "COPD context"
        results["context_notes"].append("Prioritize CO2 and ventilation")

    else:
        results["context_interpretation"] = "General clinical interpretation"

    # Step 8: Ventilator suggestion
    if on_vent == "yes":

        if clinical_context == "ARDS":
            results["ventilator_suggestions"].append("Apply lung-protective ventilation strategy")
            results["ventilator_suggestions"].append("Increase PEEP and optimize FiO2 before increasing ventilation")
            results["ventilator_suggestions"].append("Use low tidal volume (4–6 ml/kg IBW)")

            if results["pf_ratio"] is not None and results["pf_ratio"] < 100:
                results["ventilator_suggestions"].append("Consider prone positioning")

            if results["pf_ratio"] is not None and results["pf_ratio"] < 80:
                results["ventilator_suggestions"].append("Consider ECMO referral if refractory hypoxemia")

        elif clinical_context == "COPD":
            results["ventilator_suggestions"].append("Avoid aggressive ventilation increase (risk of air trapping)")

        elif "Respiratory Acidosis" in results["primary_disorder"]:
            results["ventilator_suggestions"].append("Increase minute ventilation (increase RR first)")

    # Step 9: Risk flag (UPDATED 🔥)
    if ph < 7.20:
        results["risk_flag"] = "High - severe acidemia"

    elif ph > 7.55:
        results["risk_flag"] = "High - severe alkalemia"

    elif results["pf_ratio"] is not None and results["pf_ratio"] < 80:
        results["risk_flag"] = "Critical - life-threatening hypoxemia"

    elif sample_type == "ABG" and po2 < 60:
        results["risk_flag"] = "High - severe hypoxemia"

    elif "mixed" in results["primary_disorder"].lower() or results["secondary_disorder"]:
        results["risk_flag"] = "Moderate to High - possible mixed disorder"

    elif on_vent == "yes":
        results["risk_flag"] = "Moderate - ventilated patient requires close monitoring"

    else:
        results["risk_flag"] = "Moderate/Low - clinical correlation required"

    return results


def print_results(results):
    print("\n--- BLOOD GAS RESULT ---")
    print("Acid-base status:", results["acid_base_status"])
    print("Primary disorder:", results["primary_disorder"])
    print("Final interpretation:", results["final_interpretation"])

    print("\n--- OXYGENATION ANALYSIS ---")
    print("P/F Ratio:", results["pf_ratio"])
    print("Oxygenation status:", results["oxygenation_status"])

    print("\n--- CONTEXT ---")
    print(results["context_interpretation"])
    for note in results["context_notes"]:
        print("Note:", note)

    print("\n--- SUGGESTIONS ---")
    for s in results["ventilator_suggestions"]:
        print("-", s)

    print("\nRisk:", results["risk_flag"])

    print("\n--- JSON ---")
    print(json.dumps(results, indent=4))


# RUN
sample_type = input("Enter sample type: ").strip().upper()
clinical_context = input("Enter clinical context: ").strip().upper()

ph = float(input("Enter pH: "))
pco2 = float(input("Enter PCO2: "))
hco3 = float(input("Enter HCO3: "))
po2 = float(input("Enter pO2: "))

on_vent = input("On ventilator? (yes/no): ").strip().lower()

mode = rr = tv = ""
peep = fio2 = None

if on_vent == "yes":
    mode = input("Mode: ")
    rr = input("RR: ")
    tv = input("TV: ")
    peep = float(input("PEEP: "))
    fio2 = float(input("FiO2: "))

results = analyze_abg(sample_type, clinical_context, ph, pco2, hco3, po2, on_vent, mode, rr, tv, peep, fio2)
print_results(results)