# Materials Research Assistant - Quick Start Guide

## Installation

1. **Copy project to your knowledge base**:
```bash
cp -r materials-research-assistant /path/to/your/knowledge-base/
```

2. **Install Python dependencies**:
```bash
pip install numpy pandas matplotlib seaborn scikit-learn scipy pymatgen rdkit
```

3. **Configure Zotero** (optional):
   - Get API key from https://www.zotero.org/settings/keys
   - Set environment variable: `export ZOTERO_API_KEY=your_key_here`

## Usage Examples

### Example 1: Start a New Catalysis Project

```bash
# Initialize project
/materials-init

# Provide details:
# - Project name: CO2-hydrogenation-Ni-catalyst
# - Research focus: Develop Ni-based catalysts for CO2 hydrogenation to methanol
# - PI name: Your Name
# - Create Zotero collections: Yes
```

This creates:
- `Research/CO2-hydrogenation-Ni-catalyst/` directory structure
- `00-Hub.md` project overview
- Zotero collections (if enabled)
- All subdirectories for data organization

### Example 2: Literature Search

```
Use materials-literature skill to search for "nickel catalysts CO2 hydrogenation" 
and import top 10 papers to Zotero
```

The system will:
- Search PubMed, arXiv, Semantic Scholar
- Check ChEMBL for Ni compound data
- Import papers to Zotero "Catalysts" collection
- Create notes in `Research/CO2-hydrogenation-Ni-catalyst/Papers/`

### Example 3: Document Synthesis

```bash
/synthesis-log

# Provide details:
# - Material: Ni/Al2O3 catalyst
# - Method: Wet impregnation
# - Ni loading: 10 wt%
# - Support: γ-Al2O3
```

Creates synthesis record in `Synthesis/Protocols/` with:
- Reagent list with safety data
- Step-by-step procedure
- Yield and observations
- Links to characterization

### Example 4: Analyze XRD Data

```bash
/characterization

# Select: XRD
# File: path/to/xrd_data.xy
# Material ID: Ni-Al2O3-10wt-batch1
```

The system will:
- Identify peaks and phases
- Calculate crystallite size (Scherrer equation)
- Generate XRD pattern plot
- Save to `Characterization/XRD/`
- Create Obsidian note with backlinks

### Example 5: Evaluate Catalysis Performance

```bash
/catalysis-results

# Provide:
# - Data file: catalysis_data.csv
# - Material: Ni-Al2O3-10wt-batch1
# - Reaction: CO2 + H2 → CH3OH
# - Temperature: 250°C, Pressure: 30 bar
```

Calculates:
- Conversion, selectivity, yield
- TOF (turnover frequency)
- Statistical analysis (95% CI)
- Generates performance plots
- Compares with literature from Zotero

### Example 6: Parse DFT Results

```bash
/dft-analysis

# Provide:
# - Output file: co2_hydrogenation.log (Gaussian)
# - Analysis type: Energy profile
# - System: CO2 hydrogenation on Ni(111)
```

Extracts:
- Reaction energies (ΔE, ΔG, ΔH)
- Transition state energies
- Generates energy diagram
- Saves to `Computational/DFT/`

### Example 7: Generate Manuscript

```bash
/manuscript-draft

# Provide:
# - Project: CO2-hydrogenation-Ni-catalyst
# - Journal: ACS Catalysis
# - Sections: Full manuscript (IMRAD)
# - Citation style: ACS
```

Generates:
- Introduction (from literature review)
- Methods (from synthesis protocols)
- Results (from characterization + catalysis data)
- Discussion (with literature comparison)
- Figures and tables
- References from Zotero

## Obsidian Integration

### Linking Notes

```markdown
# In a material note
Synthesis: [[Synthesis/Protocols/Ni-Al2O3-synthesis]]
XRD: [[Characterization/XRD/Ni-Al2O3-XRD]]
Performance: [[Reactions/Ni-Al2O3-performance]]
```

### Daily Lab Notebook

Create daily notes in `Daily/`:
```markdown
# 2026-04-19

## Experiments
- Synthesized Ni-Al2O3 batch 3 with 15 wt% loading
- XRD shows Ni peaks at 44.5°, 51.8°

## Observations
- Higher loading → larger Ni particles
- Need to optimize calcination temperature

## Next Steps
- [ ] BET analysis for batch 3
- [ ] Test catalytic activity at 250°C
```

### Graph View

Obsidian's graph view shows connections between:
- Materials ↔ Synthesis protocols
- Materials ↔ Characterization data
- Materials ↔ Catalysis results
- Papers ↔ Experimental results

## Tips

1. **Use templates**: Copy from `Research/templates/` for consistent formatting
2. **Tag consistently**: Use tags like #catalyst, #XRD, #DFT for easy filtering
3. **Link liberally**: Create backlinks between related notes
4. **Update 00-Hub.md**: Keep project overview current
5. **Sync Zotero**: Regularly sync notes between Zotero and Obsidian

## Troubleshooting

**MCP tools not working?**
- Check `.vscode/mcp.json` configuration
- Verify MCP servers are installed

**Zotero import failing?**
- Verify `ZOTERO_API_KEY` is set
- Check Zotero desktop app is running

**Python scripts failing?**
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Check Python version ≥ 3.8

## Next Steps

After Phase 1 setup, we'll implement:
- Phase 2: Characterization analysis skills (XRD, BET, XPS, electrochemistry)
- Phase 3: Catalysis performance evaluation
- Phase 4: Computational workflow (DFT parsing)
- Phase 5: Synthesis protocol documentation
- Phase 6: Autonomous agents
- Phase 7: Scientific writing integration
