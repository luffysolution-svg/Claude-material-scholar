#!/usr/bin/env python3
"""
Characterization Report Generator

Generates Obsidian-compatible markdown reports for characterization data with:
- Structured metadata (YAML frontmatter)
- Analysis results and interpretations
- Embedded plots
- Backlinks to materials and synthesis
"""

import os
from datetime import datetime
from pathlib import Path
import json


class CharacterizationReportGenerator:
    """Generator for characterization analysis reports."""

    def __init__(self, project_path, material_id):
        """
        Initialize report generator.

        Args:
            project_path: Path to Research project directory
            material_id: Material identifier
        """
        self.project_path = Path(project_path)
        self.material_id = material_id
        self.timestamp = datetime.now().strftime("%Y-%m-%d")

    def generate_xrd_report(self, analysis_results, plot_path, notes=""):
        """
        Generate XRD analysis report.

        Args:
            analysis_results: Dictionary from XRDAnalyzer
            plot_path: Path to XRD plot image
            notes: Additional notes

        Returns:
            Path to generated report
        """
        report_filename = f"{self.material_id}_XRD_{self.timestamp}.md"
        report_path = self.project_path / "Characterization" / "XRD" / report_filename

        # Ensure directory exists
        report_path.parent.mkdir(parents=True, exist_ok=True)

        # Extract key results
        peaks = analysis_results.get('peaks', {})
        phases = analysis_results.get('phases', [])
        crystallite_sizes = analysis_results.get('crystallite_sizes', {})

        # Generate markdown content
        content = f"""---
material_id: {self.material_id}
technique: XRD
date: {self.timestamp}
tags: [characterization, XRD, {self.material_id}]
---

# XRD Analysis: {self.material_id}

## Material

**Material**: [[Materials/{self.material_id}]]
**Analysis Date**: {self.timestamp}
**Technique**: X-ray Diffraction (XRD)

## Results

### Identified Peaks

| 2θ (°) | d-spacing (Å) | Relative Intensity | FWHM (°) |
|--------|---------------|-------------------|----------|
"""

        # Add peak data
        if 'peak_positions' in peaks:
            for i, pos in enumerate(peaks['peak_positions']):
                d_spacing = peaks.get('d_spacings', [None] * len(peaks['peak_positions']))[i]
                rel_int = peaks.get('relative_intensities', [None] * len(peaks['peak_positions']))[i]
                fwhm = peaks.get('peak_widths_fwhm', [None] * len(peaks['peak_positions']))[i]

                content += f"| {pos:.2f} | {d_spacing:.3f} | {rel_int:.2f} | {fwhm:.3f} |\n"

        content += "\n### Phase Identification\n\n"

        if phases:
            for phase in phases:
                confidence = phase.get('confidence', 0) * 100
                content += f"- **{phase['phase']}**: {confidence:.1f}% confidence ({phase['matched_peaks']}/{phase['total_peaks']} peaks matched)\n"
        else:
            content += "*No phases matched from database*\n"

        content += "\n### Crystallite Size\n\n"

        if crystallite_sizes:
            for peak_pos, size in crystallite_sizes.items():
                content += f"- Peak at {peak_pos}°: **{size:.1f} nm**\n"
        else:
            content += "*Crystallite size not calculated*\n"

        content += f"""

## XRD Pattern

![XRD Pattern]({os.path.basename(plot_path)})

## Interpretation

"""

        # Add automated interpretation
        if phases:
            main_phase = phases[0]['phase']
            content += f"The XRD pattern shows the presence of **{main_phase}** as the primary phase. "

        if crystallite_sizes:
            avg_size = sum(crystallite_sizes.values()) / len(crystallite_sizes)
            if avg_size < 10:
                content += f"The average crystallite size of {avg_size:.1f} nm indicates nanocrystalline material. "
            elif avg_size < 50:
                content += f"The average crystallite size of {avg_size:.1f} nm indicates fine crystalline material. "
            else:
                content += f"The average crystallite size of {avg_size:.1f} nm indicates well-crystallized material. "

        content += f"""

## Notes

{notes}

## Related Data

- Material: [[Materials/{self.material_id}]]
- Synthesis: [[Synthesis/Protocols/{self.material_id}_synthesis]]
- BET Analysis: [[Characterization/BET/{self.material_id}_BET]]
- Performance: [[Reactions/{self.material_id}_performance]]

## Raw Data

*XRD data file: `{self.material_id}_XRD_raw.xy`*
"""

        # Write report
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return report_path

    def generate_bet_report(self, analysis_results, plot_path, notes=""):
        """
        Generate BET analysis report.

        Args:
            analysis_results: Dictionary from BETAnalyzer
            plot_path: Path to BET plot image
            notes: Additional notes

        Returns:
            Path to generated report
        """
        report_filename = f"{self.material_id}_BET_{self.timestamp}.md"
        report_path = self.project_path / "Characterization" / "BET" / report_filename

        report_path.parent.mkdir(parents=True, exist_ok=True)

        bet_results = analysis_results.get('bet_results', {})
        isotherm_type = analysis_results.get('isotherm_type', 'Unknown')
        pore_volume = analysis_results.get('pore_volume', None)
        psd = analysis_results.get('pore_size_distribution', {})

        content = f"""---
material_id: {self.material_id}
technique: BET
date: {self.timestamp}
tags: [characterization, BET, surface-area, {self.material_id}]
---

# BET Analysis: {self.material_id}

## Material

**Material**: [[Materials/{self.material_id}]]
**Analysis Date**: {self.timestamp}
**Technique**: BET Surface Area Analysis

## Results

### Surface Area

- **BET Surface Area**: {bet_results.get('surface_area_m2_g', 'N/A'):.2f} m²/g
- **Monolayer Capacity**: {bet_results.get('monolayer_capacity', 'N/A'):.2f} cm³/g STP
- **BET Constant (C)**: {bet_results.get('BET_constant', 'N/A'):.2f}
- **R²**: {bet_results.get('r_squared', 'N/A'):.4f}

### Porosity

- **Isotherm Type**: {isotherm_type}
- **Total Pore Volume**: {pore_volume:.3f} cm³/g
- **Average Pore Diameter**: {psd.get('average_pore_diameter_nm', 'N/A'):.2f} nm

### Pore Size Distribution

"""

        if 'pore_classification' in psd:
            pore_class = psd['pore_classification']
            content += f"- **Micropores** (<2 nm): {pore_class.get('micropore_fraction', 0)*100:.1f}%\n"
            content += f"- **Mesopores** (2-50 nm): {pore_class.get('mesopore_fraction', 0)*100:.1f}%\n"
            content += f"- **Macropores** (>50 nm): {pore_class.get('macropore_fraction', 0)*100:.1f}%\n"

        content += f"""

## Isotherm Plot

![BET Isotherm]({os.path.basename(plot_path)})

## Interpretation

"""

        # Automated interpretation
        s_bet = bet_results.get('surface_area_m2_g', 0)
        if s_bet < 10:
            content += "The material has **low surface area**, typical of non-porous or dense materials. "
        elif s_bet < 100:
            content += "The material has **moderate surface area**, suitable for many catalytic applications. "
        elif s_bet < 500:
            content += "The material has **high surface area**, excellent for catalysis and adsorption. "
        else:
            content += "The material has **very high surface area**, characteristic of highly porous materials. "

        if 'Type I' in isotherm_type:
            content += "The Type I isotherm indicates **microporous** character with strong adsorbate-adsorbent interactions. "
        elif 'Type IV' in isotherm_type:
            content += "The Type IV isotherm indicates **mesoporous** character, ideal for catalytic applications. "

        content += f"""

## Notes

{notes}

## Related Data

- Material: [[Materials/{self.material_id}]]
- Synthesis: [[Synthesis/Protocols/{self.material_id}_synthesis]]
- XRD Analysis: [[Characterization/XRD/{self.material_id}_XRD]]
- Performance: [[Reactions/{self.material_id}_performance]]

## Raw Data

*BET data file: `{self.material_id}_BET_raw.csv`*
"""

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return report_path

    def generate_xps_report(self, analysis_results, plot_path, notes=""):
        """Generate XPS analysis report."""
        report_filename = f"{self.material_id}_XPS_{self.timestamp}.md"
        report_path = self.project_path / "Characterization" / "XPS" / report_filename

        report_path.parent.mkdir(parents=True, exist_ok=True)

        composition = analysis_results.get('composition', {})
        oxidation_states = analysis_results.get('oxidation_states', {})

        content = f"""---
material_id: {self.material_id}
technique: XPS
date: {self.timestamp}
tags: [characterization, XPS, surface-chemistry, {self.material_id}]
---

# XPS Analysis: {self.material_id}

## Material

**Material**: [[Materials/{self.material_id}]]
**Analysis Date**: {self.timestamp}
**Technique**: X-ray Photoelectron Spectroscopy (XPS)

## Results

### Elemental Composition

| Element | Atomic % | Binding Energy (eV) |
|---------|----------|---------------------|
"""

        for element, data in composition.items():
            at_percent = data.get('atomic_percent', 0)
            be = data.get('binding_energy', 0)
            content += f"| {element} | {at_percent:.2f} | {be:.1f} |\n"

        content += "\n### Oxidation States\n\n"

        for element, states in oxidation_states.items():
            content += f"**{element}**:\n"
            for state in states:
                content += f"- {state['oxidation_state']}: {state['percentage']:.1f}% (BE: {state['binding_energy']:.1f} eV)\n"

        content += f"""

## XPS Spectra

![XPS Spectra]({os.path.basename(plot_path)})

## Interpretation

{notes}

## Related Data

- Material: [[Materials/{self.material_id}]]
- XRD Analysis: [[Characterization/XRD/{self.material_id}_XRD]]
- Performance: [[Reactions/{self.material_id}_performance]]
"""

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return report_path

    def generate_electrochemistry_report(self, analysis_results, plot_path, notes=""):
        """Generate electrochemistry analysis report."""
        report_filename = f"{self.material_id}_Electrochemistry_{self.timestamp}.md"
        report_path = self.project_path / "Characterization" / "Electrochemistry" / report_filename

        report_path.parent.mkdir(parents=True, exist_ok=True)

        content = f"""---
material_id: {self.material_id}
technique: Electrochemistry
date: {self.timestamp}
tags: [characterization, electrochemistry, electrocatalysis, {self.material_id}]
---

# Electrochemistry Analysis: {self.material_id}

## Material

**Material**: [[Materials/{self.material_id}]]
**Analysis Date**: {self.timestamp}
**Technique**: Electrochemical Analysis

## Results

"""

        if 'cv_analysis' in analysis_results:
            cv = analysis_results['cv_analysis']
            content += f"""### Cyclic Voltammetry

- **Oxidation Peak**: {cv.get('oxidation_peak_potential_V', 'N/A')} V
- **Reduction Peak**: {cv.get('reduction_peak_potential_V', 'N/A')} V
- **Peak Separation**: {cv.get('peak_separation_V', 'N/A')} V
- **Reversibility**: {cv.get('reversibility', 'N/A')}

"""

        if 'tafel_analysis' in analysis_results:
            tafel = analysis_results['tafel_analysis']
            content += f"""### Tafel Analysis

- **Tafel Slope**: {tafel.get('tafel_slope_mV_dec', 'N/A'):.1f} mV/dec
- **Exchange Current Density**: {tafel.get('exchange_current_density', 'N/A'):.2e} mA/cm²
- **Overpotential @ 10 mA/cm²**: {tafel.get('overpotential_at_10mA_cm2', 'N/A'):.3f} V

"""

        if 'eis_analysis' in analysis_results:
            eis = analysis_results['eis_analysis']
            content += f"""### Electrochemical Impedance

- **Solution Resistance (Rs)**: {eis.get('solution_resistance', 'N/A'):.2f} Ω
- **Charge Transfer Resistance (Rct)**: {eis.get('charge_transfer_resistance', 'N/A'):.2f} Ω

"""

        content += f"""## Electrochemical Plots

![Electrochemistry]({os.path.basename(plot_path)})

## Interpretation

{notes}

## Related Data

- Material: [[Materials/{self.material_id}]]
- Performance: [[Reactions/{self.material_id}_performance]]
"""

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return report_path
