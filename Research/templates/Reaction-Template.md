---
experiment_id: {{EXPERIMENT_ID}}
material: {{MATERIAL_ID}}
date: {{DATE}}
operator: {{OPERATOR}}
tags: [catalysis, performance, {{REACTION_TYPE}}]
---

# Catalysis Experiment: {{EXPERIMENT_ID}}

## Material

**Catalyst**: [[Materials/{{MATERIAL_ID}}]]
**Mass**: {{CATALYST_MASS}} g
**Pretreatment**: {{PRETREATMENT}}

## Reaction Conditions

**Reaction**: {{REACTION_NAME}}
**Temperature**: {{TEMPERATURE}} °C
**Pressure**: {{PRESSURE}} bar
**Flow rate**: {{FLOW_RATE}} mL/min
**GHSV**: {{GHSV}} h⁻¹
**Feed composition**: {{FEED_COMPOSITION}}

## Results

### Activity
- **Conversion**: {{CONVERSION}} ± {{CONVERSION_ERROR}}%
- **Yield**: {{YIELD}} ± {{YIELD_ERROR}}%
- **TOF**: {{TOF}} ± {{TOF_ERROR}} h⁻¹
- **TON**: {{TON}}

### Selectivity
- Product 1: {{SELECTIVITY_1}}%
- Product 2: {{SELECTIVITY_2}}%
- Product 3: {{SELECTIVITY_3}}%
- Carbon balance: {{CARBON_BALANCE}}%

### Stability
- Time on stream: {{TIME_ON_STREAM}} h
- Deactivation rate: {{DEACTIVATION_RATE}}% h⁻¹
- Final conversion: {{FINAL_CONVERSION}}%

## Analysis

### Performance Plots
- ![Conversion vs Time]({{PLOT_CONVERSION}})
- ![Selectivity Chart]({{PLOT_SELECTIVITY}})
- ![Arrhenius Plot]({{PLOT_ARRHENIUS}})

### Statistical Analysis
- Confidence interval (95%): {{CI_95}}
- Standard deviation: {{STD_DEV}}
- Reproducibility: {{REPRODUCIBILITY}}

### Comparison with Literature
| Reference | Conversion | Selectivity | TOF |
|-----------|------------|-------------|-----|
| This work | {{CONVERSION}}% | {{SELECTIVITY}}% | {{TOF}} h⁻¹ |
| [@ref1] | {{REF1_CONV}}% | {{REF1_SEL}}% | {{REF1_TOF}} h⁻¹ |
| [@ref2] | {{REF2_CONV}}% | {{REF2_SEL}}% | {{REF2_TOF}} h⁻¹ |

## Observations

*Qualitative observations during the experiment*

## Next Steps

- [ ] {{NEXT_STEP_1}}
- [ ] {{NEXT_STEP_2}}

## Related Experiments

- Previous: [[Reactions/{{PREVIOUS_EXP}}]]
- Next: [[Reactions/{{NEXT_EXP}}]]
