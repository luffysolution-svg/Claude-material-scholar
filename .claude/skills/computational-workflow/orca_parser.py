#!/usr/bin/env python3
"""
ORCA Output Parser

Parses ORCA output files (.out) to extract:
- Energies (SCF, final single point)
- Geometries (optimized structures)
- Frequencies (vibrational analysis)
- Thermodynamic properties
- Electronic properties
"""

import re
import numpy as np
from pathlib import Path


class ORCAParser:
    """Parser for ORCA output files."""

    def __init__(self, file_path):
        """
        Initialize ORCA parser.

        Args:
            file_path: Path to ORCA output file (.out)
        """
        self.file_path = Path(file_path)
        self.content = None
        self.results = {}

        if self.file_path.exists():
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                self.content = f.read()

    def parse_all(self):
        """Parse all available data from ORCA output."""
        if self.content is None:
            return {'error': 'File not loaded'}

        self.results['job_type'] = self.parse_job_type()
        self.results['energies'] = self.parse_energies()
        self.results['geometry'] = self.parse_geometry()
        self.results['frequencies'] = self.parse_frequencies()
        self.results['thermochemistry'] = self.parse_thermochemistry()
        self.results['convergence'] = self.check_convergence()

        return self.results

    def parse_job_type(self):
        """Determine job type."""
        job_types = []

        if 'Geometry Optimization Run' in self.content or 'OPTIMIZATION RUN' in self.content:
            job_types.append('optimization')
        if 'VIBRATIONAL FREQUENCIES' in self.content or 'FREQUENCY ANALYSIS' in self.content:
            job_types.append('frequency')
        if 'Single Point Calculation' in self.content:
            job_types.append('single_point')
        if 'IRC CALCULATION' in self.content:
            job_types.append('IRC')

        return job_types if job_types else ['unknown']

    def parse_energies(self):
        """Extract energies from ORCA output."""
        energies = {}

        # Final single point energy
        final_energy_pattern = r'FINAL SINGLE POINT ENERGY\s+([-\d.]+)'
        final_match = re.search(final_energy_pattern, self.content)
        if final_match:
            energies['final_energy_hartree'] = float(final_match.group(1))
            energies['final_energy_eV'] = float(final_match.group(1)) * 27.2114
            energies['final_energy_kcal_mol'] = float(final_match.group(1)) * 627.509

        # SCF energy (last occurrence)
        scf_pattern = r'Total Energy\s+:\s+([-\d.]+)\s+Eh'
        scf_matches = re.findall(scf_pattern, self.content)
        if scf_matches:
            energies['SCF_hartree'] = float(scf_matches[-1])

        # Dispersion correction
        disp_pattern = r'Dispersion correction\s+([-\d.]+)'
        disp_match = re.search(disp_pattern, self.content)
        if disp_match:
            energies['dispersion_correction_hartree'] = float(disp_match.group(1))

        return energies

    def parse_geometry(self):
        """Extract optimized geometry."""
        geometry = {}

        # Find CARTESIAN COORDINATES section
        pattern = r'CARTESIAN COORDINATES \(ANGSTROEM\)\s+-+\s+(.*?)\s+-{3,}'
        matches = re.findall(pattern, self.content, re.DOTALL)

        if matches:
            # Get last geometry (optimized)
            last_geom = matches[-1]

            atoms = []
            coordinates = []

            # Parse atom lines
            for line in last_geom.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        element = parts[0]
                        x = float(parts[1])
                        y = float(parts[2])
                        z = float(parts[3])

                        atoms.append(element)
                        coordinates.append([x, y, z])
                    except ValueError:
                        continue

            geometry['atoms'] = atoms
            geometry['coordinates'] = coordinates
            geometry['n_atoms'] = len(atoms)

        return geometry

    def parse_frequencies(self):
        """Extract vibrational frequencies."""
        frequencies = {}

        # Find VIBRATIONAL FREQUENCIES section
        freq_pattern = r'VIBRATIONAL FREQUENCIES\s+-+\s+(.*?)\s+-{3,}'
        freq_match = re.search(freq_pattern, self.content, re.DOTALL)

        if freq_match:
            freq_section = freq_match.group(1)

            freq_values = []
            intensities = []

            # Parse frequency lines
            for line in freq_section.split('\n'):
                # Format: "  0:         0.00 cm**-1"
                freq_line_pattern = r'\d+:\s+([-\d.]+)\s+cm\*\*-1'
                match = re.search(freq_line_pattern, line)
                if match:
                    freq = float(match.group(1))
                    freq_values.append(freq)

            frequencies['frequencies_cm-1'] = freq_values
            frequencies['n_frequencies'] = len(freq_values)

            # Identify imaginary frequencies (negative values)
            imaginary = [f for f in freq_values if f < 0]
            frequencies['imaginary_frequencies'] = imaginary
            frequencies['n_imaginary'] = len(imaginary)

        # Find IR SPECTRUM section for intensities
        ir_pattern = r'IR SPECTRUM\s+-+\s+(.*?)\s+-{3,}'
        ir_match = re.search(ir_pattern, self.content, re.DOTALL)

        if ir_match:
            ir_section = ir_match.group(1)
            intensities = []

            for line in ir_section.split('\n'):
                # Format: "  0:         0.00    0.000000"
                ir_line_pattern = r'\d+:\s+([-\d.]+)\s+([-\d.]+)'
                match = re.search(ir_line_pattern, line)
                if match:
                    intensity = float(match.group(2))
                    intensities.append(intensity)

            frequencies['IR_intensities'] = intensities

        return frequencies

    def parse_thermochemistry(self):
        """Extract thermodynamic properties."""
        thermo = {}

        # Find THERMOCHEMISTRY section
        thermo_pattern = r'THERMOCHEMISTRY_Energies(.*?)(?:-{3,}|$)'
        thermo_match = re.search(thermo_pattern, self.content, re.DOTALL)

        if thermo_match:
            thermo_section = thermo_match.group(1)

            # Zero point energy
            zpe_pattern = r'Zero point energy\s+\.\.\.\s+([-\d.]+)\s+Eh'
            zpe_match = re.search(zpe_pattern, thermo_section)
            if zpe_match:
                thermo['ZPE_hartree'] = float(zpe_match.group(1))

            # Total enthalpy
            h_pattern = r'Total Enthalpy\s+\.\.\.\s+([-\d.]+)\s+Eh'
            h_match = re.search(h_pattern, thermo_section)
            if h_match:
                thermo['H_total_hartree'] = float(h_match.group(1))

            # Total entropy
            s_pattern = r'Total entropy correction\s+\.\.\.\s+([-\d.]+)\s+Eh'
            s_match = re.search(s_pattern, thermo_section)
            if s_match:
                thermo['TS_hartree'] = float(s_match.group(1))

            # Final Gibbs free energy
            g_pattern = r'Final Gibbs free energy\s+\.\.\.\s+([-\d.]+)\s+Eh'
            g_match = re.search(g_pattern, thermo_section)
            if g_match:
                thermo['G_total_hartree'] = float(g_match.group(1))

        # Alternative thermochemistry format
        if not thermo:
            # Zero point vibrational energy
            zpe_alt_pattern = r'Zero point vibrational energy:\s+([-\d.]+)\s+kcal/mol'
            zpe_alt_match = re.search(zpe_alt_pattern, self.content)
            if zpe_alt_match:
                zpe_kcal = float(zpe_alt_match.group(1))
                thermo['ZPE_hartree'] = zpe_kcal / 627.509

            # Total thermal energy
            e_thermal_pattern = r'Total thermal energy\s+([-\d.]+)\s+Hartree'
            e_thermal_match = re.search(e_thermal_pattern, self.content)
            if e_thermal_match:
                thermo['E_thermal_hartree'] = float(e_thermal_match.group(1))

        return thermo

    def check_convergence(self):
        """Check if calculation converged."""
        convergence = {}

        # Check for successful termination
        if 'ORCA TERMINATED NORMALLY' in self.content:
            convergence['terminated_normally'] = True
        else:
            convergence['terminated_normally'] = False

        # Check geometry optimization convergence
        if 'THE OPTIMIZATION HAS CONVERGED' in self.content:
            convergence['geometry_converged'] = True
        elif 'OPTIMIZATION RUN' in self.content:
            convergence['geometry_converged'] = False
        else:
            convergence['geometry_converged'] = None

        # Check SCF convergence
        if 'SCF CONVERGED' in self.content or '***CONVERGED***' in self.content:
            convergence['scf_converged'] = True
        else:
            convergence['scf_converged'] = False

        return convergence

    def extract_optimization_trajectory(self):
        """Extract geometry optimization trajectory."""
        trajectory = []

        # Find all geometry cycles
        cycle_pattern = r'GEOMETRY OPTIMIZATION CYCLE\s+(\d+)'
        cycles = re.findall(cycle_pattern, self.content)

        # Find all energies during optimization
        energy_pattern = r'FINAL SINGLE POINT ENERGY\s+([-\d.]+)'
        energies = re.findall(energy_pattern, self.content)

        for i, (cycle, energy) in enumerate(zip(cycles, energies)):
            trajectory.append({
                'cycle': int(cycle),
                'energy_hartree': float(energy)
            })

        return trajectory

    def get_summary(self):
        """Get summary of calculation."""
        if not self.results:
            self.parse_all()

        summary = {
            'file': str(self.file_path),
            'job_type': self.results.get('job_type', []),
            'converged': self.results.get('convergence', {}).get('terminated_normally', False)
        }

        # Add key energies
        energies = self.results.get('energies', {})
        if 'final_energy_hartree' in energies:
            summary['final_energy_hartree'] = energies['final_energy_hartree']

        thermo = self.results.get('thermochemistry', {})
        if 'G_total_hartree' in thermo:
            summary['G_total_hartree'] = thermo['G_total_hartree']

        # Add geometry info
        geometry = self.results.get('geometry', {})
        if 'n_atoms' in geometry:
            summary['n_atoms'] = geometry['n_atoms']

        # Add frequency info
        frequencies = self.results.get('frequencies', {})
        if 'n_imaginary' in frequencies:
            summary['n_imaginary_frequencies'] = frequencies['n_imaginary']

        return summary


def parse_orca_file(file_path):
    """
    Convenience function to parse ORCA output file.

    Args:
        file_path: Path to ORCA output file

    Returns:
        Dictionary with parsed results
    """
    parser = ORCAParser(file_path)
    return parser.parse_all()
