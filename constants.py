"""
constants.py
=============
Clinical thresholds and physiological reference ranges for the ABG CDSS.

All clinically-meaningful numbers live here (single source of truth) so the
engine contains no "magic numbers". Every value is referenced to a standard
critical-care / acid-base source and can be reviewed by a clinician in one place.

References:
- Winters RW. Terminology of acid-base disorders. Ann Intern Med. 1965.
- Berlin Definition of ARDS. JAMA. 2012;307(23):2526-2533.
- Marino's The ICU Book, 4th ed. (compensation & anion gap rules of thumb)
- ARDSNet ARMA trial (lung-protective ventilation, 4-6 mL/kg IBW)
"""

# --------------------------------------------------------------------------- #
#  Acid-base reference thresholds
# --------------------------------------------------------------------------- #
PH_LOW = 7.35            # below -> acidemia
PH_HIGH = 7.45           # above -> alkalemia
PH_CRIT_LOW = 7.20       # severe acidemia
PH_CRIT_HIGH = 7.55      # severe alkalemia

PACO2_NORMAL = 40.0      # mmHg, reference midpoint
PACO2_LOW = 35.0
PACO2_HIGH = 45.0

HCO3_NORMAL = 24.0       # mEq/L, reference midpoint
HCO3_LOW = 22.0
HCO3_HIGH = 26.0

# --------------------------------------------------------------------------- #
#  Anion gap
# --------------------------------------------------------------------------- #
# AG = Na - (Cl + HCO3).  Normal range varies by assay; 8-12 is the classic band.
ANION_GAP_NORMAL_LOW = 8.0
ANION_GAP_NORMAL_HIGH = 12.0
ANION_GAP_REFERENCE = 12.0     # used as the "normal" anchor for delta ratio
ALBUMIN_NORMAL = 4.0           # g/dL, for albumin-corrected AG
ALBUMIN_CORRECTION_FACTOR = 2.5  # add 2.5 to AG per 1 g/dL fall in albumin

# Delta ratio interpretation bands  (AG-12)/(24-HCO3)
DELTA_RATIO_NAGMA_MAX = 0.4    # < 0.4  -> pure normal-AG metabolic acidosis
DELTA_RATIO_MIXED_MAX = 1.0    # 0.4-1  -> mixed HAGMA + NAGMA
DELTA_RATIO_PURE_MAX = 2.0     # 1-2    -> pure HAGMA
#                                > 2    -> HAGMA + metabolic alkalosis / chronic resp acidosis

# --------------------------------------------------------------------------- #
#  Compensation formula coefficients
# --------------------------------------------------------------------------- #
# Winter's formula: expected PaCO2 = 1.5*HCO3 + 8  (+/- 2)
WINTERS_SLOPE = 1.5
WINTERS_INTERCEPT = 8.0
WINTERS_TOLERANCE = 2.0

# Metabolic alkalosis: expected PaCO2 = 0.7*HCO3 + 21  (+/- 2)
MET_ALK_SLOPE = 0.7
MET_ALK_INTERCEPT = 21.0
MET_ALK_TOLERANCE = 2.0

# Respiratory disorders: change in HCO3 per 10 mmHg change in PaCO2 from 40
HCO3_PER_10_ACUTE_RESP_ACIDOSIS = 1.0     # acute:   +1  per +10 CO2
HCO3_PER_10_CHRONIC_RESP_ACIDOSIS = 3.5   # chronic: +3.5 per +10 CO2
HCO3_PER_10_ACUTE_RESP_ALKALOSIS = 2.0    # acute:   -2  per -10 CO2
HCO3_PER_10_CHRONIC_RESP_ALKALOSIS = 4.5  # chronic: -4 to -5 per -10 CO2

# --------------------------------------------------------------------------- #
#  Oxygenation / P-F ratio  (Berlin ARDS staging)
# --------------------------------------------------------------------------- #
PF_NORMAL = 300          # >= 300 no significant impairment
PF_MILD = 200            # 200-299 mild
PF_MODERATE = 100        # 100-199 moderate ; < 100 severe
PF_CRITICAL = 80         # < 80 life-threatening hypoxemia
ARDS_MIN_PEEP = 5        # Berlin requires PEEP/CPAP >= 5 cmH2O

PAO2_SEVERE_HYPOXEMIA = 60
PAO2_MILD_HYPOXEMIA = 80
PAO2_NORMAL_UPPER = 100

# --------------------------------------------------------------------------- #
#  Weaning (RSBI)
# --------------------------------------------------------------------------- #
# RSBI = RR / Vt(L).  > 105 predicts weaning failure (Yang & Tobin 1991).
RSBI_FAILURE_THRESHOLD = 105

# --------------------------------------------------------------------------- #
#  Ideal Body Weight (Devine) & lung-protective tidal volume
# --------------------------------------------------------------------------- #
IBW_MALE_BASE = 50.0
IBW_FEMALE_BASE = 45.5
IBW_HEIGHT_COEFF = 0.91        # per cm above 152.4 cm (metric Devine)
IBW_REFERENCE_HEIGHT_CM = 152.4
LUNG_PROTECTIVE_TV_LOW = 4.0   # mL/kg IBW
LUNG_PROTECTIVE_TV_HIGH = 6.0  # mL/kg IBW
LUNG_PROTECTIVE_TV_CEILING = 8.0  # mL/kg IBW - above this is not protective

# --------------------------------------------------------------------------- #
#  Physiological input validation ranges  (reject / warn outside these)
# --------------------------------------------------------------------------- #
# (hard_min, hard_max) -> reject outside ; (warn_low, warn_high) -> flag as unusual
VALIDATION_RANGES = {
    "ph":    {"hard": (6.5, 8.0),   "plausible": (6.8, 7.8)},
    "pco2":  {"hard": (5.0, 150.0), "plausible": (10.0, 120.0)},
    "hco3":  {"hard": (2.0, 60.0),  "plausible": (5.0, 50.0)},
    "po2":   {"hard": (10.0, 700.0),"plausible": (20.0, 600.0)},
    "na":    {"hard": (100.0, 180.0),"plausible": (120.0, 160.0)},
    "cl":    {"hard": (60.0, 140.0),"plausible": (80.0, 120.0)},
    "fio2":  {"hard": (21.0, 100.0),"plausible": (21.0, 100.0)},
    "peep":  {"hard": (0.0, 30.0),  "plausible": (0.0, 24.0)},
    "rr":    {"hard": (1.0, 80.0),  "plausible": (4.0, 60.0)},
    "tv":    {"hard": (50.0, 2000.0),"plausible": (150.0, 1000.0)},
    "albumin": {"hard": (0.5, 6.0), "plausible": (1.5, 5.5)},
    "height_cm": {"hard": (120.0, 220.0), "plausible": (140.0, 210.0)},
}

# --------------------------------------------------------------------------- #
#  Severity scoring (CUSTOM HEURISTIC - not a validated score)
# --------------------------------------------------------------------------- #
# NOTE: This is an internal triage heuristic, NOT APACHE II / SOFA / any
# validated clinical score. Always labelled as such in the output.
SEVERITY_LABEL = "Custom heuristic severity index (0-10) - NOT a validated clinical score"

# --------------------------------------------------------------------------- #
#  Safety / positioning
# --------------------------------------------------------------------------- #
SAFETY_NOTE = (
    "This tool is a clinical decision SUPPORT aid for use BY a qualified "
    "respiratory therapist / physician. It does not replace clinical judgment, "
    "and must not be used as a standalone diagnostic or treatment decision tool. "
    "Clinical correlation and professional review are required."
)
SAFETY_NOTE_AR = (
    "هذه الأداة وسيلة مساندة للقرار السريري يستخدمها الأخصائي المؤهل — "
    "لا تحل محل الحكم السريري، ولا تُستخدم كأداة تشخيص أو علاج مستقلة. "
    "يلزم الربط السريري والمراجعة المهنية."
)
