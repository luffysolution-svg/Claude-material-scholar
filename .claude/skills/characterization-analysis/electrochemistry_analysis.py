#!/usr/bin/env python3
"""
Electrochemistry Analysis Module

Analyzes electrochemical data including:
- Cyclic voltammetry (CV) analysis
- Tafel plot analysis
- Electrochemical impedance spectroscopy (EIS) fitting
- Stability curves
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.signal import savgol_filter
import json


class ElectrochemistryAnalyzer:
    """Analyzer for electrochemical data."""

    def __init__(self):
        """Initialize electrochemistry analyzer."""
        self.cv_data = None
        self.tafel_data = None
        self.eis_data = None

    def analyze_cv(self, potential, current, scan_rate=50):
        """
        Analyze cyclic voltammetry data.

        Args:
            potential: Array of potential values (V vs reference)
            current: Array of current values (mA or A)
            scan_rate: Scan rate in mV/s

        Returns:
            Dictionary with CV analysis results
        """
        potential = np.array(potential)
        current = np.array(current)

        # Find peaks (oxidation and reduction)
        # Smooth data first
        current_smooth = savgol_filter(current, window_length=11, polyorder=3)

        # Find oxidation peaks (positive current)
        ox_mask = current_smooth > 0
        if np.any(ox_mask):
            ox_peak_idx = np.argmax(current_smooth[ox_mask])
            ox_peak_potential = potential[ox_mask][ox_peak_idx]
            ox_peak_current = current[ox_mask][ox_peak_idx]
        else:
            ox_peak_potential = None
            ox_peak_current = None

        # Find reduction peaks (negative current)
        red_mask = current_smooth < 0
        if np.any(red_mask):
            red_peak_idx = np.argmin(current_smooth[red_mask])
            red_peak_potential = potential[red_mask][red_peak_idx]
            red_peak_current = current[red_mask][red_peak_idx]
        else:
            red_peak_potential = None
            red_peak_current = None

        # Calculate peak separation
        if ox_peak_potential is not None and red_peak_potential is not None:
            peak_separation = abs(ox_peak_potential - red_peak_potential)
        else:
            peak_separation = None

        # Calculate electrochemically active surface area (ECSA) if double layer region identified
        # This is simplified - actual ECSA calculation requires capacitance measurement

        results = {
            'oxidation_peak_potential_V': ox_peak_potential,
            'oxidation_peak_current': ox_peak_current,
            'reduction_peak_potential_V': red_peak_potential,
            'reduction_peak_current': red_peak_current,
            'peak_separation_V': peak_separation,
            'scan_rate_mV_s': scan_rate,
            'reversibility': 'reversible' if peak_separation and peak_separation < 0.1 else 'quasi-reversible or irreversible'
        }

        self.cv_data = {
            'potential': potential.tolist(),
            'current': current.tolist(),
            'analysis': results
        }

        return results

    def analyze_tafel(self, overpotential, current_density, region='cathodic'):
        """
        Analyze Tafel plot to extract kinetic parameters.

        Tafel equation: η = a + b*log(j)
        where η is overpotential, j is current density, b is Tafel slope

        Args:
            overpotential: Array of overpotential values (V)
            current_density: Array of current density values (mA/cm² or A/cm²)
            region: 'cathodic' or 'anodic'

        Returns:
            Dictionary with Tafel analysis results
        """
        overpotential = np.array(overpotential)
        current_density = np.array(current_density)

        # Remove zero or negative current densities
        mask = current_density > 0
        eta = overpotential[mask]
        j = current_density[mask]

        if len(j) < 5:
            return {'error': 'Insufficient data points for Tafel analysis'}

        # Calculate log(j)
        log_j = np.log10(j)

        # Linear fit in Tafel region (typically middle region)
        # Select linear region (heuristic: middle 50% of data)
        n_points = len(eta)
        start_idx = n_points // 4
        end_idx = 3 * n_points // 4

        eta_fit = eta[start_idx:end_idx]
        log_j_fit = log_j[start_idx:end_idx]

        # Linear regression
        coeffs = np.polyfit(log_j_fit, eta_fit, 1)
        tafel_slope = coeffs[0]  # mV/decade
        intercept = coeffs[1]

        # Calculate exchange current density (j0) at η = 0
        log_j0 = -intercept / tafel_slope
        j0 = 10**log_j0

        # Calculate overpotential at specific current densities
        eta_at_10 = tafel_slope * np.log10(10) + intercept if 10 > j0 else None
        eta_at_100 = tafel_slope * np.log10(100) + intercept if 100 > j0 else None

        results = {
            'tafel_slope_mV_dec': abs(tafel_slope * 1000),  # Convert to mV/decade
            'exchange_current_density': j0,
            'overpotential_at_10mA_cm2': eta_at_10,
            'overpotential_at_100mA_cm2': eta_at_100,
            'region': region,
            'fit_quality': 'good' if abs(tafel_slope) < 0.2 else 'check data quality'
        }

        self.tafel_data = {
            'overpotential': overpotential.tolist(),
            'current_density': current_density.tolist(),
            'log_current_density': log_j.tolist(),
            'analysis': results
        }

        return results

    def analyze_eis(self, frequency, z_real, z_imag):
        """
        Analyze electrochemical impedance spectroscopy data.

        Args:
            frequency: Array of frequency values (Hz)
            z_real: Array of real impedance (Ohm)
            z_imag: Array of imaginary impedance (Ohm)

        Returns:
            Dictionary with EIS analysis results
        """
        frequency = np.array(frequency)
        z_real = np.array(z_real)
        z_imag = np.array(z_imag)

        # Calculate magnitude and phase
        z_mag = np.sqrt(z_real**2 + z_imag**2)
        phase = np.arctan2(-z_imag, z_real) * 180 / np.pi

        # Extract solution resistance (Rs) - high frequency intercept
        high_freq_idx = np.argmax(frequency)
        Rs = z_real[high_freq_idx]

        # Extract charge transfer resistance (Rct) - low frequency intercept minus Rs
        low_freq_idx = np.argmin(frequency)
        Rct = z_real[low_freq_idx] - Rs

        # Find characteristic frequency (peak in -Z_imag)
        peak_idx = np.argmax(-z_imag)
        f_char = frequency[peak_idx]

        # Estimate double layer capacitance
        # C_dl = 1 / (2π * f_char * Rct)
        if Rct > 0 and f_char > 0:
            C_dl = 1 / (2 * np.pi * f_char * Rct)
        else:
            C_dl = None

        results = {
            'solution_resistance_ohm': Rs,
            'charge_transfer_resistance_ohm': Rct,
            'characteristic_frequency_Hz': f_char,
            'double_layer_capacitance_F': C_dl,
            'total_resistance_ohm': z_real[low_freq_idx]
        }

        self.eis_data = {
            'frequency': frequency.tolist(),
            'z_real': z_real.tolist(),
            'z_imag': z_imag.tolist(),
            'z_magnitude': z_mag.tolist(),
            'phase': phase.tolist(),
            'analysis': results
        }

        return results

    def analyze_stability(self, time, current_or_potential, test_type='chronoamperometry'):
        """
        Analyze stability test data.

        Args:
            time: Array of time values (s or h)
            current_or_potential: Array of current (for chronoamperometry) or potential (for chronopotentiometry)
            test_type: 'chronoamperometry' or 'chronopotentiometry'

        Returns:
            Dictionary with stability analysis results
        """
        time = np.array(time)
        signal = np.array(current_or_potential)

        # Calculate initial and final values
        initial_value = np.mean(signal[:min(10, len(signal)//10)])
        final_value = np.mean(signal[-min(10, len(signal)//10):])

        # Calculate retention
        retention = (final_value / initial_value) * 100 if initial_value != 0 else 0

        # Calculate degradation rate (linear fit)
        coeffs = np.polyfit(time, signal, 1)
        degradation_rate = coeffs[0]

        # Calculate time to 90% retention
        if degradation_rate < 0:
            time_to_90 = (0.9 * initial_value - coeffs[1]) / coeffs[0]
            time_to_90 = time_to_90 if time_to_90 > 0 else None
        else:
            time_to_90 = None

        results = {
            'test_type': test_type,
            'initial_value': initial_value,
            'final_value': final_value,
            'retention_percent': retention,
            'degradation_rate_per_hour': degradation_rate * 3600 if time[-1] < 1000 else degradation_rate,
            'time_to_90_percent': time_to_90,
            'stability_rating': 'excellent' if retention > 95 else 'good' if retention > 90 else 'moderate' if retention > 80 else 'poor'
        }

        return results

    def plot_cv(self, output_path=None, title="Cyclic Voltammetry"):
        """Plot CV data."""
        if self.cv_data is None:
            return None

        fig, ax = plt.subplots(figsize=(8, 6))

        potential = np.array(self.cv_data['potential'])
        current = np.array(self.cv_data['current'])

        ax.plot(potential, current, 'b-', linewidth=2)
        ax.axhline(y=0, color='k', linestyle='--', linewidth=0.5)
        ax.axvline(x=0, color='k', linestyle='--', linewidth=0.5)

        ax.set_xlabel('Potential (V vs. Ref)', fontsize=12)
        ax.set_ylabel('Current (mA)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig

    def plot_tafel(self, output_path=None, title="Tafel Plot"):
        """Plot Tafel data."""
        if self.tafel_data is None:
            return None

        fig, ax = plt.subplots(figsize=(8, 6))

        log_j = np.array(self.tafel_data['log_current_density'])
        eta = np.array(self.tafel_data['overpotential'])

        ax.plot(log_j, eta * 1000, 'bo', markersize=6, label='Data')

        # Plot fit line
        tafel_slope = self.tafel_data['analysis']['tafel_slope_mV_dec'] / 1000
        intercept = -self.tafel_data['analysis']['exchange_current_density']

        log_j_fit = np.linspace(np.min(log_j), np.max(log_j), 100)
        eta_fit = tafel_slope * log_j_fit + intercept

        ax.plot(log_j_fit, eta_fit * 1000, 'r-', linewidth=2, label=f'Tafel slope: {tafel_slope*1000:.1f} mV/dec')

        ax.set_xlabel('log(j) [log(mA/cm²)]', fontsize=12)
        ax.set_ylabel('Overpotential (mV)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig

    def plot_nyquist(self, output_path=None, title="Nyquist Plot"):
        """Plot EIS Nyquist plot."""
        if self.eis_data is None:
            return None

        fig, ax = plt.subplots(figsize=(8, 8))

        z_real = np.array(self.eis_data['z_real'])
        z_imag = np.array(self.eis_data['z_imag'])

        ax.plot(z_real, -z_imag, 'bo-', markersize=6)
        ax.set_xlabel('Z\' (Ω)', fontsize=12)
        ax.set_ylabel('-Z\'\' (Ω)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.axis('equal')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig


def main():
    """Example usage."""
    # Example CV data
    potential = np.linspace(-0.5, 0.5, 100)
    current = 10 * np.sin(2 * np.pi * potential) + np.random.normal(0, 0.5, 100)

    analyzer = ElectrochemistryAnalyzer()
    cv_results = analyzer.analyze_cv(potential, current, scan_rate=50)
    print("CV Analysis:", json.dumps(cv_results, indent=2))


if __name__ == "__main__":
    main()
