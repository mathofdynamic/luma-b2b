# Scoring model

The adopted model is derived from the latest evidence-first research report and keeps every component separately auditable. Scores are normalized to 0–100.

```text
Raw = 12C + 12O + 10R + 16V + 10D + 12G(d) + 8A + 6E + 5P + 4F + 3S + 2L
G(d) = exp(-((d - 55) / 24)^2)
Final = clamp(Raw + trigger_bonus - risk_penalty, 0, 100)
```

`C` strength, `O` complexity, `R` repetition, `V` ROI, `D` usable digital information, `A` capability gap, `E` access, `P` project size, `F` feasibility, `S` sales ease and `L` regulatory ease. `d` is observed digital maturity (0–100). `A` is high when internal AI/software capability is low.

User-requested tiers: A ≥80, B 70–79, C 60–69, D 45–59, Reject <45. Hard disqualifiers override score.
