# ABG Clinical Decision Support Tool – V4
# For educational and clinical support use only

# -----------------------------
# INPUT SECTION
# -----------------------------

sample_type = input("Enter sample type (ABG/VBG/CBG): ").strip().upper()
clinical_context = input("Enter clinical context (ARDS/COPD/OTHER): ").strip().upper()

ph = float(input("Enter pH: "))
pco2 = float(input("Enter PCO2 (mmHg): "))
hco3 = float(input("Enter HCO3 (mEq/L): "))
po2 = float(input("Enter pO2 (mmHg): "))

on_vent = input("Is the patient on mechanical ventilation? (yes/no): ").strip().lower()

if on_vent == "yes":
    mode = input("Enter ventilator mode: ")
    rr = input("Enter respiratory rate (RR): ")
    tv = input("Enter tidal volume (TV): ")
    peep = input("Enter PEEP: ")
    fio2 = float(input("Enter FiO2 (%): "))


# -----------------------------
# STEP 1: Acid-Base Status
# -----------------------------

print("\n--- Blood Gas Result ---")

if ph < 7.35:
    print("Acid-base status: Acidosis")
elif ph > 7.45:
    print("Acid-base status: Alkalosis")
else:
    print("Acid-base status: Near normal / compensated")


# -----------------------------
# STEP 2: Primary Disorder
# -----------------------------

primary_disorder = ""

if ph < 7.35:
    if pco2 > 45:
        primary_disorder = "Respiratory Acidosis"
    elif hco3 < 22:
        primary_disorder = "Metabolic Acidosis"

elif ph > 7.45:
    if pco2 < 35:
        primary_disorder = "Respiratory Alkalosis"
    elif hco3 > 26:
        primary_disorder = "Metabolic Alkalosis"

print("Primary disorder:", primary_disorder)


# -----------------------------
# STEP 3: Compensation Check
# -----------------------------

secondary_disorder = False

if primary_disorder == "Metabolic Acidosis":
    expected_pco2 = (1.5 * hco3) + 8
    print(f"Expected pCO2: {round(expected_pco2,1)}")

    if pco2 > expected_pco2 + 2:
        print("Compensation: Inadequate (Respiratory Acidosis)")
        secondary_disorder = True
    elif pco2 < expected_pco2 - 2:
        print("Compensation: Excess (Respiratory Alkalosis)")
        secondary_disorder = True
    else:
        print("Compensation: Appropriate")

elif primary_disorder == "Respiratory Acidosis":
    if hco3 > 26:
        print("Compensation: Metabolic compensation present")
    else:
        print("Compensation: Uncompensated")

elif primary_disorder == "Respiratory Alkalosis":
    if hco3 < 22:
        print("Compensation: Metabolic compensation present")
    else:
        print("Compensation: Uncompensated")

elif primary_disorder == "Metabolic Alkalosis":
    print("Compensation: Evaluate clinically")

print("Final interpretation:", primary_disorder)


# -----------------------------
# STEP 4: Oxygenation (PaO2)
# -----------------------------

if sample_type == "ABG":
    if po2 < 60:
        oxygenation_note = "Severe hypoxemia"
    elif po2 < 80:
        oxygenation_note = "Mild to moderate hypoxemia"
    elif po2 <= 100:
        oxygenation_note = "PaO2 within normal range"
    else:
        oxygenation_note = "PaO2 above normal range"

elif sample_type == "VBG":
    oxygenation_note = "Oxygenation cannot be reliably assessed from VBG"

elif sample_type == "CBG":
    oxygenation_note = "Limited oxygenation assessment from CBG"

else:
    oxygenation_note = "Unknown sample type"

# 🔥 FIX: Avoid conflict with P/F
if on_vent == "yes":
    print("Oxygenation: Based on P/F ratio (see below)")
else:
    print("Oxygenation:", oxygenation_note)


# -----------------------------
# STEP 5: P/F Ratio (ONLY if ventilated)
# -----------------------------

if on_vent == "yes":
    pf_ratio = po2 / (fio2 / 100)

    print("\n--- Oxygenation Analysis ---")
    print("P/F Ratio:", round(pf_ratio, 1))

    if pf_ratio >= 300:
        print("Oxygenation status: No significant impairment")
    elif 200 <= pf_ratio < 300:
        print("Oxygenation status: Mild oxygenation impairment")
    elif 100 <= pf_ratio < 200:
        print("Oxygenation status: Moderate oxygenation impairment")
    else:
        print("Oxygenation status: Severe oxygenation impairment")


# -----------------------------
# STEP 6: Ventilator Settings Display
# -----------------------------

if on_vent == "yes":
    print("Ventilator status: On mechanical ventilation")
    print("Current ventilator settings:")
    print("Mode:", mode)
    print("RR:", rr)
    print("TV:", tv)
    print("PEEP:", peep)
    print("FiO2:", fio2)
else:
    print("Ventilator status: Not on mechanical ventilation")


# -----------------------------
# STEP 7: Clinical Context Logic
# -----------------------------

print("\n--- Clinical Context Logic ---")

if clinical_context == "COPD":
    print("Context: COPD")
    print("Note: Hypercapnia-driven pathology")
    print("Focus: pH and pCO2 interpretation prioritized")

elif clinical_context == "ARDS":
    if on_vent == "yes":
        if pf_ratio < 100:
            print("Context: Severe ARDS")
        elif pf_ratio < 200:
            print("Context: Moderate ARDS")
        elif pf_ratio < 300:
            print("Context: Mild ARDS")
        else:
            print("Context: No ARDS criteria")
    else:
        print("Context: ARDS suspected - need ventilated patient for P/F classification")

else:
    print("Context: General clinical interpretation")


# -----------------------------
# STEP 8: Ventilator Suggestion
# -----------------------------

if on_vent == "yes":
    print("\n--- Ventilator Suggestion ---")

    if secondary_disorder:
        print("Suggestion: Mixed disorder - treat underlying cause first")
        print("Risk flag: Moderate to High")

    else:
        if clinical_context == "COPD":
            print("COPD note: Avoid aggressive ventilation increase (risk of air trapping)")
            print("Suggestion: Optimize ventilation cautiously (prefer RR over TV)")
            print("Risk flag: Moderate")

        elif clinical_context == "ARDS":
            print("ARDS note: Oxygenation failure is primary issue")
            print("Suggestion: Apply lung-protective ventilation")
            print("Suggestion: Increase PEEP and optimize FiO2 first")
            print("Suggestion: Use low tidal volume (4–6 ml/kg)")
            print("Risk flag: Moderate")

        else:
            print("Suggestion: Adjust ventilation based on ABG findings")
            print("Risk flag: Moderate")


# -----------------------------
# FINAL SAFETY NOTE
# -----------------------------

print("\nSafety note: This tool is for educational purposes only.")
print("Clinical correlation and professional judgment are required.")