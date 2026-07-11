# ABG Clinical Decision Support Tool

> A rule-based clinical decision **support** aid for arterial/venous/capillary blood-gas interpretation, oxygenation assessment, and ventilator-context reasoning — designed for use **by** a qualified respiratory therapist or physician.

**⚠️ This tool does not replace clinical judgment.** It is not a standalone diagnostic or treatment device. Every output requires clinical correlation and professional review.

> **Version status:** `v1.0.0` is a *clinical-logic implementation* (software-verified by an internal test suite). It is **not yet clinically validated for deployment**; formal clinical validation is a planned, separate phase.

---

## Overview

This engine takes a blood-gas sample plus optional ventilator and electrolyte data and returns a structured, transparent interpretation: acid–base status, anion gap, compensation adequacy, oxygenation severity, and context-aware ventilator guidance. It is **rule-based, not AI** — every conclusion traces to an explicit, reviewable clinical rule.

## Clinical capabilities (v1.0)

| Area | What the engine does |
|------|----------------------|
| **Acid–base** | Determines acidemia/alkalemia and the primary disorder |
| **Anion gap** | Calculates AG = Na − (Cl + HCO₃), with optional albumin correction; classifies HAGMA vs NAGMA |
| **Delta ratio** | Detects concurrent metabolic disorders in high-AG acidosis |
| **Compensation** | Full checks for **all four** primary disorders (Winter's, metabolic alkalosis, acute/chronic respiratory) and flags mixed disorders |
| **Oxygenation** | PaO₂ interpretation (spontaneous) and P/F ratio (ventilated) |
| **ARDS staging** | Berlin-style severity (PEEP ≥ 5 gated) with explicit criteria limitations |
| **Ventilation** | IBW (Devine) + lung-protective tidal-volume check; RSBI weaning index |
| **Triage** | Risk flag, rule-based Clinical Attention Index (heuristic, non-prognostic), priority level, clinical flags, clinician review considerations |

## Safety design

- **Input validation** rejects physiologically impossible values (e.g. pH 8.5, FiO₂ 500%) and warns on unusual ones.
- **Henderson–Hasselbalch consistency check** catches internally inconsistent samples (likely lab/data-entry errors).
- **FiO₂ scale guard** auto-detects the common 0.5-vs-50 error.
- The **Clinical Attention Index is explicitly labelled** as a rule-based heuristic, **non-prognostic**, and **not** a validated score (APACHE/SOFA).

## Project structure

```
abg_cdss/
├── abg_engine.py      # Core clinical engine (pure, importable, no I/O)
├── validation.py      # Physiological input validation & safety checks
├── constants.py       # All clinical thresholds (single source of truth)
├── cli.py             # Interactive command-line interface
├── tests/
│   └── test_engine.py # 31 clinical validation test cases
├── CHANGELOG.md
└── README.md
```

## Usage

**Interactive:**
```bash
python cli.py
```

**As a library:**
```python
from abg_engine import analyze_abg

result = analyze_abg(
    sample_type="ABG", clinical_context="ARDS",
    ph=7.30, pco2=48, hco3=23, po2=60, na=140, cl=104,
    on_vent="yes", mode="PCV", rr=24, tv=400, peep=12, fio2=80,
    height_cm=170, sex="male",
)
print(result["final_interpretation"])   # -> "Acute Respiratory Acidosis"
print(result["pf_ratio"])               # -> 75.0
print(result["priority_level"])         # -> "IMMEDIATE ICU ACTION"
```

**Run the test suite:**
```bash
python tests/test_engine.py
```

## Clinical references

- Winters RW. Terminology of acid-base disorders. *Ann Intern Med.* 1965.
- ARDS Definition Task Force. Acute respiratory distress syndrome: the Berlin Definition. *JAMA.* 2012;307(23):2526–2533.
- Yang KL, Tobin MJ. A prospective study of indexes predicting the outcome of trials of weaning from mechanical ventilation (RSBI). *N Engl J Med.* 1991;324:1445–1450.
- The Acute Respiratory Distress Syndrome Network. Ventilation with lower tidal volumes (ARMA). *N Engl J Med.* 2000;342:1301–1308.
- Marino PL. *The ICU Book*, 4th ed.

## Limitations

- Rule-based; does not learn from data.
- ARDS staging uses P/F only — full Berlin criteria (imaging, onset, cardiac exclusion) require clinician confirmation.
- Severity score is a triage heuristic, not a validated mortality/severity scale.
- Not a regulated medical device; **not for autonomous clinical use.**
- Clinical deployment may require institutional approval, clinical validation, cybersecurity controls, health-data governance compliance, quality-management processes, and potentially medical-device regulatory assessment depending on the intended use and implementation context.

## License

See `LICENSE`.

---

<div dir="rtl">

# أداة دعم القرار السريري لتحليل غازات الدم (ABG)

أداة **مساندة** للقرار السريري، قائمة على القواعد، لتفسير غازات الدم الشرياني/الوريدي/الشعري وتقييم الأكسجة والتفكير في سياق التهوية الميكانيكية — مصمّمة ليستخدمها **الأخصائي** المؤهل (أخصائي علاج تنفسي أو طبيب).

**⚠️ هذه الأداة لا تحل محل الحكم السريري.** ليست أداة تشخيص أو علاج مستقلة، وكل مخرجاتها تتطلب ربطاً سريرياً ومراجعة مهنية.

## القدرات السريرية (الإصدار 1.0)

- تحديد الحالة الحمضية–القاعدية والاضطراب الأساسي.
- حساب فجوة الأنيون (مع تصحيح الألبومين) وتصنيف HAGMA / NAGMA.
- نسبة الدلتا لكشف الاضطرابات المختلطة.
- فحص التعويض **للاضطرابات الأربعة** كاملة (Winter's، القلاء الأيضي، الحماض/القلاء التنفسي الحاد والمزمن).
- تقييم الأكسجة (PaO₂ ونسبة P/F).
- تصنيف ARDS حسب Berlin (بشرط PEEP ≥ 5) مع توضيح حدود المعايير.
- حساب الوزن المثالي (IBW) والتحقق من التهوية الواقية للرئة، ومؤشر الفطام RSBI.
- مؤشر الانتباه السريري (اجتهادي، غير تنبّؤي) ومستوى الأولوية واعتبارات لمراجعة الأخصائي.

## السلامة

- التحقق من المدخلات ورفض القيم المستحيلة فسيولوجياً.
- فحص اتساق Henderson–Hasselbalch لكشف الأخطاء المخبرية.
- كشف خطأ إدخال FiO₂ الشائع (0.5 مقابل 50).
- مؤشر الانتباه السريري **اجتهادي وغير تنبّؤي** وليس مقياساً معتمداً (مثل APACHE/SOFA).

## التشغيل

```bash
python cli.py          # الواجهة التفاعلية
python tests/test_engine.py   # حزمة الاختبارات
```

</div>
