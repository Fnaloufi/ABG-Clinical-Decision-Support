"""
cli.py
======
Interactive command-line front-end for the ABG CDSS.

Project : CritiCore-CDSS
Author  : Fahad Aloufi (Head of Respiratory Therapy)

Separated from the engine so that the same clinical logic can also power a
web API or GUI later. All user I/O and error handling live here.

Run:  python cli.py
"""

from abg_engine import analyze_abg
import constants as C


# --------------------------------------------------------------------------- #
#  Robust input helpers (no crash on bad entry)
# --------------------------------------------------------------------------- #
def ask_float(prompt, allow_blank=False):
    while True:
        raw = input(prompt).strip()
        if allow_blank and raw == "":
            return None
        try:
            return float(raw)
        except ValueError:
            print("  -> Please enter a number (e.g. 7.35).")


def ask_choice(prompt, choices):
    choices_up = [c.upper() for c in choices]
    while True:
        raw = input(prompt).strip().upper()
        if raw in choices_up:
            return raw
        print(f"  -> Please choose one of: {', '.join(choices)}")


def ask_yes_no(prompt):
    while True:
        raw = input(prompt).strip().lower()
        if raw in ("yes", "y"):
            return "yes"
        if raw in ("no", "n"):
            return "no"
        print("  -> Please answer yes or no.")


# --------------------------------------------------------------------------- #
#  Output formatter
# --------------------------------------------------------------------------- #
def print_results(r):
    if not r.get("valid", False):
        print("\n" + "!" * 60)
        print("  INPUT ERROR - interpretation not performed")
        print("  " + r.get("error", "unknown error"))
        print("!" * 60)
        print("\n" + r.get("safety_note", ""))
        return

    line = "-" * 60
    print("\n" + line)
    print("  ABG CLINICAL DECISION SUPPORT - RESULT")
    print(line)

    if r["warnings"]:
        print("\n  WARNINGS:")
        for w in r["warnings"]:
            print(f"   ! {w}")

    print("\n  ACID-BASE")
    print(f"   Status              : {r['acid_base_status']}")
    print(f"   Primary disorder    : {r['primary_disorder']}")
    if r["compensation"]:
        print(f"   Compensation        : {r['compensation']}")
    if r["compensation_status"]:
        print(f"   Compensation status : {r['compensation_status']}")
    if r["secondary_disorder"]:
        print(f"   Secondary disorder  : {r['secondary_disorder']}")
    print(f"   Final interpretation: {r['final_interpretation']}")

    print("\n  ANION GAP")
    print(f"   Anion gap           : {r['anion_gap']}")
    if r["anion_gap_corrected"] is not None:
        print(f"   Albumin-corrected AG: {r['anion_gap_corrected']}")
    print(f"   Interpretation      : {r['anion_gap_interpretation']}")
    if r["delta_ratio"] is not None:
        print(f"   Delta ratio         : {r['delta_ratio']}  ({r['delta_ratio_interpretation']})")

    print("\n  OXYGENATION")
    if r["pf_ratio"] is not None:
        print(f"   P/F ratio           : {r['pf_ratio']}")
    print(f"   Status              : {r['oxygenation_status']}")

    if r["ventilator_status"] == "On mechanical ventilation":
        print("\n  VENTILATION")
        for k, v in r["ventilator_settings"].items():
            print(f"   {k:<20}: {v}")
        if r["ibw_kg"] is not None:
            print(f"   IBW (kg)            : {r['ibw_kg']}")
        if r["tv_per_kg"] is not None:
            print(f"   TV per kg IBW       : {r['tv_per_kg']}  ({r['lung_protective']})")
        if r["rsbi"] is not None:
            print(f"   RSBI                : {r['rsbi']}  ({r['rsbi_interpretation']})")

    print("\n  CLINICAL CONTEXT")
    print(f"   {r['context_interpretation']}")
    for note in r["context_notes"]:
        print(f"   - {note}")

    if r["ventilator_suggestions"]:
        print("\n  VENTILATOR SUGGESTIONS")
        for s in r["ventilator_suggestions"]:
            print(f"   - {s}")

    print("\n  TRIAGE")
    print(f"   Risk flag           : {r['risk_flag']}")
    print(f"   Clinical attention  : {r['attention_index']}/10  ({r['attention_index_label']})")
    print(f"   Priority level      : {r['priority_level']}")
    if r["clinical_flags"]:
        print(f"   Clinical flags      : {', '.join(r['clinical_flags'])}")

    if r["clinical_considerations"]:
        print("\n  CLINICAL CONSIDERATIONS (for clinician review - not directives)")
        for a in r["clinical_considerations"]:
            print(f"   - {a}")

    print("\n" + line)
    print("  SAFETY: " + r["safety_note"])
    print(line)


# --------------------------------------------------------------------------- #
#  Main
# --------------------------------------------------------------------------- #
def main():
    print("=" * 60)
    print("  ABG Clinical Decision Support Tool  (v1.0)")
    print("  A support aid for use BY a qualified clinician.")
    print("=" * 60)

    sample_type = ask_choice("Sample type (ABG/VBG/CBG): ", ["ABG", "VBG", "CBG"])
    clinical_context = ask_choice("Clinical context (ARDS/COPD/OTHER): ",
                                  ["ARDS", "COPD", "OTHER"])

    ph = ask_float("pH: ")
    pco2 = ask_float("PaCO2 (mmHg): ")
    hco3 = ask_float("HCO3 (mEq/L): ")
    po2 = ask_float("pO2 (mmHg): ")
    na = ask_float("Na (mEq/L): ")
    cl = ask_float("Cl (mEq/L): ")
    albumin = ask_float("Albumin (g/dL) [optional, Enter to skip]: ", allow_blank=True)

    on_vent = ask_yes_no("On mechanical ventilation? (yes/no): ")
    mode = rr = tv = ""
    peep = fio2 = height_cm = None
    sex = "male"

    if on_vent == "yes":
        mode = input("Ventilator mode: ").strip()
        rr = ask_float("RR (breaths/min): ", allow_blank=True)
        tv = ask_float("Tidal volume (mL): ", allow_blank=True)
        peep = ask_float("PEEP (cmH2O): ", allow_blank=True)
        fio2 = ask_float("FiO2 (%): ")
        height_cm = ask_float("Height (cm) [for IBW, optional]: ", allow_blank=True)
        if height_cm is not None:
            sex = ask_choice("Sex (M/F): ", ["M", "F"])

    results = analyze_abg(
        sample_type=sample_type, clinical_context=clinical_context,
        ph=ph, pco2=pco2, hco3=hco3, po2=po2, na=na, cl=cl,
        on_vent=on_vent, mode=mode, rr=rr, tv=tv, peep=peep, fio2=fio2,
        albumin=albumin, height_cm=height_cm, sex=sex,
    )
    print_results(results)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
