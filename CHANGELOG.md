# Changelog

All notable changes to the ABG Clinical Decision Support tool.

## [1.0.0] — 2026-07 — Clinical Safety & Restructure

Consolidation of the prior V2–V7 iterations into a single, tested, modular,
clinically-hardened package.

### Added (clinical)
- **Anion gap** calculation (Na − Cl − HCO₃) with optional **albumin correction**.
- **HAGMA vs NAGMA** classification.
- **Delta ratio** (delta-delta) for detecting concurrent metabolic disorders.
- **Complete compensation logic for all four primary disorders**, replacing the
  previous metabolic-acidosis-only Winter's check:
  - Metabolic alkalosis expected PaCO₂ (0.7·HCO₃ + 21).
  - Acute vs chronic respiratory acidosis (ΔHCO₃ 1 vs 3.5 per 10 mmHg).
  - Acute vs chronic respiratory alkalosis (ΔHCO₃ 2 vs 4.5 per 10 mmHg).
  - Superimposed-metabolic-disorder detection for respiratory primaries.
- **IBW (Devine)** + **lung-protective tidal-volume** check (4–6 mL/kg IBW).
- **RSBI** weaning index (RR / Vt).
- Explicit **ARDS Berlin-criteria limitations** note.

### Added (safety)
- Physiological **input validation** (hard limits reject impossible values).
- **Henderson–Hasselbalch consistency** check for lab/data-entry errors.
- **FiO₂ scale guard** (auto-detects 0.5-vs-50 fraction/percent error).
- Bilingual (EN/AR) safety note on every result.
- Severity score now explicitly labelled a non-validated heuristic.

### Added (engineering)
- Modular architecture: `abg_engine` / `validation` / `constants` / `cli`.
- Engine is a **pure function** (no I/O) — reusable by CLI, API, or GUI.
- **31 clinical validation test cases** (all passing).
- Robust CLI input handling (no crash on malformed entry).
- Professional bilingual README with clinical references.

### Changed
- Terminology: "Acidosis/Alkalosis" → "Acidemia/Alkalemia" for the pH status.
- Single canonical codebase replaces 8 duplicated script files.

## Historical (pre-1.0)
- **V2** — Foundation: ABG interpretation, Winter's, ventilator context, risk flag.
- **V3** — Physiology: P/F ratio, oxygenation classification.
- **V4** — Decision intelligence: ARDS/COPD context logic.
- **V5** — Product layer: structured dict output, JSON export.
- **V6** — Scoring engine: severity score, priority level, clinical flags.
- **V7** — Action engine + PEEP-gated ARDS staging.
