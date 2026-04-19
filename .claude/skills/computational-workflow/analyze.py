"""
Computational Workflow Skill - Main Orchestration Script
Analyzes DFT calculations, calculates thermodynamics, and generates energy diagrams
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import parsers
from gaussian_parser import GaussianParser
from orca_parser import ORCAParser
from vasp_parser import VASPParser

# Import analysis modules
from thermodynamic_calculator import ThermodynamicCalculator, ThermodynamicData
from energy_diagram import EnergyDiagramGenerator, EnergyLevel


class ComputationalWorkflow:
    """Main orchestration class for computational chemistry workflows"""

    def __init__(self, software: str = "gaussian", energy_unit: str = "hartree"):
        """
        Initialize workflow

        Args:
            software: DFT software (gaussian, orca, vasp)
            energy_unit: Energy unit (hartree or eV)
        """
        self.software = software.lower()
        self.energy_unit = energy_unit

        # Map software name to parser class (instantiated per-file in parse_output_files)
        self._parser_classes = {
            "gaussian": GaussianParser,
            "orca": ORCAParser,
            "vasp": VASPParser,
        }
        if self.software not in self._parser_classes:
            raise ValueError(f"Unsupported software: {software}")

        # Initialize calculator and diagram generator
        self.thermo_calc = ThermodynamicCalculator(energy_unit=energy_unit)
        self.diagram_gen = EnergyDiagramGenerator()

    def parse_output_files(self, file_paths: List[str]) -> Dict[str, Dict]:
        """
        Parse multiple DFT output files

        Args:
            file_paths: List of output file paths

        Returns:
            Dictionary mapping file paths to parsed data
        """
        parsed_data = {}
        parser_cls = self._parser_classes[self.software]

        for file_path in file_paths:
            if not os.path.exists(file_path):
                print(f"Warning: File not found: {file_path}")
                continue

            try:
                if self.software == "vasp":
                    parser = parser_cls(outcar_path=file_path)
                else:
                    parser = parser_cls(file_path)
                data = parser.parse_all()
                parsed_data[file_path] = data
                print(f"Parsed: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"Error parsing {file_path}: {str(e)}")

        return parsed_data

    def extract_thermodynamic_data(
        self,
        parsed_data: Dict,
        temperature: float = 298.15
    ) -> ThermodynamicData:
        """
        Extract ThermodynamicData from parsed output

        Args:
            parsed_data: Parsed DFT output dictionary
            temperature: Temperature (K)

        Returns:
            ThermodynamicData object
        """
        energies = parsed_data.get("energies", {})
        thermo = parsed_data.get("thermochemistry", {})

        # Electronic energy — try all parser-specific key names
        E_elec = (
            energies.get("SCF_hartree") or          # Gaussian / ORCA
            energies.get("final_energy_hartree") or  # ORCA final SP
            energies.get("free_energy_hartree") or   # VASP (eV converted)
            energies.get("free_energy_eV", 0.0)      # VASP raw eV
        ) or 0.0

        ZPE = (
            energies.get("ZPE_hartree") or           # Gaussian
            thermo.get("ZPE_hartree") or             # ORCA
            0.0
        )

        # Thermal corrections: use total H/G if available, else individual corrections
        H_total = energies.get("H_total_hartree") or thermo.get("H_total_hartree")
        G_total = energies.get("G_total_hartree") or thermo.get("G_total_hartree")

        if H_total is not None:
            H_corr = H_total - E_elec
        else:
            H_corr = energies.get("thermal_correction_H_hartree") or thermo.get("enthalpy_correction", 0.0)

        if G_total is not None:
            G_corr = G_total - E_elec
        else:
            G_corr = energies.get("thermal_correction_G_hartree") or thermo.get("gibbs_correction", 0.0)

        # Entropy in cal/(mol·K)
        S = (
            thermo.get("entropy_cal_mol_K") or   # Gaussian
            thermo.get("entropy", 0.0)
        ) or 0.0

        return ThermodynamicData(
            E_elec=E_elec,
            ZPE=ZPE,
            H_corr=H_corr,
            G_corr=G_corr,
            S=S,
            temperature=temperature,
            energy_unit=self.energy_unit
        )

    def analyze_reaction_energy(
        self,
        reactant_files: List[str],
        product_files: List[str],
        temperature: float = 298.15
    ) -> Dict[str, Any]:
        """
        Analyze reaction thermodynamics

        Args:
            reactant_files: Reactant output files
            product_files: Product output files
            temperature: Temperature (K)

        Returns:
            Dictionary with thermodynamic results
        """
        print("\n=== Parsing Reactants ===")
        reactant_data = self.parse_output_files(reactant_files)

        print("\n=== Parsing Products ===")
        product_data = self.parse_output_files(product_files)

        # Extract thermodynamic data
        reactants = [self.extract_thermodynamic_data(data, temperature)
                     for data in reactant_data.values()]
        products = [self.extract_thermodynamic_data(data, temperature)
                    for data in product_data.values()]

        # Calculate reaction thermodynamics
        print("\n=== Calculating Thermodynamics ===")
        results = self.thermo_calc.calculate_reaction_energy(
            reactants, products, temperature
        )

        # Calculate equilibrium constant
        results["K_eq"] = self.thermo_calc.calculate_equilibrium_constant(
            results["ΔG"], temperature
        )

        return results

    def analyze_activation_barrier(
        self,
        reactant_file: str,
        transition_state_file: str,
        temperature: float = 298.15
    ) -> Dict[str, Any]:
        """
        Analyze activation barrier

        Args:
            reactant_file: Reactant output file
            transition_state_file: Transition state output file
            temperature: Temperature (K)

        Returns:
            Dictionary with activation parameters
        """
        print("\n=== Parsing Reactant ===")
        reactant_data = self.parse_output_files([reactant_file])

        print("\n=== Parsing Transition State ===")
        ts_data = self.parse_output_files([transition_state_file])

        # Extract thermodynamic data
        reactant = self.extract_thermodynamic_data(
            list(reactant_data.values())[0], temperature
        )
        ts = self.extract_thermodynamic_data(
            list(ts_data.values())[0], temperature
        )

        # Check for imaginary frequency in TS
        ts_parsed = list(ts_data.values())[0]
        frequencies = ts_parsed.get("frequencies", {})
        imaginary_freqs = frequencies.get("imaginary_frequencies", [])

        if not imaginary_freqs:
            print("[WARN] Warning: No imaginary frequency found in transition state!")
        else:
            print(f"[OK] Imaginary frequency: {imaginary_freqs[0]:.2f} cm⁻¹")

        # Calculate activation parameters
        print("\n=== Calculating Activation Parameters ===")
        results = self.thermo_calc.calculate_activation_energy(
            reactant, ts, temperature
        )

        # Calculate rate constant
        results["k_rate"] = self.thermo_calc.calculate_rate_constant(
            results["ΔG‡"], temperature
        )

        return results

    def analyze_multi_step_mechanism(
        self,
        reactant_files: List[str],
        intermediate_files: List[List[str]],
        transition_state_files: List[str],
        product_files: List[str],
        temperature: float = 298.15
    ) -> Dict[str, Any]:
        """
        Analyze multi-step reaction mechanism

        Args:
            reactant_files: Reactant output files
            intermediate_files: List of intermediate file lists for each step
            transition_state_files: Transition state files for each step
            product_files: Product output files
            temperature: Temperature (K)

        Returns:
            Dictionary with mechanism analysis
        """
        print("\n=== Analyzing Multi-Step Mechanism ===")

        # Parse all files
        all_files = reactant_files + product_files + transition_state_files
        for int_files in intermediate_files:
            all_files.extend(int_files)

        parsed_data = self.parse_output_files(all_files)

        # Build energy profile
        energy_levels = []
        x_pos = 0

        # Reactants
        reactant_data_list = [parsed_data[f] for f in reactant_files if f in parsed_data]
        reactant_thermo = [self.extract_thermodynamic_data(d, temperature)
                          for d in reactant_data_list]
        reactant_energy = sum(r.E_elec + r.G_corr for r in reactant_thermo)
        reactant_energy_kcal = reactant_energy * self.thermo_calc.conversion_factor

        energy_levels.append(EnergyLevel(
            name="Reactants",
            energy=0.0,  # Reference
            x_position=x_pos,
            label="R",
            color="blue"
        ))
        x_pos += 1

        # Process each step
        for i, (ts_file, int_files) in enumerate(zip(transition_state_files, intermediate_files)):
            # Transition state
            if ts_file in parsed_data:
                ts_thermo = self.extract_thermodynamic_data(parsed_data[ts_file], temperature)
                ts_energy = (ts_thermo.E_elec + ts_thermo.G_corr) * self.thermo_calc.conversion_factor
                rel_energy = ts_energy - reactant_energy_kcal

                energy_levels.append(EnergyLevel(
                    name=f"TS{i+1}",
                    energy=rel_energy,
                    x_position=x_pos,
                    label=f"TS{i+1}",
                    color="red",
                    is_transition_state=True
                ))
                x_pos += 1

            # Intermediate
            if int_files:
                int_data_list = [parsed_data[f] for f in int_files if f in parsed_data]
                int_thermo = [self.extract_thermodynamic_data(d, temperature)
                             for d in int_data_list]
                int_energy = sum(i.E_elec + i.G_corr for i in int_thermo)
                int_energy_kcal = int_energy * self.thermo_calc.conversion_factor
                rel_energy = int_energy_kcal - reactant_energy_kcal

                energy_levels.append(EnergyLevel(
                    name=f"Int{i+1}",
                    energy=rel_energy,
                    x_position=x_pos,
                    label=f"I{i+1}",
                    color="green"
                ))
                x_pos += 1

        # Products
        product_data_list = [parsed_data[f] for f in product_files if f in parsed_data]
        product_thermo = [self.extract_thermodynamic_data(d, temperature)
                         for d in product_data_list]
        product_energy = sum(p.E_elec + p.G_corr for p in product_thermo)
        product_energy_kcal = product_energy * self.thermo_calc.conversion_factor
        rel_energy = product_energy_kcal - reactant_energy_kcal

        energy_levels.append(EnergyLevel(
            name="Products",
            energy=rel_energy,
            x_position=x_pos,
            label="P",
            color="blue"
        ))

        # Calculate overall thermodynamics
        overall_thermo = self.thermo_calc.calculate_reaction_energy(
            reactant_thermo, product_thermo, temperature
        )

        # Find rate-determining step (highest barrier)
        ts_energies = [level.energy for level in energy_levels if level.is_transition_state]
        if ts_energies:
            rds_barrier = max(ts_energies)
            rds_index = [level.energy for level in energy_levels].index(rds_barrier)
            rds_name = energy_levels[rds_index].name
        else:
            rds_barrier = None
            rds_name = None

        return {
            "energy_levels": energy_levels,
            "overall_thermodynamics": overall_thermo,
            "rate_determining_step": rds_name,
            "rds_barrier": rds_barrier,
            "temperature": temperature
        }

    def generate_energy_diagram(
        self,
        energy_levels: List[EnergyLevel],
        title: str = "Reaction Coordinate Diagram",
        save_path: Optional[str] = None
    ) -> str:
        """
        Generate energy diagram

        Args:
            energy_levels: List of EnergyLevel objects
            title: Diagram title
            save_path: Path to save figure

        Returns:
            Path to saved figure
        """
        print("\n=== Generating Energy Diagram ===")

        fig = self.diagram_gen.create_reaction_coordinate_diagram(
            energy_levels=energy_levels,
            title=title,
            show_values=True,
            save_path=save_path
        )

        if save_path:
            print(f"[OK] Energy diagram saved: {save_path}")

        return save_path

    def generate_obsidian_report(
        self,
        results: Dict[str, Any],
        project_name: Optional[str],
        output_path: str,
        analysis_type: str
    ):
        """
        Generate Obsidian-compatible markdown report

        Args:
            results: Analysis results dictionary
            project_name: Project name for backlinks
            output_path: Path to save report
            analysis_type: Type of analysis performed
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""---
type: computational-analysis
analysis_type: {analysis_type}
software: {self.software}
temperature: {results.get('temperature', 298.15)} K
date: {timestamp}
project: {project_name or 'N/A'}
tags: [DFT, computational-chemistry, mechanism]
---

# Computational Analysis Report

## Analysis Details
- **Software**: {self.software.upper()}
- **Analysis Type**: {analysis_type}
- **Temperature**: {results.get('temperature', 298.15)} K
- **Date**: {timestamp}

"""

        if analysis_type == "reaction_energy":
            report += f"""## Reaction Thermodynamics

| Property | Value | Unit |
|----------|-------|------|
| ΔE | {results.get('ΔE', 0):.2f} | kcal/mol |
| ΔE+ZPE | {results.get('ΔE+ZPE', 0):.2f} | kcal/mol |
| ΔH | {results.get('ΔH', 0):.2f} | kcal/mol |
| ΔG | {results.get('ΔG', 0):.2f} | kcal/mol |
| ΔS | {results.get('ΔS', 0):.2f} | cal/(mol·K) |
| K_eq | {results.get('K_eq', 0):.2e} | - |

### Interpretation
- **Thermodynamic favorability**: {"Favorable (ΔG < 0)" if results.get('ΔG', 0) < 0 else "Unfavorable (ΔG > 0)"}
- **Enthalpy change**: {"Exothermic (ΔH < 0)" if results.get('ΔH', 0) < 0 else "Endothermic (ΔH > 0)"}
- **Entropy change**: {"Entropy increases (ΔS > 0)" if results.get('ΔS', 0) > 0 else "Entropy decreases (ΔS < 0)"}
"""

        elif analysis_type == "activation_barrier":
            report += f"""## Activation Parameters

| Property | Value | Unit |
|----------|-------|------|
| Ea | {results.get('Ea', 0):.2f} | kcal/mol |
| Ea+ZPE | {results.get('Ea+ZPE', 0):.2f} | kcal/mol |
| ΔH‡ | {results.get('ΔH‡', 0):.2f} | kcal/mol |
| ΔG‡ | {results.get('ΔG‡', 0):.2f} | kcal/mol |
| ΔS‡ | {results.get('ΔS‡', 0):.2f} | cal/(mol·K) |
| k_rate | {results.get('k_rate', 0):.2e} | s⁻¹ |

### Interpretation
- **Barrier height**: {results.get('ΔG‡', 0):.2f} kcal/mol
- **Rate constant**: {results.get('k_rate', 0):.2e} s⁻¹ at {results.get('temperature', 298.15)} K
"""

        elif analysis_type == "multi_step":
            overall = results.get('overall_thermodynamics', {})
            report += f"""## Multi-Step Mechanism Analysis

### Overall Reaction Thermodynamics
| Property | Value | Unit |
|----------|-------|------|
| ΔG | {overall.get('ΔG', 0):.2f} | kcal/mol |
| ΔH | {overall.get('ΔH', 0):.2f} | kcal/mol |
| ΔS | {overall.get('ΔS', 0):.2f} | cal/(mol·K) |

### Rate-Determining Step
- **Step**: {results.get('rate_determining_step', 'N/A')}
- **Barrier**: {results.get('rds_barrier', 0):.2f} kcal/mol

### Energy Profile
See energy diagram for complete reaction coordinate.
"""

        report += f"""
## Files Analyzed
- Software: {self.software.upper()}
- Energy unit: {self.energy_unit}

## Notes
Add your observations and interpretations here.

## Related
"""

        if project_name:
            report += f"- [[{project_name}/00-Hub|Project Hub]]\n"
            report += f"- [[{project_name}/Computational/|Computational Directory]]\n"

        # Write report
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"[OK] Report saved: {output_path}")


def main():
    """Main entry point for computational workflow skill"""

    # Parse command-line arguments or JSON input
    if len(sys.argv) > 1:
        # Load parameters from JSON file or string
        params = json.loads(sys.argv[1])
    else:
        print("Error: No parameters provided")
        sys.exit(1)

    # Extract parameters
    action = params.get("action")
    software = params.get("software", "gaussian")
    energy_unit = params.get("energy_unit", "hartree")
    temperature = params.get("temperature", 298.15)
    output_dir = params.get("output_dir", ".")
    project_name = params.get("project_name")

    # Initialize workflow
    workflow = ComputationalWorkflow(software=software, energy_unit=energy_unit)

    # Execute action
    if action == "parse":
        output_files = params.get("output_files", [])
        results = workflow.parse_output_files(output_files)
        print(json.dumps(results, indent=2, default=str))

    elif action == "thermodynamics":
        reaction_type = params.get("reaction_type", "reaction_energy")

        if reaction_type == "reaction_energy":
            reactant_files = params.get("reactant_files", [])
            product_files = params.get("product_files", [])
            results = workflow.analyze_reaction_energy(
                reactant_files, product_files, temperature
            )

            # Generate report
            report_path = os.path.join(output_dir, "reaction_thermodynamics.md")
            workflow.generate_obsidian_report(
                results, project_name, report_path, "reaction_energy"
            )

            print("\n=== Results ===")
            print(json.dumps(results, indent=2))

        elif reaction_type == "activation_barrier":
            reactant_file = params.get("reactant_files", [])[0]
            ts_file = params.get("transition_state_files", [])[0]
            results = workflow.analyze_activation_barrier(
                reactant_file, ts_file, temperature
            )

            # Generate report
            report_path = os.path.join(output_dir, "activation_barrier.md")
            workflow.generate_obsidian_report(
                results, project_name, report_path, "activation_barrier"
            )

            print("\n=== Results ===")
            print(json.dumps(results, indent=2))

    elif action == "energy_diagram":
        # This would typically be called after mechanism analysis
        print("Use 'full_analysis' action for complete mechanism with energy diagram")

    elif action == "full_analysis":
        reaction_type = params.get("reaction_type", "multi_step")

        if reaction_type == "multi_step":
            reactant_files = params.get("reactant_files", [])
            product_files = params.get("product_files", [])
            ts_files = params.get("transition_state_files", [])
            int_files_list = params.get("intermediate_files", [])

            # Convert intermediate files to list of lists if needed
            if int_files_list and not isinstance(int_files_list[0], list):
                int_files_list = [[f] for f in int_files_list]

            results = workflow.analyze_multi_step_mechanism(
                reactant_files, int_files_list, ts_files, product_files, temperature
            )

            # Generate energy diagram
            diagram_title = params.get("diagram_title", "Reaction Coordinate Diagram")
            diagram_path = os.path.join(output_dir, "energy_diagram.png")
            workflow.generate_energy_diagram(
                results["energy_levels"], diagram_title, diagram_path
            )

            # Generate report
            report_path = os.path.join(output_dir, "mechanism_analysis.md")
            workflow.generate_obsidian_report(
                results, project_name, report_path, "multi_step"
            )

            print("\n=== Results ===")
            print(f"Rate-determining step: {results['rate_determining_step']}")
            print(f"RDS barrier: {results['rds_barrier']:.2f} kcal/mol")
            print(f"Overall ΔG: {results['overall_thermodynamics']['ΔG']:.2f} kcal/mol")

    else:
        print(f"Error: Unknown action '{action}'")
        sys.exit(1)


if __name__ == "__main__":
    main()
