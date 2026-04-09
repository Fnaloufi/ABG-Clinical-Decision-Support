# ABG Clinical Decision Support Tool - V1
# For educational and clinical support use only
sample_type=input("Enter sample type(ABG/VBG/CBG):").strip().upper()
ph=float(input("Enter pH:"))
pco2=float(input("Enter PCO2(mmHg):"))
hco3=float(input("Enter HCO3)(mEq/L):"))
po2=float(input("Enter pO2(mmHg):").strip())
on_vent= input("Is the patient on mechanical ventilation?(yes/no):").strip().lower()
if on_vent=="yes":
    mode=input("Enter ventilator mode:")
    rr=input("Enter respiratory rate(RR):")
    tv=input("Enter tidal volume(TV):")
    peep=input("Enter PEEP:")
    fio2= float(input("Enter Fio2 (%):"))
print("\n---Blood Gas Result---")
#Step 1:Determine acid-base status
if ph<7.35:
    print("Acid-base status:Acidosis")
elif ph>7.45:
    print("Acid-base status:Alkalosis")
else:
    print("Acid-base status:Near normal/compensated")
#Step 2: Determine primary disorder
if ph< 7.35:
    if pco2>45 and hco3<22:
        primary_disorder="possible mixed acidosis"
    elif pco2>45:
        primary_disorder="Respiratory Acidosis"
    elif hco3<22:
        primary_disorder="Metabolic Acidosis"
    else:
        primary_disorder="unclear"
elif ph>7.45:
    if pco2<35 and hco3>26:
        primary_disorder="Possible mixed alkalosis"
    elif pco2<35:
        primary_disorder="Respiratory Alkalosis"
    elif hco3>26:
        primary_disorder="Metabolic Alkalosis"
    else:
        primary_disorder="Mixed or unclear"
print("Primary disorder:",primary_disorder)
secondary_disorder=""
#step 3:Check compensation for metabolic acidosis 
if primary_disorder=="Metabolic Acidosis":
    expected_pco2 =(1.5*hco3)+8
    low_range=expected_pco2-2
    high_range=expected_pco2+2
    print("Expected pCo2:", round(expected_pco2,1),f"(range{round(low_range,1)}-{round(high_range,1)})")
    if pco2< low_range:
        print("Compensation: Lower than expected pCO2")
        secondary_disorder="Respiratory Alkalosis"
    elif pco2> high_range:
        print("Compensation: Higher than expected pCO2")
        secondary_disorder="Respiratory Acidosis"
    else:
        print("Compensation: Appropriate respiratory compensation")
    if secondary_disorder!="":
        print("Secondary disorder:", secondary_disorder)
        print("Final interpretation:",primary_disorder,"+", secondary_disorder)
    else:
        print("Final interpretation:", primary_disorder,"(compensated)")
#Step 4:Oxygenation note
if sample_type =="ABG":
    if po2< 60:
        oxygenation_note="Severe hypoxemia"
    elif po2<80:
        oxygenation_note="Mild to moderate hypoxemia"
    elif po2 <= 100:
        oxygenation_note="PaO2 within common normal range"
    else:
        oxygenation_note="PaO2 above common reference range"
elif sample_type =="VBG":
    oxygenation_note="Oxygenation cannot be reliably assessed from VBG pO2"
elif sample_type == "CBG":
    oxygenation_note="Oxygenation assessment from CBG pO2 is limited;ABG is preferred"
else:
    oxygenation_note="Unknown sample type - oxygenation interpretation limited"
print("Oxygenation:",oxygenation_note)
# Step 5: P/F Ratio
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
#Step 6: Current Ventilator settings
if on_vent == "yes":
    print("Ventilator status: On mechanical ventilation")
    print("Current ventilator settings:")
    print("Mode:", mode)
    print("RR:", rr)
    print("TV:", tv)
    print("peep:", peep)
    print("FIO2:", fio2)
else:
    print("Ventilator status: Not on mechanical ventilation")
#Step 7: Ventilator suggestion
if on_vent=="yes":
    print("\n---Ventilator Suggestion---")
    if secondary_disorder:
        print("Suggestion: Mixed disorder - treat underlying cause, avoid immediate ventilator changes")
    elif"Respiratory Acidosis" in primary_disorder:
        print("Suggestion: Increase minute ventilation(increase RR first; consider increasing VT cautiously)")
    elif"Respiratory Alkalosis" in primary_disorder:
        print("Suggestion: Decrease minute ventilation(decrease RR first; consider decreasing VT if appropriate)")
    elif primary_disorder=="Metabolic Acidosis":
        print("Suggestion: Ensure adequate ventilation,consider underlying cause(do not suppress compensation)")
    elif primary_disorder=="Metabolic Alkalosis":
        print("Suggestion: Consider reducing ventilation cautiously if clinically indicated")
    else:
        print("Suggestion: Clinical review required")
#Step 8: Risk flag
if ph<7.20:
    risk_flag="High-severe acidemia"
elif ph>7.55:
    risk_flag="High-severe alkalemia"
elif sample_type=="ABG" and po2<60:
    risk_flag="High-severe hypoxemia"
elif "mixed" in primary_disorder.lower() or secondary_disorder:
    risk_flag="Moderate to High - possible mixed disorder"
elif on_vent=="yes":
    risk_flag="Moderate - ventilated patientrequires close monitoring "
else:
    risk_flag="Moderate/Low - clinical correlation required"
print("Risk flag:", risk_flag)
#Step 9: safety note
print("\nSafety note:This tool is for educational and clinical support purposes only")
print("it must not be used as a standalone diagnosis or treatment decision tool.")
print("Clinical correlation and professional review are required.")







    

            
