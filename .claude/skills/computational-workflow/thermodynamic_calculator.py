"""
Thermodynamic Calculator for Computational Chemistry
Calculates ΔG, ΔH, ΔS with temperature corrections, equilibrium constants, and rate constants
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Physical constants
R = 8.314462618  # J/(mol·K) - Gas constant
h = 6.62607015e-34  # J·s - Planck constant
kB = 1.380649e-23  # J/K - Boltzmann constant
c = 299792458  # m/s - Speed of light
kcal_to_J = 4184  # J/kcal
hartree_to_kcal = 627.5095  # kcal/mol per hartree
eV_to_kcal = 23.0605  # kcal/mol per eV


@dataclass
class ThermodynamicData:
    """Container for thermodynamic properties"""
    E_elec: float  # Electronic energy (hartree or eV)
    ZPE: float  # Zero-point energy (hartree or eV)
    H_corr: float  # Enthalpy correction (hartree or eV)
    G_corr: float  # Gibbs free energy correction (hartree or eV)
    S: float  # Entropy (cal/(mol·K))
    temperature: float  # Temperature (K)
    energy_unit: str = "hartree"  # "hartree" or "eV"


class ThermodynamicCalculator:
    """Calculate thermodynamic properties from DFT outputs"""

    def __init__(self, energy_unit: str = "hartree"):
        """
        Initialize calculator

        Args:
            energy_unit: "hartree" (Gaussian, ORCA) or "eV" (VASP)
        """
        self.energy_unit = energy_unit
        self.conversion_factor = hartree_to_kcal if energy_unit == "hartree" else eV_to_kcal

    def calculate_reaction_energy(
        self,
        reactants: List[ThermodynamicData],
        products: List[ThermodynamicData],
        temperature: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate reaction thermodynamics: ΔE, ΔH, ΔG, ΔS

        Args:
            reactants: List of reactant thermodynamic data
            products: List of product thermodynamic data
            temperature: Temperature for corrections (K), uses reactant T if None

        Returns:
            Dictionary with ΔE, ΔH, ΔG, ΔS in kcal/mol (S in cal/(mol·K))
        """
        if temperature is None:
            temperature = reactants[0].temperature

        # Sum energies for reactants and products
        E_reactants = sum(r.E_elec for r in reactants)
        E_products = sum(p.E_elec for p in products)

        ZPE_reactants = sum(r.ZPE for r in reactants)
        ZPE_products = sum(p.ZPE for p in products)

        H_reactants = sum(r.E_elec + r.H_corr for r in reactants)
        H_products = sum(p.E_elec + p.H_corr for p in products)

        G_reactants = sum(r.E_elec + r.G_corr for r in reactants)
        G_products = sum(p.E_elec + p.G_corr for p in products)

        S_reactants = sum(r.S for r in reactants)
        S_products = sum(p.S for p in products)

        # Calculate differences (products - reactants)
        delta_E = (E_products - E_reactants) * self.conversion_factor
        delta_ZPE = (ZPE_products - ZPE_reactants) * self.conversion_factor
        delta_H = (H_products - H_reactants) * self.conversion_factor
        delta_G = (G_products - G_reactants) * self.conversion_factor
        delta_S = S_products - S_reactants

        return {
            "ΔE": delta_E,
            "ΔE+ZPE": delta_E + delta_ZPE,
            "ΔH": delta_H,
            "ΔG": delta_G,
            "ΔS": delta_S,
            "temperature": temperature
        }

    def calculate_activation_energy(
        self,
        reactant: ThermodynamicData,
        transition_state: ThermodynamicData,
        temperature: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate activation barrier: Ea, ΔH‡, ΔG‡, ΔS‡

        Args:
            reactant: Reactant thermodynamic data
            transition_state: Transition state thermodynamic data
            temperature: Temperature (K)

        Returns:
            Dictionary with Ea, ΔH‡, ΔG‡, ΔS‡ in kcal/mol
        """
        if temperature is None:
            temperature = reactant.temperature

        delta_E = (transition_state.E_elec - reactant.E_elec) * self.conversion_factor
        delta_ZPE = (transition_state.ZPE - reactant.ZPE) * self.conversion_factor

        delta_H = ((transition_state.E_elec + transition_state.H_corr) -
                   (reactant.E_elec + reactant.H_corr)) * self.conversion_factor

        delta_G = ((transition_state.E_elec + transition_state.G_corr) -
                   (reactant.E_elec + reactant.G_corr)) * self.conversion_factor

        delta_S = transition_state.S - reactant.S

        return {
            "Ea": delta_E,
            "Ea+ZPE": delta_E + delta_ZPE,
            "ΔH‡": delta_H,
            "ΔG‡": delta_G,
            "ΔS‡": delta_S,
            "temperature": temperature
        }

    def calculate_equilibrium_constant(
        self,
        delta_G: float,
        temperature: float
    ) -> float:
        """
        Calculate equilibrium constant from ΔG

        ΔG = -RT ln(K)
        K = exp(-ΔG / RT)

        Args:
            delta_G: Gibbs free energy change (kcal/mol)
            temperature: Temperature (K)

        Returns:
            Equilibrium constant K (dimensionless)
        """
        delta_G_J = delta_G * kcal_to_J  # Convert to J/mol
        K = np.exp(-delta_G_J / (R * temperature))
        return K

    def calculate_rate_constant(
        self,
        delta_G_activation: float,
        temperature: float,
        transmission_coefficient: float = 1.0
    ) -> float:
        """
        Calculate rate constant using Eyring equation

        k = (κ * kB * T / h) * exp(-ΔG‡ / RT)

        Args:
            delta_G_activation: Activation free energy (kcal/mol)
            temperature: Temperature (K)
            transmission_coefficient: κ, typically 1.0

        Returns:
            Rate constant k (s⁻¹)
        """
        delta_G_J = delta_G_activation * kcal_to_J  # Convert to J/mol
        k = (transmission_coefficient * kB * temperature / h) * \
            np.exp(-delta_G_J / (R * temperature))
        return k

    def calculate_temperature_correction(
        self,
        E_elec: float,
        ZPE: float,
        H_corr_T1: float,
        G_corr_T1: float,
        S_T1: float,
        T1: float,
        T2: float,
        frequencies: Optional[List[float]] = None
    ) -> Tuple[float, float, float]:
        """
        Correct thermodynamic properties from T1 to T2

        Uses rigid rotor-harmonic oscillator approximation
        If frequencies provided, recalculates thermal corrections
        Otherwise, uses linear scaling approximation

        Args:
            E_elec: Electronic energy (hartree or eV)
            ZPE: Zero-point energy (hartree or eV)
            H_corr_T1: Enthalpy correction at T1 (hartree or eV)
            G_corr_T1: Gibbs correction at T1 (hartree or eV)
            S_T1: Entropy at T1 (cal/(mol·K))
            T1: Original temperature (K)
            T2: Target temperature (K)
            frequencies: Vibrational frequencies (cm⁻¹), optional

        Returns:
            (H_corr_T2, G_corr_T2, S_T2)
        """
        if frequencies is not None:
            # Recalculate thermal corrections from frequencies
            H_corr_T2, S_T2 = self._calculate_thermal_corrections(frequencies, T2)
            G_corr_T2 = H_corr_T2 - (T2 * S_T2 / (1000 * self.conversion_factor))
        else:
            # Linear scaling approximation
            # ΔH ≈ constant, ΔS scales with ln(T)
            H_corr_T2 = H_corr_T1 * (T2 / T1)
            S_T2 = S_T1 * (T2 / T1)
            G_corr_T2 = H_corr_T1 - (T2 * S_T2 / (1000 * self.conversion_factor))

        return H_corr_T2, G_corr_T2, S_T2

    def _calculate_thermal_corrections(
        self,
        frequencies: List[float],
        temperature: float
    ) -> Tuple[float, float]:
        """
        Calculate thermal corrections from vibrational frequencies

        Uses rigid rotor-harmonic oscillator approximation

        Args:
            frequencies: Vibrational frequencies (cm⁻¹)
            temperature: Temperature (K)

        Returns:
            (H_corr, S) in (hartree or eV, cal/(mol·K))
        """
        # Convert frequencies to energy (cm⁻¹ to J)
        freq_J = np.array([f * h * c * 100 for f in frequencies if f > 0])

        # Thermal energy
        kT = kB * temperature

        # Vibrational contribution to enthalpy
        H_vib = 0.0
        S_vib = 0.0

        for freq in freq_J:
            x = freq / kT
            if x < 100:  # Avoid overflow
                exp_x = np.exp(x)
                H_vib += freq * (0.5 + 1.0 / (exp_x - 1.0))
                S_vib += x / (exp_x - 1.0) - np.log(1.0 - np.exp(-x))

        # Add translational and rotational contributions (3RT/2 each for ideal gas)
        H_trans_rot = 3 * R * temperature  # J/mol
        S_trans_rot = 30.0  # Approximate, cal/(mol·K)

        # Convert to output units
        H_corr = (H_vib + H_trans_rot) / (kcal_to_J * self.conversion_factor)
        S = (S_vib * R / 4.184) + S_trans_rot  # Convert to cal/(mol·K)

        return H_corr, S

    def generate_thermodynamic_summary(
        self,
        reaction_data: Dict[str, float],
        activation_data: Optional[Dict[str, float]] = None
    ) -> str:
        """
        Generate formatted thermodynamic summary

        Args:
            reaction_data: Output from calculate_reaction_energy()
            activation_data: Output from calculate_activation_energy(), optional

        Returns:
            Formatted string summary
        """
        T = reaction_data["temperature"]

        summary = f"Thermodynamic Summary (T = {T:.1f} K)\n"
        summary += "=" * 50 + "\n\n"

        summary += "Reaction Thermodynamics:\n"
        summary += f"  ΔE           = {reaction_data['ΔE']:>10.2f} kcal/mol\n"
        summary += f"  ΔE+ZPE       = {reaction_data['ΔE+ZPE']:>10.2f} kcal/mol\n"
        summary += f"  ΔH           = {reaction_data['ΔH']:>10.2f} kcal/mol\n"
        summary += f"  ΔG           = {reaction_data['ΔG']:>10.2f} kcal/mol\n"
        summary += f"  ΔS           = {reaction_data['ΔS']:>10.2f} cal/(mol·K)\n"

        # Equilibrium constant
        K = self.calculate_equilibrium_constant(reaction_data['ΔG'], T)
        summary += f"\n  K_eq         = {K:.2e}\n"

        if activation_data:
            summary += "\n" + "=" * 50 + "\n"
            summary += "Activation Barrier:\n"
            summary += f"  Ea           = {activation_data['Ea']:>10.2f} kcal/mol\n"
            summary += f"  Ea+ZPE       = {activation_data['Ea+ZPE']:>10.2f} kcal/mol\n"
            summary += f"  ΔH‡          = {activation_data['ΔH‡']:>10.2f} kcal/mol\n"
            summary += f"  ΔG‡          = {activation_data['ΔG‡']:>10.2f} kcal/mol\n"
            summary += f"  ΔS‡          = {activation_data['ΔS‡']:>10.2f} cal/(mol·K)\n"

            # Rate constant
            k = self.calculate_rate_constant(activation_data['ΔG‡'], T)
            summary += f"\n  k            = {k:.2e} s⁻¹\n"

        return summary
