# ABG Clinical Decision Support Tool - V1
# For educational and clinical support use only
sample_type=input("Enter sample type(ABG/VBG/CBG):").upper()
ph=float(input("Enter pH:"))
pco2=float(input("Enter PCO2(mmHg):"))
hco3=float(input("Enter HCO3)(mEq/L):"))
po2=float(input("Enter pO2(mmHg):"))
on_vent= input("Is the patient on mechanical ventilation?(yes/no):").lower()
if on_vent=="yes":
    mode=input("Enter ventilator mode:")
    rr=input("Enter respiratory rate(RR):")
    tv=input("Enter tidal volume(TV):")
    peep=input("Enter PEEP:")
    fio2=input("EnterFio2(%):")
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
#Step 3:Oxygenation note
if sample_type =="ABG":
    if po2< 60:
        oxygenation_note="Severe hypoxemia"
    elif po2<80:
        oxygenation_note="Pao2 within common normal range"
    else:
        oxygenation_note="PaO2 above common reference range"
elif sample_type =="VBG":
    oxygenation_note="Oxygenation cannot be reliably assessed from VBG pO2"
elif sample_type == "CBG":
    oxygenation_note="Oxygenation assessment from CBG pO2 is limited;ABG is preferred"
else:
    oxygenation_note="Unknown sample type - oxygenation interpretation limited"
print("Oxygenation:",oxygenation_note)
#Step 4:Ventilator context
if on_vent == "yes":
    print(" Ventilator status: On mechanical ventilation")
    print("Mode:",mode)
    print("RR",rr)
    print("TV",tv)
    print("PEEP",peep)
    print("FIO2",fio2)
else:
    print("Ventilator status: Not on mechanical ventilation")
#Step 5: Risk flag
if ph<7.20:
    risk_flag="High-severe acidemia"
elif ph>7.55:
    risk_flag="High-severe alkalemia"
elif sample_type=="ABG" and po2<60:
    risk_flag="High-severe hypoxemia"
elif "mixed" in primary_disorder.lower():
    risk_flag="Moderate to High-possible mixed disorder"
elif on_vent=="yes":
    risk_flag="Moderate- ventilated patientrequires close clinical review"
else:
    risk_flag="Moderate/Low - clinical correlation required"
print("Risk flag:", risk_flag)
#Step 6: safety note
print("\nSafety note:This tool is for educational and clinical support purposes only")
print("it must not be used as a standalone diagnosis or treatment decision tool.")
print("Clinical correlation and professional review are required.")







    

            
