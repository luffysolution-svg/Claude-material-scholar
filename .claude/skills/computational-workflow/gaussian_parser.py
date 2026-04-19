#!/usr/bin/env python3
"""
Gaussian Output Parser

Parses Gaussian output files (.log, .out) to extract:
- Energies (SCF, ZPE, thermal corrections)
- Geometries (optimized structures)
- Frequencies (vibrational analysis)
- Thermodynamic properties (H, G, S)
- Electronic properties (charges, orbitals)
"""

import re
import numpy as np
from pathlib import Path


class GaussianParser:
    """Parser for Gaussian output files."""

    def __init__(self, file_path):
        """
        Initialize Gaussian parser.

        Args:
            file_path: Path to Gaussian output file (.log or .out)
        """
        self.file_path = Path(file_path)
        self.content = None
        self.results = {}

        if self.file_path.exists():
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                self.content = f.read()

    def parse_all(self):
        """Parse all available data from Gaussian output."""
        if self.content is None:
            return {'error': 'File not loaded'}

        self.results['job_type'] = self.parse_job_type()
        self.results['energies'] = self.parse_energies()
        self.results['geometry'] = self.parse_geometry()
        self.results['frequencies'] = self.parse_frequencies()
        self.results['thermochemistry'] = self.parse_thermochemistry()
        self.results['charges'] = self.parse_charges()
        self.results['convergence'] = self.check_convergence()

        return self.results

    def parse_job_type(self):
        """Determine job type (optimization, frequency, single point, etc.)."""
        job_types = []

        if re.search(r'#.*opt', self.content, re.IGNORECASE):
            job_types.append('optimization')
        if re.search(r'#.*freq', self.content, re.IGNORECASE):
            job_types.append('frequency')
        if re.search(r'#.*sp', self.content, re.IGNORECASE):
            job_types.append('single_point')
        if re.search(r'#.*irc', self.content, re.IGNORECASE):
            job_types.append('IRC')
        if re.search(r'#.*ts', self.content, re.IGNORECASE):
            job_types.append('transition_state')

        return job_types if job_types else ['unknown']

    def parse_energies(self):
        """Extract energies from Gaussian output."""
        energies = {}

        # SCF energy (electronic energy)
        scf_pattern = r'SCF Done:\s+E\(\w+\)\s+=\s+([-\d.]+)'
        scf_matches = re.findall(scf_pattern, self.content)
        if scf_matches:
            energies['SCF_hartree'] = float(scf_matches[-1])  # Last SCF energy
            energies['SCF_eV'] = float(scf_matches[-1]) * 27.2114  # Convert to eV
            energies['SCF_kcal_mol'] = float(scf_matches[-1]) * 627.509  # Convert to kcal/mol

        # Zero-point energy
        zpe_pattern = r'Zero-point correction=\s+([-\d.]+)'
        zpe_match = re.search(zpe_pattern, self.content)
        if zpe_match:
            energies['ZPE_hartree'] = float(zpe_match.group(1))

        # Thermal correction to energy
        thermal_e_pattern = r'Thermal correction to Energy=\s+([-\d.]+)'
        thermal_e_match = re.search(thermal_e_pattern, self.content)
        if thermal_e_match:
            energies['thermal_correction_E_hartree'] = float(thermal_e_match.group(1))

        # Thermal correction to enthalpy
        thermal_h_pattern = r'Thermal correction to Enthalpy=\s+([-\d.]+)'
        thermal_h_match = re.search(thermal_h_pattern, self.content)
        if thermal_h_match:
            energies['thermal_correction_H_hartree'] = float(thermal_h_match.group(1))

        # Thermal correction to Gibbs free energy
        thermal_g_pattern = r'Thermal correction to Gibbs Free Energy=\s+([-\d.]+)'
        thermal_g_match = re.search(thermal_g_pattern, self.content)
        if thermal_g_match:
            energies['thermal_correction_G_hartree'] = float(thermal_g_match.group(1))

        # Sum of electronic and thermal energies
        sum_e_pattern = r'Sum of electronic and thermal Energies=\s+([-\d.]+)'
        sum_e_match = re.search(sum_e_pattern, self.content)
        if sum_e_match:
            energies['E_total_hartree'] = float(sum_e_match.group(1))

        # Sum of electronic and thermal enthalpies
        sum_h_pattern = r'Sum of electronic and thermal Enthalpies=\s+([-\d.]+)'
        sum_h_match = re.search(sum_h_pattern, self.content)
        if sum_h_match:
            energies['H_total_hartree'] = float(sum_h_match.group(1))

        # Sum of electronic and thermal free energies
        sum_g_pattern = r'Sum of electronic and thermal Free Energies=\s+([-\d.]+)'
        sum_g_match = re.search(sum_g_pattern, self.content)
        if sum_g_match:
            energies['G_total_hartree'] = float(sum_g_match.group(1))

        return energies

    def parse_geometry(self):
        """Extract optimized geometry."""
        geometry = {}

        # Find standard orientation section
        pattern = r'Standard orientation:.*?-{5,}(.*?)-{5,}'
        matches = re.findall(pattern, self.content, re.DOTALL)

        if matches:
            # Get last geometry (optimized)
            last_geom = matches[-1]

            atoms = []
            coordinates = []

            # Parse atom lines
            atom_pattern = r'\s+\d+\s+(\d+)\s+\d+\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)'
            for match in re.finditer(atom_pattern, last_geom):
                atomic_num = int(match.group(1))
                x = float(match.group(2))
                y = float(match.group(3))
                z = float(match.group(4))

                # Convert atomic number to element symbol
                element = self.atomic_number_to_symbol(atomic_num)

                atoms.append(element)
                coordinates.append([x, y, z])

            geometry['atoms'] = atoms
            geometry['coordinates'] = coordinates
            geometry['n_atoms'] = len(atoms)

        return geometry

    def parse_frequencies(self):
        """Extract vibrational frequencies."""
        frequencies = {}

        # Find frequencies section
        freq_pattern = r'Frequencies --\s+([\d.\s]+)'
        freq_matches = re.findall(freq_pattern, self.content)

        if freq_matches:
            all_freqs = []
            for match in freq_matches:
                freqs = [float(f) for f in match.split()]
                all_freqs.extend(freqs)

            frequencies['frequencies_cm-1'] = all_freqs
            frequencies['n_frequencies'] = len(all_freqs)

            # Check for imaginary frequencies (negative values)
            imaginary_freqs = [f for f in all_freqs if f < 0]
            frequencies['imaginary_frequencies'] = imaginary_freqs
            frequencies['n_imaginary'] = len(imaginary_freqs)

            # Classify structure
            if len(imaginary_freqs) == 0:
                frequencies['structure_type'] = 'minimum'
            elif len(imaginary_freqs) == 1:
                frequencies['structure_type'] = 'transition_state'
            else:
                frequencies['structure_type'] = 'higher_order_saddle_point'

        return frequencies

    def parse_thermochemistry(self):
        """Extract thermochemical properties."""
        thermo = {}

        # Temperature
        temp_pattern = r'Temperature\s+([\d.]+)\s+Kelvin'
        temp_match = re.search(temp_pattern, self.content)
        if temp_match:
            thermo['temperature_K'] = float(temp_match.group(1))

        # Pressure
        press_pattern = r'Pressure\s+([\d.]+)\s+Atm'
        press_match = re.search(press_pattern, self.content)
        if press_match:
            thermo['pressure_atm'] = float(press_match.group(1))

        # Entropy
        entropy_pattern = r'Total\s+.*?S\s+.*?Cal/Mol-Kelvin.*?\n.*?Electronic.*?\n.*?Translational.*?\n.*?Rotational.*?\n.*?Vibrational.*?\n\s+Total\s+([\d.]+)'
        entropy_match = re.search(entropy_pattern, self.content)
        if entropy_match:
            thermo['entropy_cal_mol_K'] = float(entropy_match.group(1))
            thermo['entropy_J_mol_K'] = float(entropy_match.group(1)) * 4.184

        return thermo

    def parse_charges(self):
        """Extract atomic charges."""
        charges = {}

        # Mulliken charges
        mulliken_pattern = r'Mulliken charges:.*?\n\s+\d+(.*?)Sum of Mulliken charges'
        mulliken_match = re.search(mulliken_pattern, self.content, re.DOTALL)

        if mulliken_match:
            charge_lines = mulliken_match.group(1).strip().split('\n')
            mulliken_charges = []

            for line in charge_lines:
                match = re.search(r'\d+\s+\w+\s+([-\d.]+)', line)
                if match:
                    mulliken_charges.append(float(match.group(1)))

            charges['mulliken'] = mulliken_charges

        # NBO charges (if available)
        nbo_pattern = r'Summary of Natural Population Analysis:.*?\n.*?-{5,}(.*?)-{5,}'
        nbo_match = re.search(nbo_pattern, self.content, re.DOTALL)

        if nbo_match:
            nbo_section = nbo_match.group(1)
            nbo_charges = []

            charge_pattern = r'\w+\s+\d+\s+([-\d.]+)'
            for match in re.finditer(charge_pattern, nbo_section):
                nbo_charges.append(float(match.group(1)))

            if nbo_charges:
                charges['nbo'] = nbo_charges

        return charges

    def check_convergence(self):
        """Check if calculation converged."""
        convergence = {}

        # Check for normal termination
        if 'Normal termination' in self.content:
            convergence['terminated_normally'] = True
        else:
            convergence['terminated_normally'] = False

        # Check for optimization convergence
        if 'Optimization completed' in self.content or 'Stationary point found' in self.content:
            convergence['optimization_converged'] = True
        else:
            convergence['optimization_converged'] = False

        return convergence

    @staticmethod
    def atomic_number_to_symbol(atomic_num):
        """Convert atomic number to element symbol."""
        elements = {
            1: 'H', 2: 'He', 3: 'Li', 4: 'Be', 5: 'B', 6: 'C', 7: 'N', 8: 'O',
            9: 'F', 10: 'Ne', 11: 'Na', 12: 'Mg', 13: 'Al', 14: 'Si', 15: 'P',
            16: 'S', 17: 'Cl', 18: 'Ar', 19: 'K', 20: 'Ca', 21: 'Sc', 22: 'Ti',
            23: 'V', 24: 'Cr', 25: 'Mn', 26: 'Fe', 27: 'Co', 28: 'Ni', 29: 'Cu',
            30: 'Zn', 31: 'Ga', 32: 'Ge', 33: 'As', 34: 'Se', 35: 'Br', 36: 'Kr',
            47: 'Ag', 48: 'Cd', 78: 'Pt', 79: 'Au', 80: 'Hg'
        }
        return elements.get(atomic_num, f'X{atomic_num}')


def parse_gaussian_file(file_path):
    """
    Convenience function to parse Gaussian output file.

    Args:
        file_path: Path to Gaussian output file

    Returns:
        Dictionary with parsed results
    """
    parser = GaussianParser(file_path)
    return parser.parse_all()
