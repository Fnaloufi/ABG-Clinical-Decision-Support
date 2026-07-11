"""
validation.py
=============
Physiological input validation for the ABG CDSS.

Project : CritiCore-CDSS
Author  : Fahad Aloufi (Head of Respiratory Therapy)

Two levels of checking:
  1. HARD limits  -> value is physiologically impossible / a data-entry error.
                     analyze() will refuse to interpret and returns an error.
  2. PLAUSIBLE band-> value is possible but unusual; a warning is attached but
                     interpretation proceeds.

This is a safety-critical layer: in a medical tool, silently interpreting
pH = 8.5 or FiO2 = 500 is worse than refusing.
"""

from constants import VALIDATION_RANGES


class ValidationError(ValueError):
    """Raised when an input is physiologically impossible."""


def validate_value(name: str, value, required: bool = True):
    """
    Validate a single numeric input against its physiological range.

    Returns a list of warning strings (empty if none).
    Raises ValidationError if the value is outside hard physiological limits.
    """
    warnings = []

    if value is None:
        if required:
            raise ValidationError(f"'{name}' is required but was not provided.")
        return warnings

    # numeric coercion
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"'{name}' must be a number (got: {value!r}).")

    ranges = VALIDATION_RANGES.get(name)
    if ranges is None:
        return warnings  # no range defined -> skip

    hard_min, hard_max = ranges["hard"]
    if value < hard_min or value > hard_max:
        raise ValidationError(
            f"'{name}' = {value} is outside the physiologically possible range "
            f"({hard_min}-{hard_max}). Please re-check the entry."
        )

    plaus_min, plaus_max = ranges["plausible"]
    if value < plaus_min or value > plaus_max:
        warnings.append(
            f"'{name}' = {value} is unusual (expected {plaus_min}-{plaus_max}); "
            f"verify the value."
        )

    return warnings


def validate_fio2_scale(fio2):
    """
    Catch the classic 0.5 vs 50 FiO2 error.
    FiO2 should be a PERCENT (21-100). If a fraction (0.21-1.0) sneaks in,
    the P/F ratio would be off by 100x.
    """
    if fio2 is None:
        return None, []
    fio2 = float(fio2)
    warnings = []
    if 0.0 < fio2 <= 1.0:
        warnings.append(
            f"FiO2 = {fio2} looks like a fraction. Interpreting as "
            f"{fio2 * 100:.0f}%. Enter FiO2 as a percent (e.g. 50 for 50%)."
        )
        fio2 = fio2 * 100
    return fio2, warnings


def validate_abg_inputs(
    ph, pco2, hco3, po2, na=None, cl=None,
    on_vent="no", fio2=None, peep=None, rr=None, tv=None,
    albumin=None, height_cm=None,
):
    """
    Validate the full input set. Returns (cleaned_values_dict, warnings_list).
    Raises ValidationError on any hard-limit violation.
    """
    warnings = []

    warnings += validate_value("ph", ph)
    warnings += validate_value("pco2", pco2)
    warnings += validate_value("hco3", hco3)
    warnings += validate_value("po2", po2)

    # Na / Cl now mandatory for a complete (anion-gap-capable) interpretation
    warnings += validate_value("na", na)
    warnings += validate_value("cl", cl)

    # optional albumin (for corrected AG)
    warnings += validate_value("albumin", albumin, required=False)

    cleaned_fio2 = None
    if str(on_vent).strip().lower() == "yes":
        cleaned_fio2, fio2_warn = validate_fio2_scale(fio2)
        warnings += fio2_warn
        warnings += validate_value("fio2", cleaned_fio2)
        warnings += validate_value("peep", peep, required=False)
        warnings += validate_value("rr", rr, required=False)
        warnings += validate_value("tv", tv, required=False)

    warnings += validate_value("height_cm", height_cm, required=False)

    # internal consistency check: Henderson-Hasselbalch sanity
    # pH, PaCO2, HCO3 should be roughly consistent. Large mismatch -> lab error.
    consistency_warn = _check_henderson_hasselbalch(ph, pco2, hco3)
    if consistency_warn:
        warnings.append(consistency_warn)

    cleaned = {
        "ph": float(ph), "pco2": float(pco2), "hco3": float(hco3),
        "po2": float(po2),
        "na": float(na) if na is not None else None,
        "cl": float(cl) if cl is not None else None,
        "fio2": cleaned_fio2,
        "peep": float(peep) if peep is not None else None,
        "rr": float(rr) if rr is not None else None,
        "tv": float(tv) if tv is not None else None,
        "albumin": float(albumin) if albumin is not None else None,
        "height_cm": float(height_cm) if height_cm is not None else None,
    }
    return cleaned, warnings


def _check_henderson_hasselbalch(ph, pco2, hco3, tolerance=0.10):
    """
    Verify the reported pH is consistent with PaCO2 and HCO3.
    pH = 6.1 + log10(HCO3 / (0.03 * PaCO2))
    If the calculated pH differs from the reported pH by more than `tolerance`,
    the sample is internally inconsistent (likely a lab/data-entry error).
    """
    import math
    try:
        calc_ph = 6.1 + math.log10(float(hco3) / (0.03 * float(pco2)))
    except (ValueError, ZeroDivisionError):
        return None
    diff = abs(calc_ph - float(ph))
    if diff > tolerance:
        return (
            f"Internal inconsistency: reported pH ({ph}) does not match the pH "
            f"calculated from PaCO2 and HCO3 ({calc_ph:.2f}) via Henderson-"
            f"Hasselbalch (difference {diff:.2f}). Possible lab or data-entry "
            f"error - verify the sample before acting on the interpretation."
        )
    return None
