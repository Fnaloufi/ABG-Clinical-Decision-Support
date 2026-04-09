# ABG Clinical Decision Support Tool - V5 + V6
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
        "severity_score": 0,
        "priority_level": "",
        "clinical_flags": [],
        "safety_note": "This tool is for educational and clinical support purposes only. Clinical correlation and professional review are required."
    }

    # Normalize text inputs
    sample_type = sample_type.strip().upper()
    clinical_context = clinical_context.strip().upper()
    on_vent = on_vent.strip().lower()

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

        results["compensation"] = (
            f"Expected pCO2: {round(expected_pco2, 1)} "
            f"(range {round(low_range, 1)}-{round(high_range, 1)})"
        )

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
    # Use PaO2 interpretation only if NOT on ventilator
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
        if on_vent == "yes" and peep is not None and peep >= 5 and results["pf_ratio"] is not None:
            if results["pf_ratio"] < 100:
                results["context_interpretation"] = "Severe ARDS"
            elif results["pf_ratio"] < 200:
                results["context_interpretation"] = "Moderate ARDS"
            elif results["pf_ratio"] < 300:
                results["context_interpretation"] = "Mild ARDS"
            else:
                results["context_interpretation"] = "ARDS context provided, but P/F ratio does not support ARDS oxygenation threshold"
        else:
            results["context_interpretation"] = "ARDS context provided, but data are insufficient for simplified ARDS classification"

        if results["pf_ratio"] is not None and results["pf_ratio"] < 80:
            results["context_notes"].append("Critical hypoxemia - urgent escalation required")

    elif clinical_context == "COPD":
        results["context_interpretation"] = "COPD context"
        results["context_notes"].append("Prioritize pH and pCO2 interpretation")
        if (
            "Respiratory Acidosis" in results["primary_disorder"]
            or results["secondary_disorder"] == "Respiratory Acidosis"
        ):
            results["context_notes"].append("Hypercapnic ventilatory failure pattern present")
        results["context_notes"].append(
            "P/F ratio may describe oxygenation severity, but it does not by itself define COPD-specific decision making"
        )

    else:
        results["context_interpretation"] = "General clinical interpretation"

    # Step 8: Ventilator suggestion
    if on_vent == "yes":
        if results["secondary_disorder"]:
            results["ventilator_suggestions"].append(
                "Treat underlying cause first; avoid immediate ventilator changes"
            )

        elif clinical_context == "ARDS":
            results["ventilator_suggestions"].append(
                "Apply lung-protective ventilation strategy"
            )
            results["ventilator_suggestions"].append(
                "Increase PEEP and optimize FiO2 before increasing ventilation"
            )
            results["ventilator_suggestions"].append(
                "Use low tidal volume (4-6 ml/kg IBW)"
            )

            if results["pf_ratio"] is not None and results["pf_ratio"] < 100:
                results["ventilator_suggestions"].append(
                    "Consider prone positioning"
                )

            if results["pf_ratio"] is not None and results["pf_ratio"] < 80:
                results["ventilator_suggestions"].append(
                    "Consider ECMO referral if refractory hypoxemia"
                )

        elif clinical_context == "COPD":
            results["ventilator_suggestions"].append(
                "Avoid aggressive ventilation increase (risk of air trapping)"
            )

        elif "Respiratory Acidosis" in results["primary_disorder"]:
            results["ventilator_suggestions"].append(
                "Increase minute ventilation (increase RR first)"
            )

        elif "Respiratory Alkalosis" in results["primary_disorder"]:
            results["ventilator_suggestions"].append(
                "Decrease minute ventilation (decrease RR first)"
            )

        elif results["primary_disorder"] == "Metabolic Acidosis":
            results["ventilator_suggestions"].append(
                "Ensure adequate ventilation and address the underlying metabolic cause"
            )

        elif results["primary_disorder"] == "Metabolic Alkalosis":
            results["ventilator_suggestions"].append(
                "Consider reducing ventilation cautiously if clinically indicated"
            )

    # Step 9: Risk flag
    if results["pf_ratio"] is not None and results["pf_ratio"] < 80:
        results["risk_flag"] = "Critical - life-threatening hypoxemia"

    elif ph < 7.20:
        results["risk_flag"] = "High - severe acidemia"

    elif ph > 7.55:
        results["risk_flag"] = "High - severe alkalemia"

    elif sample_type == "ABG" and po2 < 60:
        results["risk_flag"] = "High - severe hypoxemia"

    elif "mixed" in results["primary_disorder"].lower() or results["secondary_disorder"]:
        results["risk_flag"] = "Moderate to High - possible mixed disorder"

    elif on_vent == "yes":
        results["risk_flag"] = "Moderate - ventilated patient requires close monitoring"

    else:
        results["risk_flag"] = "Moderate/Low - clinical correlation required"

    # Step 10: Severity Score
    if results["pf_ratio"] is not None:
        if results["pf_ratio"] < 100:
            results["severity_score"] = 10
        elif results["pf_ratio"] < 200:
            results["severity_score"] = 8
        elif results["pf_ratio"] < 300:
            results["severity_score"] = 5
        else:
            results["severity_score"] = 2
    else:
        if ph < 7.20 or ph > 7.55:
            results["severity_score"] = 7
        elif ph < 7.30 or ph > 7.50:
            results["severity_score"] = 5
        else:
            results["severity_score"] = 2

    # Step 11: Priority Level
    if results["severity_score"] >= 9:
        results["priority_level"] = "IMMEDIATE ICU ACTION"
    elif results["severity_score"] >= 7:
        results["priority_level"] = "URGENT REVIEW"
    elif results["severity_score"] >= 4:
        results["priority_level"] = "MODERATE"
    else:
        results["priority_level"] = "STABLE"

    # Step 12: Clinical Flags
    if clinical_context == "ARDS":
        results["clinical_flags"].append("ARDS")

    if results["pf_ratio"] is not None and results["pf_ratio"] < 100:
        results["clinical_flags"].append("Critical Hypoxemia")

    if on_vent == "yes":
        results["clinical_flags"].append("Ventilated Patient")

    return results


def print_results(results):
    print("\n--- BLOOD GAS RESULT ---")
    print("Acid-base status:", results["acid_base_status"])
    print("Primary disorder:", results["primary_disorder"])

    if results["compensation"]:
        print("Compensation:", results["compensation"])

    if results["secondary_disorder"]:
        print("Secondary disorder:", results["secondary_disorder"])

    print("Final interpretation:", results["final_interpretation"])

    print("\n--- OXYGENATION ANALYSIS ---")
    if results["pf_ratio"] is not None:
        print("P/F Ratio:", results["pf_ratio"])
    print("Oxygenation status:", results["oxygenation_status"])

    print("\n--- CONTEXT ---")
    print(results["context_interpretation"])
    for note in results["context_notes"]:
        print("Note:", note)

    print("\n--- SUGGESTIONS ---")
    if results["ventilator_suggestions"]:
        for suggestion in results["ventilator_suggestions"]:
            print("-", suggestion)
    else:
        print("- No ventilator suggestion generated")

    print("\nRisk:", results["risk_flag"])
    print("Severity Score:", results["severity_score"])
    print("Priority Level:", results["priority_level"])

    if results["clinical_flags"]:
        print("Clinical Flags:", ", ".join(results["clinical_flags"]))

    print("\n--- JSON ---")
    print(json.dumps(results, indent=4))


# RUN SECTION
sample_type = input("Enter sample type (ABG/VBG/CBG): ").strip().upper()
clinical_context = input("Enter clinical context (ARDS/COPD/OTHER): ").strip().upper()

ph = float(input("Enter pH: ").strip())
pco2 = float(input("Enter PCO2 (mmHg): ").strip())
hco3 = float(input("Enter HCO3 (mEq/L): ").strip())
po2 = float(input("Enter pO2 (mmHg): ").strip())

on_vent = input("Is the patient on mechanical ventilation? (yes/no): ").strip().lower()

mode = ""
rr = ""
tv = ""
peep = None
fio2 = None

if on_vent == "yes":
    mode = input("Enter ventilator mode: ").strip()
    rr = input("Enter respiratory rate (RR): ").strip()
    tv = input("Enter tidal volume (TV): ").strip()
    peep = float(input("Enter PEEP: ").strip())
    fio2 = float(input("Enter FiO2 (%): ").strip())

results = analyze_abg(
    sample_type=sample_type,
    clinical_context=clinical_context,
    ph=ph,
    pco2=pco2,
    hco3=hco3,
    po2=po2,
    on_vent=on_vent,
    mode=mode,
    rr=rr,
    tv=tv,
    peep=peep,
    fio2=fio2
)
print_results(results)