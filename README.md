# Materials Research Assistant

A comprehensive research workflow system for materials science, chemistry, and catalysis research, inspired by [claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar).

## Overview

This project provides an integrated environment for materials research with:
- **Literature management** via Zotero and ai4scholar MCP tools
- **Obsidian knowledge base** with bidirectional linking
- **Automated data analysis** for characterization and catalysis
- **Computational workflow** support (DFT, MD)
- **Scientific writing** assistance with citation management

## Features

### 🔬 Research Workflows

- **Literature Review**: Multi-database search (PubMed, arXiv, Semantic Scholar, ChEMBL) with auto-import to Zotero
- **Characterization Analysis**: XRD, BET, TEM, XPS, electrochemistry with automated plotting
- **Catalysis Evaluation**: Activity, selectivity, stability, TOF calculations with statistical analysis
- **Computational Chemistry**: DFT parsing (Gaussian, ORCA, VASP), energy diagrams, mechanism analysis
- **Synthesis Documentation**: Protocol tracking with safety data and batch records
- **Manuscript Preparation**: Auto-generation from Obsidian notes with Zotero citations

### 🛠️ Skills

- `materials-init` - Initialize new research projects
- `characterization-analysis` - Analyze XRD, BET, TEM, XPS, electrochemistry data
- `catalysis-performance` - Calculate conversion, selectivity, TOF, stability
- `computational-workflow` - Parse DFT outputs, generate energy diagrams
- `synthesis-protocol` - Document synthesis procedures
- `materials-literature` - Domain-specific literature search
- `materials-paper-review` - Manuscript self-review

### 🤖 Agents

- `materials-reviewer` - Autonomous literature review
- `catalyst-optimizer` - Performance optimization recommendations
- `characterization-expert` - Multi-technique interpretation

### ⚡ Commands

- `/materials-init` - Initialize new project
- `/characterization` - Analyze characterization data
- `/catalysis-results` - Evaluate catalysis performance
- `/dft-analysis` - Parse computational results
- `/synthesis-log` - Document synthesis
- `/manuscript-draft` - Generate manuscript
- `/paper-review` - Review manuscript

## Installation

### Prerequisites

- Claude Code CLI or Desktop App
- Python 3.8+
- Zotero (optional but recommended)
- Obsidian (optional but recommended)

### Setup

1. **Clone or copy this project structure**:
```bash
cd your-knowledge-base
cp -r materials-research-assistant .claude/
```

2. **Configure MCP servers** (if not already configured):

Add to your `.vscode/mcp.json` or Claude Code settings:
```json
{
  "mcpServers": {
    "ai4scholar": {
      "command": "npx",
      "args": ["-y", "@ai4scholar/mcp-server"]
    },
    "mineru": {
      "command": "python",
      "args": ["-m", "mineru_mcp"]
    }
  }
}
```

3. **Install Python dependencies**:
```bash
pip install numpy pandas matplotlib seaborn scikit-learn scipy pymatgen rdkit
```

4. **Configure Zotero** (optional):
   - Install Zotero desktop application
   - Get API key from https://www.zotero.org/settings/keys
   - Set environment variable: `ZOTERO_API_KEY=your_key_here`

5. **Configure Obsidian** (optional):
   - Create or open your Obsidian vault
   - Point to the `Research/` directory in this project

## Quick Start

### 1. Initialize a New Project

```
/materials-init
```

Follow the prompts to create:
- Project directory structure
- Obsidian hub file (00-Hub.md)
- Zotero collections
- Project templates

### 2. Literature Review

Use the materials-literature skill to search for papers:
```
Search for papers on "CO2 hydrogenation catalysts" and import to Zotero
```

### 3. Document Synthesis

```
/synthesis-log
```

Record synthesis procedures, reagents, conditions, and batch information.

### 4. Analyze Characterization Data

```
/characterization
```

Analyze XRD, BET, TEM, XPS, or electrochemistry data with automated plotting.

### 5. Evaluate Catalysis Performance

```
/catalysis-results
```

Calculate conversion, selectivity, TOF, and stability with statistical analysis.

### 6. Computational Analysis

```
/dft-analysis
```

Parse DFT outputs and generate energy diagrams.

### 7. Write Manuscript

```
/manuscript-draft
```

Generate manuscript from Obsidian notes with Zotero citations.

## Project Structure

```
Research/{project-name}/
├── 00-Hub.md                 # Project overview
├── Materials/                # Catalyst materials
├── Characterization/         # XRD, BET, TEM, XPS data
│   ├── XRD/
│   ├── BET/
│   ├── TEM/
│   ├── XPS/
│   └── Electrochemistry/
├── Reactions/                # Catalysis experiments
│   ├── Results/
│   └── Conditions/
├── Synthesis/                # Synthesis protocols
│   ├── Protocols/
│   └── Batches/
├── Computational/            # DFT, MD simulations
│   ├── DFT/
│   └── MD/
├── Papers/                   # Literature notes
├── Writing/                  # Manuscripts
│   ├── Manuscripts/
│   └── Presentations/
└── Daily/                    # Lab notebook
```

## Integration

### Zotero

- Auto-creates collections for each project
- Imports papers with PDF attachments
- Syncs notes to Obsidian Papers/ directory
- Generates citation keys for manuscripts

### Obsidian

- Bidirectional linking between experiments, materials, and papers
- YAML frontmatter for metadata
- Daily notes for lab notebook
- Graph view for knowledge visualization

### MCP Tools

- **ai4scholar**: Literature search, PDF download, citations
- **ChEMBL**: Compound properties, bioactivity, ADMET
- **Consensus**: Research consensus
- **mineru**: High-quality PDF parsing

### Existing Skills

- **exploratory-data-analysis**: Format detection (200+ formats)
- **statistical-analysis**: Hypothesis testing, regression
- **matplotlib/seaborn**: Publication-quality plots
- **pymatgen**: Crystal structure analysis
- **rdkit**: Molecular structure analysis
- **scikit-learn**: Machine learning

## Examples

### Example 1: CO2 Hydrogenation Catalyst

```
1. /materials-init
   Project: CO2-hydrogenation-catalyst
   Focus: Develop efficient catalysts for CO2 to methanol

2. Search literature on "Cu/ZnO catalysts for CO2 hydrogenation"

3. /synthesis-log
   Material: Cu-ZnO-Al2O3
   Method: Co-precipitation

4. /characterization
   Type: XRD
   File: cu-zno-xrd.csv

5. /catalysis-results
   Data: co2-hydrogenation-results.xlsx

6. /dft-analysis
   File: co2-activation-gaussian.log

7. /manuscript-draft
   Journal: ACS Catalysis
```

## Contributing

This is a template project. Customize skills, agents, and templates for your specific research needs.

## License

MIT License

## Acknowledgments

Inspired by [claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) by Galaxy-Dawn.

## Support

For issues or questions:
- Check the documentation in each skill directory
- Review example workflows in `examples/`
- Consult the plan file at `.claude/plans/`
