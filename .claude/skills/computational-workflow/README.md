# Computational Workflow Skill

Comprehensive computational chemistry workflow for DFT analysis, reaction mechanism studies, and energy diagram generation.

## Features

- **Multi-Software Support**: Parse outputs from Gaussian, ORCA, and VASP
- **Thermodynamic Analysis**: Calculate ΔG, ΔH, ΔS, equilibrium constants, and rate constants
- **Activation Barriers**: Analyze transition states and calculate activation energies
- **Multi-Step Mechanisms**: Full reaction pathway analysis with intermediates
- **Energy Diagrams**: Publication-quality reaction coordinate diagrams
- **Obsidian Integration**: Auto-generate markdown reports with backlinks

## Supported DFT Software

| Software | File Format | Energy Unit | Features |
|----------|-------------|-------------|----------|
| Gaussian | `.log` | Hartree | Energies, geometries, frequencies, thermochemistry |
| ORCA | `.out` | Hartree | Energies, geometries, frequencies, thermochemistry |
| VASP | `OUTCAR` | eV | Energies, geometries, forces, stress tensor |

## Usage

### 1. Parse Single Output File

```python
from computational_workflow import ComputationalWorkflow

workflow = ComputationalWorkflow(software="gaussian")
parsed_data = workflow.parse_output_files(["reactant.log"])
```

### 2. Calculate Reaction Thermodynamics

```python
results = workflow.analyze_reaction_energy(
    reactant_files=["reactant.log"],
    product_files=["product.log"],
    temperature=298.15
)

print(f"ΔG = {results['ΔG']:.2f} kcal/mol")
print(f"ΔH = {results['ΔH']:.2f} kcal/mol")
print(f"K_eq = {results['K_eq']:.2e}")
```

### 3. Analyze Activation Barrier

```python
barrier = workflow.analyze_activation_barrier(
    reactant_file="reactant.log",
    transition_state_file="ts.log",
    temperature=373.15
)

print(f"ΔG‡ = {barrier['ΔG‡']:.2f} kcal/mol")
print(f"k = {barrier['k']:.2e} s⁻¹")
```

### 4. Full Mechanism Analysis

```python
mechanism = workflow.analyze_multi_step_mechanism(
    reactant_files=["reactant.log"],
    intermediate_files=["int1.log", "int2.log"],
    transition_state_files=["ts1.log", "ts2.log"],
    product_files=["product.log"],
    temperature=298.15
)

# Generate energy diagram
workflow.generate_mechanism_diagram(
    mechanism,
    title="CO2 Hydrogenation Mechanism",
    save_path="mechanism.png"
)
```

### 5. Via Skill Interface

```bash
# Parse outputs
python analyze.py --action parse --software gaussian --output_files reactant.log product.log

# Calculate thermodynamics
python analyze.py --action thermodynamics --software gaussian \
  --reaction_type reaction_energy \
  --reactant_files reactant.log \
  --product_files product.log \
  --temperature 298.15

# Full analysis with diagram
python analyze.py --action full_analysis --software gaussian \
  --reaction_type multi_step \
  --reactant_files reactant.log \
  --intermediate_files int1.log int2.log \
  --transition_state_files ts1.log ts2.log \
  --product_files product.log \
  --diagram_title "Reaction Mechanism" \
  --project_name "my-project"
```

## Output Files

### Parsed Data (JSON)
```json
{
  "energies": {
    "electronic_energy": -123.456789,
    "zero_point_energy": 0.123456,
    "gibbs_free_energy": -123.345678
  },
  "geometry": [...],
  "frequencies": [...],
  "thermochemistry": {...}
}
```

### Thermodynamic Results
```
=== Reaction Thermodynamics ===
ΔE = -15.3 kcal/mol
ΔE+ZPE = -14.8 kcal/mol
ΔH = -15.1 kcal/mol
ΔG = -12.4 kcal/mol
ΔS = -9.2 cal/(mol·K)
K_eq = 3.45e+09
```

### Obsidian Report
```markdown
---
type: computational-analysis
software: gaussian
reaction_type: multi_step
temperature: 298.15
date: 2026-04-19
---

# CO2 Hydrogenation Mechanism

## Reaction Pathway

Reactant → TS1 → Intermediate1 → TS2 → Product

## Thermodynamics

| Step | ΔG (kcal/mol) | ΔH (kcal/mol) | ΔS (cal/mol·K) |
|------|---------------|---------------|----------------|
| Overall | -12.4 | -15.1 | -9.2 |

## Energy Diagram

![mechanism](./mechanism.png)

## Related Notes
- [[Materials/catalyst-name]]
- [[Reactions/experimental-results]]
```

## Thermodynamic Equations

### Reaction Energy
```
ΔG = G(products) - G(reactants)
ΔH = H(products) - H(reactants)
ΔS = S(products) - S(reactants)
```

### Equilibrium Constant
```
ΔG = -RT ln(K)
K = exp(-ΔG / RT)
```

### Rate Constant (Eyring Equation)
```
k = (κ * kB * T / h) * exp(-ΔG‡ / RT)
```

### Arrhenius Equation
```
k = A * exp(-Ea / RT)
ln(k) = ln(A) - Ea / (RT)
```

## Energy Diagram Types

### 1. Reaction Coordinate Diagram
- Linear pathway with energy levels
- Transition states marked with dashed lines
- Energy values displayed

### 2. Multi-Pathway Comparison
- Compare different reaction routes
- Identify lowest-energy pathway
- Visualize selectivity

### 3. Potential Energy Surface
- 2D contour plot
- Reaction coordinate vs. energy
- Identify saddle points

## File Structure

```
computational-workflow/
├── skill.json              # Skill metadata and parameters
├── analyze.py              # Main orchestration script
├── gaussian_parser.py      # Gaussian output parser
├── orca_parser.py          # ORCA output parser
├── vasp_parser.py          # VASP output parser
├── thermodynamic_calculator.py  # Thermodynamic calculations
├── energy_diagram.py       # Energy diagram generator
└── README.md               # This file
```

## Dependencies

```bash
pip install numpy scipy matplotlib pandas
```

## Integration with Other Skills

- **catalysis-performance**: Compare computational predictions with experimental results
- **characterization-analysis**: Correlate DFT structures with XRD/XPS data
- **materials-literature**: Find computational benchmarks from literature
- **scientific-writing**: Auto-generate Methods and Results sections

## Common Workflows

### Workflow 1: Single Reaction Analysis
1. Optimize reactant and product geometries
2. Run frequency calculations
3. Parse outputs with `computational-workflow`
4. Calculate ΔG, ΔH, ΔS
5. Generate energy diagram
6. Save to Obsidian

### Workflow 2: Transition State Search
1. Optimize reactant geometry
2. Perform transition state search
3. Verify single imaginary frequency
4. Run IRC to confirm connectivity
5. Calculate activation barrier
6. Estimate rate constant

### Workflow 3: Mechanism Comparison
1. Calculate multiple reaction pathways
2. Compare activation barriers
3. Identify rate-determining step
4. Generate multi-pathway diagram
5. Predict selectivity

## Troubleshooting

### Issue: Parser fails to extract energies
- **Solution**: Check convergence in output file
- Gaussian: Look for "Normal termination"
- ORCA: Check "ORCA TERMINATED NORMALLY"
- VASP: Verify "reached required accuracy"

### Issue: Imaginary frequencies in reactant/product
- **Solution**: Re-optimize geometry with tighter convergence criteria
- Check for very small imaginary frequencies (<50 cm⁻¹) - may be numerical noise

### Issue: Large ΔS values
- **Solution**: Verify temperature consistency across calculations
- Check for changes in molecular degrees of freedom (e.g., dissociation)

### Issue: Energy diagram looks incorrect
- **Solution**: Verify all calculations use same level of theory
- Check that all structures are at stationary points (no imaginary frequencies except TS)

## Best Practices

1. **Consistency**: Use same level of theory, basis set, and functional for all structures
2. **Convergence**: Verify SCF and geometry convergence for all calculations
3. **Frequency Calculations**: Always run frequency calculations for thermochemistry
4. **Temperature**: Use experimental temperature for thermodynamic corrections
5. **Solvation**: Include solvent effects if reaction occurs in solution
6. **Dispersion**: Use dispersion-corrected functionals for non-covalent interactions
7. **Basis Set**: Use appropriate basis set size (at least double-ζ with polarization)

## References

- Gaussian User's Guide: https://gaussian.com/man/
- ORCA Manual: https://www.faccts.de/docs/orca/
- VASP Wiki: https://www.vasp.at/wiki/
- Computational Chemistry Comparison and Benchmark Database: https://cccbdb.nist.gov/

## Citation

If you use this skill in your research, please cite:
```
Materials Research Assistant - Computational Workflow Skill
https://github.com/your-repo/materials-research-assistant
```
