#!/usr/bin/env python3
"""
Activity Metrics Module

Calculates catalytic activity metrics including:
- Conversion and yield
- Turnover frequency (TOF)
- Turnover number (TON)
- Space velocity calculations
- Reaction rates
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import sem, t
import json


class ActivityMetricsCalculator:
    """Calculator for catalytic activity metrics."""

    def __init__(self):
        """Initialize activity metrics calculator."""
        self.results = {}

    def calculate_conversion(self, reactant_in, reactant_out):
        """
        Calculate conversion.

        Conversion (%) = [(C_in - C_out) / C_in] × 100

        Args:
            reactant_in: Inlet concentration or flow rate
            reactant_out: Outlet concentration or flow rate

        Returns:
            Conversion percentage
        """
        if reactant_in == 0:
            return 0.0

        conversion = ((reactant_in - reactant_out) / reactant_in) * 100
        return max(0.0, min(100.0, conversion))  # Clamp between 0-100%

    def calculate_yield(self, product_out, reactant_in, stoichiometry=1.0):
        """
        Calculate yield.

        Yield (%) = (moles of product / (moles of reactant × stoichiometry)) × 100

        Args:
            product_out: Product concentration or flow rate
            reactant_in: Inlet reactant concentration or flow rate
            stoichiometry: Stoichiometric coefficient (product/reactant)

        Returns:
            Yield percentage
        """
        if reactant_in == 0:
            return 0.0

        yield_pct = (product_out / (reactant_in * stoichiometry)) * 100
        return max(0.0, min(100.0, yield_pct))

    def calculate_tof(self, reaction_rate, active_sites):
        """
        Calculate turnover frequency (TOF).

        TOF (h⁻¹) = reaction rate (mol/s) / number of active sites (mol) × 3600

        Args:
            reaction_rate: Reaction rate in mol/s
            active_sites: Number of active sites in mol

        Returns:
            TOF in h⁻¹
        """
        if active_sites == 0:
            return None

        tof = (reaction_rate / active_sites) * 3600  # Convert to h⁻¹
        return tof

    def calculate_ton(self, moles_converted, active_sites):
        """
        Calculate turnover number (TON).

        TON = total moles converted / number of active sites

        Args:
            moles_converted: Total moles of reactant converted
            active_sites: Number of active sites in mol

        Returns:
            TON (dimensionless)
        """
        if active_sites == 0:
            return None

        ton = moles_converted / active_sites
        return ton

    def calculate_space_velocity(self, flow_rate, catalyst_volume=None, catalyst_mass=None):
        """
        Calculate space velocity.

        GHSV (h⁻¹) = volumetric flow rate / catalyst volume
        WHSV (h⁻¹) = mass flow rate / catalyst mass

        Args:
            flow_rate: Flow rate (mL/min or g/h)
            catalyst_volume: Catalyst volume in mL (for GHSV)
            catalyst_mass: Catalyst mass in g (for WHSV)

        Returns:
            Dictionary with GHSV and/or WHSV
        """
        results = {}

        if catalyst_volume is not None and catalyst_volume > 0:
            # GHSV in h⁻¹
            ghsv = (flow_rate * 60) / catalyst_volume  # Convert mL/min to mL/h
            results['GHSV_h-1'] = ghsv

        if catalyst_mass is not None and catalyst_mass > 0:
            # WHSV in h⁻¹
            whsv = flow_rate / catalyst_mass
            results['WHSV_h-1'] = whsv

        return results

    def calculate_reaction_rate(self, conversion, flow_rate, catalyst_mass, reactant_conc=None):
        """
        Calculate reaction rate.

        Rate (mol/g/s) = (conversion × flow_rate × concentration) / catalyst_mass

        Args:
            conversion: Conversion fraction (0-1)
            flow_rate: Flow rate in mL/min
            catalyst_mass: Catalyst mass in g
            reactant_conc: Reactant concentration in mol/L (optional)

        Returns:
            Reaction rate in mol/g/s
        """
        if catalyst_mass == 0:
            return None

        # Convert flow rate to L/s
        flow_rate_L_s = flow_rate / (1000 * 60)

        if reactant_conc is not None:
            # Calculate molar flow rate
            molar_flow = flow_rate_L_s * reactant_conc  # mol/s
            rate = (conversion * molar_flow) / catalyst_mass  # mol/g/s
        else:
            # Return normalized rate
            rate = (conversion * flow_rate_L_s) / catalyst_mass

        return rate

    def calculate_productivity(self, product_flow, catalyst_mass, time=None):
        """
        Calculate catalyst productivity.

        Productivity (g_product/g_cat/h) = product flow rate / catalyst mass

        Args:
            product_flow: Product flow rate in g/h
            catalyst_mass: Catalyst mass in g
            time: Time period in hours (for cumulative productivity)

        Returns:
            Productivity in g_product/g_cat/h
        """
        if catalyst_mass == 0:
            return None

        productivity = product_flow / catalyst_mass

        if time is not None:
            # Cumulative productivity
            cumulative = productivity * time
            return {'productivity_g_g_h': productivity, 'cumulative_g_g': cumulative}

        return productivity

    def calculate_statistics(self, data_points):
        """
        Calculate statistical metrics for replicate measurements.

        Args:
            data_points: List or array of measurement values

        Returns:
            Dictionary with mean, std, sem, and confidence interval
        """
        data = np.array(data_points)

        if len(data) < 2:
            return {
                'mean': data[0] if len(data) == 1 else None,
                'std': None,
                'sem': None,
                'ci_95': None,
                'n': len(data)
            }

        mean = np.mean(data)
        std = np.std(data, ddof=1)
        standard_error = sem(data)

        # 95% confidence interval
        confidence = 0.95
        dof = len(data) - 1
        t_value = t.ppf((1 + confidence) / 2, dof)
        ci = t_value * standard_error

        return {
            'mean': mean,
            'std': std,
            'sem': standard_error,
            'ci_95': ci,
            'ci_95_range': (mean - ci, mean + ci),
            'n': len(data),
            'relative_std_pct': (std / mean * 100) if mean != 0 else None
        }

    def analyze_time_series(self, time, conversion):
        """
        Analyze conversion vs time data.

        Args:
            time: Array of time points (hours)
            conversion: Array of conversion values (%)

        Returns:
            Dictionary with time series analysis
        """
        time = np.array(time)
        conversion = np.array(conversion)

        # Initial and final conversion
        initial_conversion = conversion[0]
        final_conversion = conversion[-1]

        # Average conversion
        avg_conversion = np.mean(conversion)

        # Conversion change
        conversion_change = final_conversion - initial_conversion

        # Deactivation rate (if applicable)
        if len(time) > 1 and conversion_change < 0:
            # Linear fit for deactivation
            coeffs = np.polyfit(time, conversion, 1)
            deactivation_rate = coeffs[0]  # %/h
        else:
            deactivation_rate = None

        return {
            'initial_conversion_pct': initial_conversion,
            'final_conversion_pct': final_conversion,
            'average_conversion_pct': avg_conversion,
            'conversion_change_pct': conversion_change,
            'deactivation_rate_pct_h': deactivation_rate,
            'time_on_stream_h': time[-1] - time[0]
        }

    def plot_conversion_vs_time(self, time, conversion, output_path=None, title="Conversion vs Time"):
        """
        Plot conversion vs time.

        Args:
            time: Array of time points (hours)
            conversion: Array of conversion values (%)
            output_path: Path to save plot
            title: Plot title

        Returns:
            matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(time, conversion, 'bo-', linewidth=2, markersize=8, label='Conversion')

        ax.set_xlabel('Time on Stream (h)', fontsize=12)
        ax.set_ylabel('Conversion (%)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=10)

        # Add horizontal line at initial conversion
        ax.axhline(y=conversion[0], color='r', linestyle='--', alpha=0.5, label=f'Initial: {conversion[0]:.1f}%')

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig

    def plot_activity_comparison(self, materials, conversions, output_path=None, title="Activity Comparison"):
        """
        Plot bar chart comparing activity of different materials.

        Args:
            materials: List of material names
            conversions: List of conversion values (%)
            output_path: Path to save plot
            title: Plot title

        Returns:
            matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        x_pos = np.arange(len(materials))
        ax.bar(x_pos, conversions, color='steelblue', alpha=0.8, edgecolor='black')

        ax.set_xlabel('Material', fontsize=12)
        ax.set_ylabel('Conversion (%)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(materials, rotation=45, ha='right')
        ax.grid(True, axis='y', alpha=0.3)

        # Add value labels on bars
        for i, v in enumerate(conversions):
            ax.text(i, v + 1, f'{v:.1f}%', ha='center', va='bottom', fontsize=10)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig


# Example usage
if __name__ == "__main__":
    calc = ActivityMetricsCalculator()

    # Example: Calculate conversion
    conversion = calc.calculate_conversion(reactant_in=100, reactant_out=25)
    print(f"Conversion: {conversion:.2f}%")

    # Example: Calculate TOF
    tof = calc.calculate_tof(reaction_rate=1e-6, active_sites=1e-8)
    print(f"TOF: {tof:.2f} h⁻¹")

    # Example: Statistics
    data = [75.2, 76.1, 74.8, 75.5, 76.3]
    stats = calc.calculate_statistics(data)
    print(f"Mean: {stats['mean']:.2f} ± {stats['ci_95']:.2f}%")
