#!/usr/bin/env python3
"""
VASP Output Parser

Parses VASP output files (OUTCAR, OSZICAR) to extract:
- Energies (total energy, free energy)
- Forces and stress
- Electronic structure (band structure, DOS)
- Convergence information
"""

import re
import numpy as np
from pathlib import Path


class VASPParser:
    """Parser for VASP output files."""

    def __init__(self, outcar_path=None, oszicar_path=None):
        """
        Initialize VASP parser.

        Args:
            outcar_path: Path to OUTCAR file
            oszicar_path: Path to OSZICAR file (optional)
        """
        self.outcar_path = Path(outcar_path) if outcar_path else None
        self.oszicar_path = Path(oszicar_path) if oszicar_path else None
        self.outcar_content = None
        self.oszicar_content = None
        self.results = {}

        if self.outcar_path and self.outcar_path.exists():
            with open(self.outcar_path, 'r', encoding='utf-8', errors='ignore') as f:
                self.outcar_content = f.read()

        if self.oszicar_path and self.oszicar_path.exists():
            with open(self.oszicar_path, 'r', encoding='utf-8', errors='ignore') as f:
                self.oszicar_content = f.read()

    def parse_all(self):
        """Parse all available data from VASP output."""
        if self.outcar_content is None:
            return {'error': 'OUTCAR not loaded'}

        self.results['job_info'] = self.parse_job_info()
        self.results['energies'] = self.parse_energies()
        self.results['geometry'] = self.parse_geometry()
        self.results['forces'] = self.parse_forces()
        self.results['stress'] = self.parse_stress()
        self.results['convergence'] = self.check_convergence()

        return self.results

    def parse_job_info(self):
        """Extract job information."""
        info = {}

        # VASP version
        version_pattern = r'vasp\.(\d+\.\d+\.\d+)'
        version_match = re.search(version_pattern, self.outcar_content, re.IGNORECASE)
        if version_match:
            info['vasp_version'] = version_match.group(1)

        # Number of ions
        nions_pattern = r'NIONS\s*=\s*(\d+)'
        nions_match = re.search(nions_pattern, self.outcar_content)
        if nions_match:
            info['n_ions'] = int(nions_match.group(1))

        # K-points
        kpoints_pattern = r'k-points\s+NKPTS\s*=\s*(\d+)'
        kpoints_match = re.search(kpoints_pattern, self.outcar_content)
        if kpoints_match:
            info['n_kpoints'] = int(kpoints_match.group(1))

        # Electronic steps
        nelm_pattern = r'NELM\s*=\s*(\d+)'
        nelm_match = re.search(nelm_pattern, self.outcar_content)
        if nelm_match:
            info['max_electronic_steps'] = int(nelm_match.group(1))

        # Ionic steps
        nsw_pattern = r'NSW\s*=\s*(\d+)'
        nsw_match = re.search(nsw_pattern, self.outcar_content)
        if nsw_match:
            info['max_ionic_steps'] = int(nsw_match.group(1))

        return info

    def parse_energies(self):
        """Extract energies from VASP output."""
        energies = {}

        # Free energy (TOTEN)
        toten_pattern = r'free  energy   TOTEN\s*=\s*([-\d.]+)\s*eV'
        toten_matches = re.findall(toten_pattern, self.outcar_content)
        if toten_matches:
            energies['free_energy_eV'] = float(toten_matches[-1])  # Last value
            energies['free_energy_hartree'] = float(toten_matches[-1]) / 27.2114
            energies['free_energy_kcal_mol'] = float(toten_matches[-1]) * 23.0605

        # Energy without entropy (E0)
        e0_pattern = r'energy  without entropy\s*=\s*([-\d.]+)'
        e0_matches = re.findall(e0_pattern, self.outcar_content)
        if e0_matches:
            energies['energy_without_entropy_eV'] = float(e0_matches[-1])

        # Energy with sigma->0 (extrapolated)
        sigma0_pattern = r'energy\(sigma->0\)\s*=\s*([-\d.]+)'
        sigma0_matches = re.findall(sigma0_pattern, self.outcar_content)
        if sigma0_matches:
            energies['energy_sigma0_eV'] = float(sigma0_matches[-1])

        # Parse OSZICAR if available for energy convergence
        if self.oszicar_content:
            oszicar_energies = []
            for line in self.oszicar_content.split('\n'):
                # Format: "  1 F= -.12345678E+02 E0= -.12345678E+02  d E =-.123456E+00"
                match = re.search(r'F=\s*([-\d.E+]+)', line)
                if match:
                    oszicar_energies.append(float(match.group(1)))

            if oszicar_energies:
                energies['energy_convergence'] = oszicar_energies
                energies['final_energy_oszicar_eV'] = oszicar_energies[-1]

        return energies

    def parse_geometry(self):
        """Extract final geometry."""
        geometry = {}

        # Find POSITION section
        pattern = r'POSITION\s+TOTAL-FORCE \(eV/Angst\)\s+-+\s+(.*?)\s+-{3,}'
        matches = re.findall(pattern, self.outcar_content, re.DOTALL)

        if matches:
            # Get last geometry
            last_geom = matches[-1]

            coordinates = []
            forces = []

            for line in last_geom.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 6:
                    try:
                        x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
                        fx, fy, fz = float(parts[3]), float(parts[4]), float(parts[5])

                        coordinates.append([x, y, z])
                        forces.append([fx, fy, fz])
                    except ValueError:
                        continue

            geometry['coordinates'] = coordinates
            geometry['forces'] = forces
            geometry['n_atoms'] = len(coordinates)

        # Get atom types from POTCAR section
        potcar_pattern = r'VRHFIN\s*=(\w+)'
        atom_types = re.findall(potcar_pattern, self.outcar_content)
        if atom_types:
            geometry['atom_types'] = atom_types

        # Get number of each atom type
        ions_per_type_pattern = r'ions per type =\s+([\d\s]+)'
        ions_match = re.search(ions_per_type_pattern, self.outcar_content)
        if ions_match:
            ions_per_type = [int(x) for x in ions_match.group(1).split()]
            geometry['ions_per_type'] = ions_per_type

            # Expand atom types
            if atom_types:
                atoms = []
                for atom_type, count in zip(atom_types, ions_per_type):
                    atoms.extend([atom_type] * count)
                geometry['atoms'] = atoms

        return geometry

    def parse_forces(self):
        """Extract forces on atoms."""
        forces_data = {}

        # Find TOTAL-FORCE section
        pattern = r'TOTAL-FORCE \(eV/Angst\)\s+-+\s+(.*?)\s+-{3,}'
        matches = re.findall(pattern, self.outcar_content, re.DOTALL)

        if matches:
            last_forces = matches[-1]

            forces = []
            for line in last_forces.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 6:
                    try:
                        fx = float(parts[3])
                        fy = float(parts[4])
                        fz = float(parts[5])
                        forces.append([fx, fy, fz])
                    except ValueError:
                        continue

            forces_array = np.array(forces)
            forces_data['forces_eV_Ang'] = forces

            # Calculate force magnitudes
            if len(forces_array) > 0:
                magnitudes = np.linalg.norm(forces_array, axis=1)
                forces_data['force_magnitudes'] = magnitudes.tolist()
                forces_data['max_force'] = float(np.max(magnitudes))
                forces_data['rms_force'] = float(np.sqrt(np.mean(magnitudes**2)))

        return forces_data

    def parse_stress(self):
        """Extract stress tensor."""
        stress_data = {}

        # Find stress tensor
        pattern = r'in kB\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)'
        matches = re.findall(pattern, self.outcar_content)

        if matches:
            # Get last stress tensor
            last_stress = matches[-1]
            stress_tensor = [float(x) for x in last_stress]

            stress_data['stress_tensor_kB'] = stress_tensor
            stress_data['stress_xx'] = stress_tensor[0]
            stress_data['stress_yy'] = stress_tensor[1]
            stress_data['stress_zz'] = stress_tensor[2]
            stress_data['stress_xy'] = stress_tensor[3]
            stress_data['stress_yz'] = stress_tensor[4]
            stress_data['stress_zx'] = stress_tensor[5]

            # Calculate pressure (negative of trace/3)
            pressure = -(stress_tensor[0] + stress_tensor[1] + stress_tensor[2]) / 3
            stress_data['pressure_kB'] = pressure

        return stress_data

    def check_convergence(self):
        """Check if calculation converged."""
        convergence = {}

        # Check for "reached required accuracy"
        if 'reached required accuracy' in self.outcar_content:
            convergence['converged'] = True
        else:
            convergence['converged'] = False

        # Check for warnings
        warnings = []
        if 'WARNING' in self.outcar_content:
            warning_lines = [line for line in self.outcar_content.split('\n') if 'WARNING' in line]
            warnings.extend(warning_lines[:5])  # First 5 warnings

        convergence['warnings'] = warnings

        return convergence

    def get_band_gap(self):
        """Extract band gap if available."""
        # This is a simplified extraction
        # Full band structure analysis would require parsing EIGENVAL or vasprun.xml

        gap_pattern = r'E-fermi\s*:\s*([-\d.]+)'
        fermi_match = re.search(gap_pattern, self.outcar_content)

        if fermi_match:
            return {'fermi_energy_eV': float(fermi_match.group(1))}

        return {}


def parse_vasp_output(outcar_path, oszicar_path=None):
    """
    Convenience function to parse VASP output.

    Args:
        outcar_path: Path to OUTCAR file
        oszicar_path: Path to OSZICAR file (optional)

    Returns:
        Dictionary with parsed results
    """
    parser = VASPParser(outcar_path, oszicar_path)
    return parser.parse_all()
