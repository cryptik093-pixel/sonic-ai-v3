# Evidence Learning Loop

## Purpose
Ensure Sonic learns from observed outcomes rather than accumulating unvalidated recommendations.

```text
Decision
  ->
Action
  ->
Observation
  ->
Metric
  ->
Validation
  ->
Memory
  ->
Next Decision
```

## Commerce example

```text
Hypothesis:
Audio preview above CTA increases add-to-cart rate.

Baseline:
record current validated metric

Experiment:
preview-first layout

Observed:
record measured experiment result

Confidence:
calculated from evidence quality/sample

Decision:
PROMOTE_VARIANT | REJECT_VARIANT | CONTINUE_TEST
```

## Rule
Never manufacture experiment metrics. Baseline and observed values must come from validated analytics evidence.
