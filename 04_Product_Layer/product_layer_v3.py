# ABG Clinical Decision Support Tool - Refined V8
# Product Layer
# For educational and clinical support use only

import json


def detect_compensation_failure(primary_disorder, pco2, hco3):
    result = {
        "compensation_status": "Appropriate",
        "compensation_warning": None
    }

    if primary_disorder == "Metabolic Acidosis":
        expected_pco2 = (1.5 * hco3) + 8
        low_range = expected_pco2 - 2
        high_range = expected_pco2 + 2

        if pco2 > high_range:
            result["compensation_status"] = "Inadequate"
            result["compensation_warning"] = "Failed Respiratory Compensation"
        elif pco2 < low_range:
            result["compensation_status"] = "Excessive"
            result["compensation_warning"] = "Possible Respiratory Alkalosis"

    return result


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
        "action_plan": [],
        "protocol_engine": {
            "protocol_name": "",
            "protocol_reason": "",
            "protocol_steps": []
        },
        "compensation_engine": {
            "compensation_status": "",
            "compensation_warning": ""
        },
        "safety_note": "This tool is for educational and clinical support purposes only. Clinical correlation and professional review are required."
    }

    # Normalize inputs
    sample_type = sample_type.strip().upper()
    clinical_context = clinical_context.strip().upper()
    on_vent = on_vent.strip().lower()

    # -----------------------------
    # Step 1: Acid-base status
    # -----------------------------
    if ph < 7.35:
        results["acid_base_status"] = "Acidosis"
    elif ph > 7.45:
        results["acid_base_status"] = "Alkalosis"
    else:
        results["acid_base_status"] = "Near normal / compensated"

    # -----------------------------
    # Step 2: Primary disorder
    # -----------------------------
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

    # -----------------------------
    # Step 3: Compensation / final interpretation
    # -----------------------------
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

    # -----------------------------
    # Step 4: Compensation conflict engine
    # -----------------------------
    comp_check = detect_compensation_failure(
        results["primary_disorder"],
        pco2,
        hco3
    )
    results["compensation_engine"]["compensation_status"] = comp_check["compensation_status"]
    results["compensation_engine"]["compensation_warning"] = comp_check["compensation_warning"] or ""

    # -----------------------------
    # Step 5: Oxygenation assessment
    # -----------------------------
    if on_vent != "yes":
        if sample_type == "ABG":
            if po2 < 60:
                results["oxygenation_note"] = "Severe hypoxemia"
                results["oxygenation_status"] = "Severe hypoxemia"
            elif po2 < 80:
                results["oxygenation_note"] = "Mild to moderate hypoxemia"
                results["oxygenation_status"] = "Mild to moderate hypoxemia"
            else:
                results["oxygenation_note"] = "Normal oxygenation"
                results["oxygenation_status"] = "Normal oxygenation"
        elif sample_type == "VBG":
            results["oxygenation_note"] = "Oxygenation cannot be reliably assessed from VBG"
            results["oxygenation_status"] = "Oxygenation assessment limited"
        elif sample_type == "CBG":
            results["oxygenation_note"] = "Oxygenation assessment from CBG is limited"
            results["oxygenation_status"] = "Oxygenation assessment limited"
        else:
            results["oxygenation_note"] = "Unknown sample type"
            results["oxygenation_status"] = "Unknown oxygenation status"

    # -----------------------------
    # Step 6: P/F ratio
    # -----------------------------
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

    # -----------------------------
    # Step 7: Ventilator status/settings
    # -----------------------------
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

    # -----------------------------
    # Step 8: Clinical context
    # -----------------------------
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
        results["context_notes"].append("Interpretation based on acid-base physiology")
        results["context_notes"].append("Clinical correlation required")

    # -----------------------------
    # Step 9: Ventilator suggestions
    # -----------------------------
    if on_vent == "yes":
        if results["secondary_disorder"]:
            results["ventilator_suggestions"].append(
                "Treat underlying cause first; avoid immediate ventilator changes"
            )

        elif clinical_context == "ARDS":
            results["ventilator_suggestions"].append("Apply lung-protective ventilation strategy")
            results["ventilator_suggestions"].append("Increase PEEP and optimize FiO2 before increasing ventilation")
            results["ventilator_suggestions"].append("Use low tidal volume (4-6 ml/kg IBW)")
            results["ventilator_suggestions"].append("Ensure plateau pressure < 30 cmH2O")

            if results["pf_ratio"] is not None and results["pf_ratio"] < 100:
                results["ventilator_suggestions"].append("Consider prone positioning")

            if (
                results["pf_ratio"] is not None
                and results["pf_ratio"] < 80
                and fio2 is not None
                and fio2 > 80
                and peep is not None
                and peep >= 10
            ):
                results["ventilator_suggestions"].append("Strong consideration for ECMO referral")

        elif clinical_context == "COPD":
            results["ventilator_suggestions"].append("Avoid aggressive ventilation increase (risk of air trapping)")

        elif "Respiratory Acidosis" in results["primary_disorder"]:
            results["ventilator_suggestions"].append("Increase minute ventilation (increase RR first)")

        elif "Respiratory Alkalosis" in results["primary_disorder"]:
            results["ventilator_suggestions"].append("Decrease minute ventilation (decrease RR first)")

        elif results["primary_disorder"] == "Metabolic Acidosis":
            results["ventilator_suggestions"].append(
                "Ensure adequate ventilation and address the underlying metabolic cause"
            )

    # -----------------------------
    # Step 10: Severity score
    # -----------------------------
    acid_score = 0
    oxygen_score = 0

    # Acidemia / alkalemia weighting
    if ph < 7.10 or ph > 7.60:
        acid_score = 10
    elif ph < 7.20 or ph > 7.55:
        acid_score = 8
    elif ph < 7.30 or ph > 7.50:
        acid_score = 5
    elif ph < 7.35 or ph > 7.45:
        acid_score = 2

    # Oxygenation weighting
    if results["pf_ratio"] is not None:
        if results["pf_ratio"] < 80:
            oxygen_score = 10
        elif results["pf_ratio"] < 100:
            oxygen_score = 9
        elif results["pf_ratio"] < 200:
            oxygen_score = 7
        elif results["pf_ratio"] < 300:
            oxygen_score = 5
        else:
            oxygen_score = 2
    else:
        if sample_type == "ABG":
            if po2 < 60:
                oxygen_score = 7
            elif po2 < 80:
                oxygen_score = 4
            else:
                oxygen_score = 1

    results["severity_score"] = max(acid_score, oxygen_score)

    # Raise severity for mixed / conflict / ventilatory failure features
    if "Mixed" in results["primary_disorder"] or results["secondary_disorder"]:
        results["severity_score"] += 1

    if comp_check["compensation_warning"] == "Failed Respiratory Compensation":
        results["severity_score"] += 1

    if on_vent == "yes" and "Respiratory Acidosis" in results["primary_disorder"]:
        results["severity_score"] += 1

    if results["severity_score"] > 10:
        results["severity_score"] = 10

    # -----------------------------
    # Step 11: Risk flag
    # -----------------------------
    if results["severity_score"] >= 9:
        results["risk_flag"] = "Critical"
    elif results["severity_score"] >= 7:
        results["risk_flag"] = "High"
    elif results["severity_score"] >= 5:
        results["risk_flag"] = "Moderate"
    else:
        results["risk_flag"] = "Low"

    if results["pf_ratio"] is not None and results["pf_ratio"] < 80:
        results["risk_flag"] = "Critical - life-threatening hypoxemia"
    elif ph < 7.10:
        results["risk_flag"] = "Critical - life-threatening acidemia"
    elif ph < 7.20:
        results["risk_flag"] = "High - severe acidemia"
    elif ph > 7.60:
        results["risk_flag"] = "Critical - life-threatening alkalemia"
    elif ph > 7.55:
        results["risk_flag"] = "High - severe alkalemia"

    # -----------------------------
    # Step 12: Priority level
    # -----------------------------
    if results["severity_score"] >= 9:
        results["priority_level"] = "IMMEDIATE ICU ACTION"
    elif results["severity_score"] >= 7:
        results["priority_level"] = "URGENT REVIEW"
    elif results["severity_score"] >= 5:
        results["priority_level"] = "MODERATE"
    else:
        results["priority_level"] = "STABLE"

    # -----------------------------
    # Step 13: Clinical flags
    # -----------------------------
    if clinical_context == "ARDS":
        if results["pf_ratio"] is not None and results["pf_ratio"] < 100:
            results["clinical_flags"].append("Severe ARDS")
        else:
            results["clinical_flags"].append("ARDS")

    elif clinical_context == "COPD":
        results["clinical_flags"].append("COPD")

    if "Metabolic Acidosis" in results["primary_disorder"] or "Metabolic Acidosis" in results["final_interpretation"]:
        results["clinical_flags"].append("Metabolic Acidosis")

    if "Respiratory Acidosis" in results["primary_disorder"] or results["secondary_disorder"] == "Respiratory Acidosis":
        results["clinical_flags"].append("Respiratory Acidosis")

    if pco2 > 45:
        results["clinical_flags"].append("Hypercapnia")

    if "Mixed" in results["primary_disorder"] or results["secondary_disorder"]:
        results["clinical_flags"].append("Mixed Disorder")

    if comp_check["compensation_warning"] == "Failed Respiratory Compensation":
        results["clinical_flags"].append("Failed Respiratory Compensation")

    if ph < 7.10:
        results["clinical_flags"].append("Severe Acidemia")
    elif ph < 7.20:
        results["clinical_flags"].append("Acidemia")

    if results["pf_ratio"] is not None and results["pf_ratio"] < 100:
        if fio2 is not None and fio2 >= 80:
            results["clinical_flags"].append("Refractory Hypoxemia")
        results["clinical_flags"].append("Critical Hypoxemia")

    if on_vent == "yes":
        results["clinical_flags"].append("Ventilated Patient")

    results["clinical_flags"] = list(dict.fromkeys(results["clinical_flags"]))

    # -----------------------------
    # Step 14: Action plan
    # -----------------------------
    if clinical_context == "ARDS":
        # Priority order: oxygenation -> lung protection -> ventilation
        if results["priority_level"] == "IMMEDIATE ICU ACTION":
            results["action_plan"].append("Optimize FiO2 to target SpO2 88-95%")
            results["action_plan"].append("Increase PEEP (stepwise strategy)")
            results["action_plan"].append("Apply lung-protective ventilation (4-6 ml/kg IBW)")
            results["action_plan"].append("Ensure plateau pressure < 30 cmH2O")
            results["action_plan"].append("Consider prone positioning")

            if (
                results["pf_ratio"] is not None
                and results["pf_ratio"] < 80
                and fio2 is not None
                and fio2 > 80
                and peep is not None
                and peep >= 10
            ):
                results["action_plan"].append("Strong consideration for ECMO referral")
            else:
                results["action_plan"].append("Evaluate for ECMO referral if refractory hypoxemia")

        # Ventilation adjustment only if severe acidemia
        if "Respiratory Acidosis" in results["primary_disorder"] and ph < 7.20:
            results["action_plan"].append("Consider increasing RR carefully for severe acidemia")

        if "Respiratory Acidosis" in results["primary_disorder"]:
            results["action_plan"].append("Balance ventilation goals against lung-protective strategy")

    elif clinical_context == "COPD":
        results["action_plan"].append("Avoid aggressive ventilation increase due to risk of air trapping")

        if "Respiratory Acidosis" in results["primary_disorder"]:
            results["action_plan"].append("Increase minute ventilation (increase RR carefully)")
            results["action_plan"].append("Allow adequate expiratory time to avoid auto-PEEP")

        results["action_plan"].append("Review ventilator settings and reassess blood gas")
        results["action_plan"].append("Continue close clinical monitoring")

    else:
        if results["severity_score"] >= 9:
            results["action_plan"].append("Urgently identify the underlying cause")
            results["action_plan"].append("Arrange immediate senior/ICU review")
            results["action_plan"].append("Repeat ABG urgently after intervention")
        elif results["severity_score"] >= 7:
            results["action_plan"].append("Urgently identify the underlying cause")
            results["action_plan"].append("Repeat ABG soon after intervention")
        else:
            results["action_plan"].append("Correlate clinically and reassess ABG")

        if "Metabolic Acidosis" in results["primary_disorder"] or "Metabolic Acidosis" in results["final_interpretation"]:
            results["action_plan"].append("Investigate the cause of metabolic acidosis")
            results["action_plan"].append("Check lactate if indicated")
            results["action_plan"].append("Check ketones if DKA is suspected")
            results["action_plan"].append("Review renal function")
            results["action_plan"].append("Consider sepsis workup if clinically indicated")

        if "Respiratory Acidosis" in results["primary_disorder"] or results["secondary_disorder"] == "Respiratory Acidosis":
            results["action_plan"].append("Assess for hypoventilation and consider ventilatory support if clinically indicated")

        if comp_check["compensation_warning"] == "Failed Respiratory Compensation":
            results["action_plan"].append("Compensation failure detected - reassess ventilation and underlying cause")

        if ph < 7.25 and results["secondary_disorder"] == "Respiratory Acidosis":
            results["action_plan"].append("High risk of ventilatory failure - assess need for ventilatory support")

        if ph < 7.10:
            results["action_plan"].append("Consider ICU-level monitoring due to severe acidemia")

    results["action_plan"] = list(dict.fromkeys(results["action_plan"]))

    # -----------------------------
    # Step 15: Protocol engine
    # -----------------------------
    protocol_name = ""
    protocol_reason = ""
    protocol_steps = []

    if clinical_context == "ARDS" and results["pf_ratio"] is not None and results["pf_ratio"] < 100:
        protocol_name = "Severe ARDS Rescue Protocol"
        protocol_reason = "P/F ratio below 100 with ARDS context"
        protocol_steps = [
            "Use lung-protective ventilation",
            "Optimize FiO2 and PEEP",
            "Ensure plateau pressure remains below 30 cmH2O",
            "Consider prone positioning early"
        ]

        if (
            results["pf_ratio"] < 80
            and fio2 is not None
            and fio2 > 80
            and peep is not None
            and peep >= 10
        ):
            protocol_steps.append("Strongly escalate for ECMO evaluation")
        else:
            protocol_steps.append("Escalate for ECMO evaluation if refractory hypoxemia")

    elif clinical_context == "COPD" and "Respiratory Acidosis" in results["primary_disorder"]:
        protocol_name = "COPD Hypercapnic Ventilation Protocol"
        protocol_reason = "COPD context with hypercapnic respiratory acidosis"
        protocol_steps = [
            "Avoid aggressive ventilation increase",
            "Prefer careful RR adjustment over large tidal volume changes",
            "Allow adequate expiratory time",
            "Monitor for dynamic hyperinflation / air trapping",
            "Repeat blood gas after ventilator adjustment"
        ]

    elif (
        "Metabolic Acidosis" in results["primary_disorder"]
        and results["secondary_disorder"] == "Respiratory Acidosis"
    ):
        protocol_name = "Mixed Acidosis Escalation Protocol"
        protocol_reason = "Metabolic acidosis with superimposed respiratory acidosis"
        protocol_steps = [
            "Urgently identify the underlying cause",
            "Assess for ventilatory failure",
            "Arrange close monitoring / higher level of care",
            "Repeat ABG urgently after intervention"
        ]

    elif results["primary_disorder"] == "Metabolic Acidosis" and results["severity_score"] >= 7:
        protocol_name = "Severe Metabolic Acidosis Protocol"
        protocol_reason = "Severe acidemia with metabolic acidosis pattern"
        protocol_steps = [
            "Investigate the cause immediately",
            "Assess hemodynamics and tissue perfusion",
            "Consider ICU-level monitoring",
            "Repeat ABG and relevant labs urgently"
        ]

    else:
        protocol_name = "General ABG Reassessment Protocol"
        protocol_reason = "No disease-specific protocol triggered"
        protocol_steps = [
            "Correlate clinically",
            "Review trend and repeat ABG if needed",
            "Adjust management according to underlying cause"
        ]

    results["protocol_engine"]["protocol_name"] = protocol_name
    results["protocol_engine"]["protocol_reason"] = protocol_reason
    results["protocol_engine"]["protocol_steps"] = protocol_steps

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

    if results["compensation_engine"]["compensation_status"]:
        print("Compensation Status:", results["compensation_engine"]["compensation_status"])
    if results["compensation_engine"]["compensation_warning"]:
        print("Compensation Warning:", results["compensation_engine"]["compensation_warning"])

    print("\n--- ACTION PLAN ---")
    if results["action_plan"]:
        for action in results["action_plan"]:
            print("-", action)
    else:
        print("- No action plan generated")

    print("\n--- PROTOCOL ENGINE ---")
    print("Protocol:", results["protocol_engine"]["protocol_name"])
    print("Reason:", results["protocol_engine"]["protocol_reason"])
    for step in results["protocol_engine"]["protocol_steps"]:
        print("-", step)

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