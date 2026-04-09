# ABG Tool – Version 4 (Decision Intelligence)

## Features
- ABG interpretation
- Compensation logic
- Mixed disorder handling
- Oxygenation note
- P/F ratio
- Ventilator settings output
- Clinical context layer (ARDS / COPD / OTHER)
- Context-aware ventilator suggestion
- Risk flag

## Decision Logic Added
- ARDS logic based on context and P/F ratio
- COPD logic prioritizing pH and pCO2 interpretation
- Ventilator suggestions now depend on context, not ABG alone

## Notes
- ARDS logic is still simplified
- COPD logic does not yet include chronic baseline handling
- P/F ratio is used as oxygenation severity indicator
- This is still a rule-based system, not AI

## Next Step
- Move to Product Layer (V5)
- Convert print-based output into structured output
- Prepare for UI / app integration