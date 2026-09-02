# Scoring model

The adopted model is derived from the latest evidence-first research report and keeps every component separately auditable. Scores are normalized to 0–100.

The production audit implementation is `src/audit/commercial.py` and the reviewable configuration is `config/scoring.yaml`.

```text
raw = sum(weight * component / 100)
new_score = clamp(round(raw + trigger_bonus - risk_penalty), 0, 100)
confidence_factor = round(0.40 + 0.60 * score_confidence / 100, 3)
confidence_adjusted_score = round(new_score * confidence_factor, 1)
```

Weights are: company strength 12, operational complexity 12, workflow density 10, AI ROI 16, usable data 10, digital-maturity fit 12, outsourcing fit 8, sales access 6, expected project value 5, implementation 4, sales-cycle ease 3 and regulatory ease 2.

Every component is stored separately. Digital maturity remains a non-linear fit concept: known moderate/fragmented public operating surfaces are favored; known high technical maturity reduces fit; unknown maturity is neutral, not favorable. `KNOWN_LOW_INTERNAL_TECH` and `UNKNOWN_INTERNAL_TECH` are separate statuses. Unknown technical capability maps to neutral 50/50 scores and lowers confidence.

User-requested tiers are applied to the revised raw score: A ≥80 with the READY gate, B 70–79 with evidence/workflow gates, C 60–69, D 45–59 and Reject <45 or hard disqualifier. A `confidence_adjusted_score` is used for ranking within commercial reports; it does not hide the raw score.

READY additionally requires supported active operation, at least two independent source families, commercial evidence strength ≥70, score confidence ≥65, a `EVIDENCE_SUPPORTED` or `STRONG_HYPOTHESIS` workflow, no known high internal AI/software capability and revised score ≥70. Proposals are generated only for READY records.
