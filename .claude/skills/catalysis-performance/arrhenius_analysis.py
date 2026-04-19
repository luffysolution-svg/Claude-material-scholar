#!/usr/bin/env python3
"""
Arrhenius Analysis Module

Analyzes temperature-dependent kinetics including:
- Activation energy calculation
- Pre-exponential factor determination
- Temperature dependence analysis
- Arrhenius plots
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import linregress
from scipy.optimize import curve_fit
import json


class ArrheniusAnalyzer:
    """Analyzer for Arrhenius kinetics."""

    def __init__(self):
        """Initialize Arrhenius analyzer."""
        self.R = 8.314  # Gas constant in J/(mol·K)
        self.results = {}

    @staticmethod
    def arrhenius_equation(T, A, Ea, R=8.314):
        """
        Arrhenius equation: k = A * exp(-Ea / (R*T))

        Args:
            T: Temperature in Kelvin
            A: Pre-exponential factor
            Ea: Activation energy in J/mol
            R: Gas constant (default: 8.314 J/(mol·K))

        Returns:
            Rate constant k
        """
        return A * np.exp(-Ea / (R * T))

    def calculate_activation_energy(self, temperatures, rate_constants, temp_unit='C'):
        """
        Calculate activation energy from Arrhenius plot.

        ln(k) = ln(A) - Ea/(R*T)

        Args:
            temperatures: Array of temperatures
            rate_constants: Array of rate constants
            temp_unit: Temperature unit ('C' or 'K')

        Returns:
            Dictionary with Ea, A, and fit statistics
        """
        temperatures = np.array(temperatures)
        rate_constants = np.array(rate_constants)

        # Convert to Kelvin if necessary
        if temp_unit == 'C':
            T_K = temperatures + 273.15
        else:
            T_K = temperatures

        # Remove zero or negative rate constants
        mask = rate_constants > 0
        T_K = T_K[mask]
        k = rate_constants[mask]

        if len(k) < 2:
            return {'error': 'Insufficient data points for Arrhenius analysis'}

        # Calculate 1/T and ln(k)
        inv_T = 1 / T_K
        ln_k = np.log(k)

        # Linear regression: ln(k) = ln(A) - Ea/R * (1/T)
        slope, intercept, r_value, p_value, std_err = linregress(inv_T, ln_k)

        # Extract parameters
        Ea = -slope * self.R  # Activation energy in J/mol
        Ea_kJ = Ea / 1000  # Convert to kJ/mol
        A = np.exp(intercept)  # Pre-exponential factor

        # Calculate standard error of Ea
        Ea_std_err = std_err * self.R / 1000  # in kJ/mol

        # Calculate fitted values
        ln_k_fit = slope * inv_T + intercept
        k_fit = np.exp(ln_k_fit)

        results = {
            'activation_energy_kJ_mol': Ea_kJ,
            'activation_energy_J_mol': Ea,
            'Ea_std_error_kJ_mol': Ea_std_err,
            'pre_exponential_factor': A,
            'ln_A': intercept,
            'r_squared': r_value ** 2,
            'p_value': p_value,
            'temperatures_K': T_K.tolist(),
            'rate_constants': k.tolist(),
            'ln_rate_constants': ln_k.tolist(),
            'inv_temperature': inv_T.tolist(),
            'fitted_ln_k': ln_k_fit.tolist(),
            'fitted_k': k_fit.tolist()
        }

        return results

    def calculate_rate_at_temperature(self, T, Ea, A, temp_unit='C'):
        """
        Calculate rate constant at a given temperature.

        Args:
            T: Temperature
            Ea: Activation energy in kJ/mol
            A: Pre-exponential factor
            temp_unit: Temperature unit ('C' or 'K')

        Returns:
            Rate constant at temperature T
        """
        if temp_unit == 'C':
            T_K = T + 273.15
        else:
            T_K = T

        Ea_J = Ea * 1000  # Convert to J/mol
        k = self.arrhenius_equation(T_K, A, Ea_J, self.R)

        return k

    def calculate_temperature_for_rate(self, k_target, Ea, A):
        """
        Calculate temperature required for a target rate constant.

        T = Ea / (R * (ln(A) - ln(k)))

        Args:
            k_target: Target rate constant
            Ea: Activation energy in kJ/mol
            A: Pre-exponential factor

        Returns:
            Temperature in Kelvin
        """
        if k_target <= 0 or A <= 0:
            return None

        Ea_J = Ea * 1000
        T = Ea_J / (self.R * (np.log(A) - np.log(k_target)))

        return T

    def analyze_temperature_dependence(self, temperatures, conversions, temp_unit='C'):
        """
        Analyze temperature dependence of conversion.

        Args:
            temperatures: Array of temperatures
            conversions: Array of conversion values (%)
            temp_unit: Temperature unit ('C' or 'K')

        Returns:
            Dictionary with temperature dependence analysis
        """
        temperatures = np.array(temperatures)
        conversions = np.array(conversions)

        if temp_unit == 'C':
            T_K = temperatures + 273.15
        else:
            T_K = temperatures

        # Calculate temperature coefficient (Q10)
        # Q10 = rate at (T+10) / rate at T
        if len(temperatures) >= 2:
            # Use first and last points for Q10 estimation
            T_diff = temperatures[-1] - temperatures[0]
            if T_diff > 0:
                conv_ratio = conversions[-1] / conversions[0] if conversions[0] > 0 else 0
                Q10 = conv_ratio ** (10 / T_diff)
            else:
                Q10 = None
        else:
            Q10 = None

        # Fit polynomial to conversion vs temperature
        if len(temperatures) >= 3:
            coeffs = np.polyfit(temperatures, conversions, 2)
            fitted_conversions = np.polyval(coeffs, temperatures)

            # Calculate R²
            ss_res = np.sum((conversions - fitted_conversions) ** 2)
            ss_tot = np.sum((conversions - np.mean(conversions)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        else:
            coeffs = None
            fitted_conversions = None
            r_squared = None

        results = {
            'temperatures': temperatures.tolist(),
            'temperatures_K': T_K.tolist(),
            'conversions_%': conversions.tolist(),
            'Q10_temperature_coefficient': Q10,
            'polynomial_coefficients': coeffs.tolist() if coeffs is not None else None,
            'fitted_conversions': fitted_conversions.tolist() if fitted_conversions is not None else None,
            'r_squared': r_squared
        }

        return results

    def calculate_apparent_activation_energy(self, temperatures, conversions, flow_rate, catalyst_mass, temp_unit='C'):
        """
        Calculate apparent activation energy from conversion data.

        Assumes first-order kinetics: r = k * C
        k can be estimated from conversion and space velocity

        Args:
            temperatures: Array of temperatures
            conversions: Array of conversion values (fraction 0-1)
            flow_rate: Flow rate (mL/min)
            catalyst_mass: Catalyst mass (g)
            temp_unit: Temperature unit ('C' or 'K')

        Returns:
            Dictionary with apparent Ea
        """
        temperatures = np.array(temperatures)
        conversions = np.array(conversions)

        if temp_unit == 'C':
            T_K = temperatures + 273.15
        else:
            T_K = temperatures

        # Calculate apparent rate constants
        # For plug flow: k = -(F/W) * ln(1-X)
        # where F = flow rate, W = catalyst mass, X = conversion
        WHSV = flow_rate / catalyst_mass  # h⁻¹ (assuming flow in mL/min → need conversion)

        k_app = []
        valid_T = []

        for i, X in enumerate(conversions):
            if 0 < X < 1:
                k = -WHSV * np.log(1 - X)
                k_app.append(k)
                valid_T.append(T_K[i])

        if len(k_app) < 2:
            return {'error': 'Insufficient valid data points'}

        k_app = np.array(k_app)
        valid_T = np.array(valid_T)

        # Arrhenius analysis
        inv_T = 1 / valid_T
        ln_k = np.log(k_app)

        slope, intercept, r_value, p_value, std_err = linregress(inv_T, ln_k)

        Ea = -slope * self.R / 1000  # kJ/mol
        A = np.exp(intercept)

        results = {
            'apparent_Ea_kJ_mol': Ea,
            'pre_exponential_factor': A,
            'r_squared': r_value ** 2,
            'temperatures_K': valid_T.tolist(),
            'apparent_rate_constants': k_app.tolist()
        }

        return results

    def plot_arrhenius(self, temperatures, rate_constants, Ea=None, A=None, temp_unit='C', output_path=None):
        """
        Generate Arrhenius plot.

        Args:
            temperatures: Array of temperatures
            rate_constants: Array of rate constants
            Ea: Activation energy (kJ/mol) for fitted line
            A: Pre-exponential factor for fitted line
            temp_unit: Temperature unit ('C' or 'K')
            output_path: Path to save plot

        Returns:
            matplotlib figure
        """
        temperatures = np.array(temperatures)
        rate_constants = np.array(rate_constants)

        if temp_unit == 'C':
            T_K = temperatures + 273.15
        else:
            T_K = temperatures

        # Remove invalid data
        mask = rate_constants > 0
        T_K = T_K[mask]
        k = rate_constants[mask]

        inv_T = 1 / T_K
        ln_k = np.log(k)

        fig, ax = plt.subplots(figsize=(10, 7))

        # Plot data points
        ax.plot(inv_T * 1000, ln_k, 'o', markersize=10, label='Experimental data', color='blue')

        # Plot fitted line if Ea and A provided
        if Ea is not None and A is not None:
            inv_T_fit = np.linspace(min(inv_T), max(inv_T), 100)
            ln_k_fit = np.log(A) - (Ea * 1000) / self.R * inv_T_fit
            ax.plot(inv_T_fit * 1000, ln_k_fit, '-', linewidth=2, label=f'Fit: Ea = {Ea:.1f} kJ/mol', color='red')

        ax.set_xlabel('1000/T (K⁻¹)', fontsize=14)
        ax.set_ylabel('ln(k)', fontsize=14)
        ax.set_title('Arrhenius Plot', fontsize=16, fontweight='bold')
        ax.legend(fontsize=12)
        ax.grid(True, alpha=0.3)

        # Add text box with parameters
        if Ea is not None and A is not None:
            textstr = f'Ea = {Ea:.2f} kJ/mol\nA = {A:.2e}'
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=12,
                   verticalalignment='top', bbox=props)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig

    def plot_temperature_dependence(self, temperatures, conversions, temp_unit='C', output_path=None):
        """
        Plot conversion vs temperature.

        Args:
            temperatures: Array of temperatures
            conversions: Array of conversion values
            temp_unit: Temperature unit ('C' or 'K')
            output_path: Path to save plot

        Returns:
            matplotlib figure
        """
        fig, ax = plt.subplots(figsize=(10, 7))

        ax.plot(temperatures, conversions, 'o-', markersize=10, linewidth=2, color='blue')

        ax.set_xlabel(f'Temperature (°{temp_unit})', fontsize=14)
        ax.set_ylabel('Conversion (%)', fontsize=14)
        ax.set_title('Temperature Dependence of Conversion', fontsize=16, fontweight='bold')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig


if __name__ == '__main__':
    # Example usage
    analyzer = ArrheniusAnalyzer()

    # Example data
    temperatures = [200, 225, 250, 275, 300]  # °C
    rate_constants = [0.05, 0.15, 0.35, 0.75, 1.5]  # arbitrary units

    # Calculate activation energy
    results = analyzer.calculate_activation_energy(temperatures, rate_constants)

    print("Arrhenius Analysis Results:")
    print(f"Activation Energy: {results['activation_energy_kJ_mol']:.2f} ± {results['Ea_std_error_kJ_mol']:.2f} kJ/mol")
    print(f"Pre-exponential Factor: {results['pre_exponential_factor']:.2e}")
    print(f"R²: {results['r_squared']:.4f}")

    # Generate plot
    analyzer.plot_arrhenius(
        temperatures,
        rate_constants,
        Ea=results['activation_energy_kJ_mol'],
        A=results['pre_exponential_factor'],
        output_path='arrhenius_plot.png'
    )
