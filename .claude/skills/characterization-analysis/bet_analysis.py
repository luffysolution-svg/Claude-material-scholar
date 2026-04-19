#!/usr/bin/env python3
"""
BET Analysis Module

Analyzes BET (Brunauer-Emmett-Teller) surface area data including:
- Surface area calculation
- Pore size distribution
- Isotherm classification (Type I-VI)
- Pore volume determination
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import linregress
import json


class BETAnalyzer:
    """Analyzer for BET surface area and porosity data."""

    def __init__(self, relative_pressure=None, quantity_adsorbed=None):
        """
        Initialize BET analyzer.

        Args:
            relative_pressure: Array of P/P0 values (0-1), optional
            quantity_adsorbed: Array of adsorbed quantity (cm3/g STP or mmol/g), optional
        """
        self.p_p0 = np.array(relative_pressure) if relative_pressure is not None else None
        self.q_ads = np.array(quantity_adsorbed) if quantity_adsorbed is not None else None
        self.bet_results = None
        self.isotherm_type = None

    def load_data(self, relative_pressure, quantity_adsorbed):
        """Load or replace isotherm data."""
        self.p_p0 = np.array(relative_pressure)
        self.q_ads = np.array(quantity_adsorbed)

    def calculate_bet_surface_area(self, p_p0=None, q_ads=None, p_p0_range=(0.05, 0.3), cross_section=0.162):
        """
        Calculate BET surface area.

        BET equation: (P/P0) / [Q(1-P/P0)] = 1/(Q_m*C) + (C-1)/(Q_m*C) * (P/P0)

        Args:
            p_p0: Relative pressure array (uses instance data if None)
            q_ads: Quantity adsorbed array (uses instance data if None)
            p_p0_range: Tuple of (min, max) relative pressure for BET analysis
            cross_section: Cross-sectional area of adsorbate molecule (nm2)
                          Default: 0.162 nm2 for N2 at 77K

        Returns:
            Dictionary with BET surface area and parameters
        """
        if p_p0 is not None:
            self.load_data(p_p0, q_ads)
        if self.p_p0 is None:
            raise ValueError("No data loaded. Pass p_p0/q_ads or call load_data() first.")

        # Select data in BET range
        mask = (self.p_p0 >= p_p0_range[0]) & (self.p_p0 <= p_p0_range[1])
        p_p0_bet = self.p_p0[mask]
        q_ads_bet = self.q_ads[mask]

        # Calculate BET transform: y = (P/P0) / [Q(1-P/P0)]
        y = p_p0_bet / (q_ads_bet * (1 - p_p0_bet))
        x = p_p0_bet

        # Linear regression
        slope, intercept, r_value, p_value, std_err = linregress(x, y)

        # Calculate BET parameters
        C = 1 + (slope / intercept)  # BET constant
        Q_m = 1 / (slope + intercept)  # Monolayer capacity (cm³/g STP)

        # Calculate surface area
        # S_BET = (Q_m * N_A * σ) / V_m
        # where N_A = Avogadro's number, σ = cross-section, V_m = molar volume (22414 cm³/mol at STP)
        N_A = 6.022e23  # molecules/mol
        V_m = 22414  # cm³/mol at STP
        sigma_m2 = cross_section * 1e-18  # Convert nm² to m²

        S_BET = (Q_m * N_A * sigma_m2) / V_m  # m²/g

        self.bet_results = {
            'surface_area_m2_g': S_BET,
            'monolayer_capacity': Q_m,
            'BET_constant': C,
            'correlation_coefficient': r_value,
            'r_squared': r_value**2,
            'p_p0_range': p_p0_range
        }

        return self.bet_results

    def classify_isotherm(self):
        """
        Classify isotherm type according to IUPAC classification.

        Type I: Microporous materials (sharp uptake at low P/P0)
        Type II: Non-porous or macroporous materials (gradual uptake)
        Type III: Weak adsorbent-adsorbate interactions
        Type IV: Mesoporous materials (hysteresis loop)
        Type V: Weak interactions with mesopores
        Type VI: Stepwise multilayer adsorption

        Returns:
            Isotherm type classification
        """
        # Calculate uptake at different P/P0 ranges
        low_p = self.q_ads[self.p_p0 < 0.1]
        mid_p = self.q_ads[(self.p_p0 >= 0.1) & (self.p_p0 < 0.4)]
        high_p = self.q_ads[self.p_p0 >= 0.4]

        if len(low_p) == 0 or len(mid_p) == 0 or len(high_p) == 0:
            return "Insufficient data for classification"

        # Calculate relative uptakes
        low_uptake = np.mean(low_p) / np.max(self.q_ads)
        mid_uptake = np.mean(mid_p) / np.max(self.q_ads)

        # Classification logic
        if low_uptake > 0.7:
            isotherm_type = "Type I (Microporous)"
        elif low_uptake < 0.3 and mid_uptake < 0.5:
            isotherm_type = "Type III (Weak interactions)"
        elif low_uptake > 0.4 and mid_uptake > 0.6:
            isotherm_type = "Type IV (Mesoporous)"
        else:
            isotherm_type = "Type II (Non-porous/Macroporous)"

        self.isotherm_type = isotherm_type
        return isotherm_type

    def calculate_pore_volume(self, p_p0_threshold=0.95):
        """
        Calculate total pore volume at high relative pressure.

        Args:
            p_p0_threshold: Relative pressure for pore volume calculation (default: 0.95)

        Returns:
            Total pore volume in cm³/g
        """
        # Find quantity adsorbed at threshold P/P0
        idx = np.argmin(np.abs(self.p_p0 - p_p0_threshold))
        q_at_threshold = self.q_ads[idx]

        # Convert from cm³/g STP to cm³/g liquid
        # Liquid N2 density at 77K: 0.808 g/cm³
        # Molar volume at STP: 22414 cm³/mol
        # N2 molar mass: 28.014 g/mol
        rho_liquid = 0.808  # g/cm³
        M_N2 = 28.014  # g/mol
        V_m = 22414  # cm³/mol

        V_pore = (q_at_threshold * M_N2) / (V_m * rho_liquid)

        return V_pore

    def calculate_pore_size_distribution(self, method='BJH'):
        """
        Calculate pore size distribution using BJH method.

        Args:
            method: Method for PSD calculation ('BJH' or 'DFT')

        Returns:
            Dictionary with pore size distribution data
        """
        if method == 'BJH':
            # Simplified BJH calculation
            # For full implementation, would need desorption branch data

            # Calculate average pore diameter using 4V/S approximation
            if self.bet_results is None:
                self.calculate_bet_surface_area()

            V_pore = self.calculate_pore_volume()
            S_BET = self.bet_results['surface_area_m2_g']

            # Average pore diameter (nm)
            d_avg = (4 * V_pore * 1000) / S_BET  # Convert cm³ to nm³

            psd_results = {
                'method': 'BJH (simplified)',
                'average_pore_diameter_nm': d_avg,
                'total_pore_volume_cm3_g': V_pore,
                'note': 'Full BJH requires desorption branch data'
            }

        else:
            psd_results = {
                'method': method,
                'note': f'{method} method not yet implemented'
            }

        return psd_results

    def plot_isotherm(self, output_path=None, title="N2 Adsorption Isotherm"):
        """
        Plot adsorption isotherm.

        Args:
            output_path: Path to save plot (optional)
            title: Plot title

        Returns:
            matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot isotherm
        ax.plot(self.p_p0, self.q_ads, 'bo-', linewidth=2, markersize=6, label='Adsorption')

        ax.set_xlabel('Relative Pressure (P/P₀)', fontsize=12)
        ax.set_ylabel('Quantity Adsorbed (cm³/g STP)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()

        # Add isotherm type annotation if classified
        if self.isotherm_type:
            ax.text(
                0.95, 0.05,
                f'Isotherm Type: {self.isotherm_type}',
                transform=ax.transAxes,
                fontsize=10,
                verticalalignment='bottom',
                horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            )

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig

    def plot_bet_transform(self, output_path=None):
        """
        Plot BET transform to show linearity.

        Returns:
            matplotlib figure object
        """
        if self.bet_results is None:
            self.calculate_bet_surface_area()

        p_p0_range = self.bet_results['p_p0_range']
        mask = (self.p_p0 >= p_p0_range[0]) & (self.p_p0 <= p_p0_range[1])
        p_p0_bet = self.p_p0[mask]
        q_ads_bet = self.q_ads[mask]

        # BET transform
        y = p_p0_bet / (q_ads_bet * (1 - p_p0_bet))
        x = p_p0_bet

        # Linear fit
        slope = (self.bet_results['BET_constant'] - 1) / self.bet_results['monolayer_capacity']
        intercept = 1 / (self.bet_results['monolayer_capacity'] * self.bet_results['BET_constant'])
        y_fit = slope * x + intercept

        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(x, y, 'bo', markersize=8, label='Data')
        ax.plot(x, y_fit, 'r-', linewidth=2, label='Linear Fit')

        ax.set_xlabel('Relative Pressure (P/P₀)', fontsize=12)
        ax.set_ylabel('(P/P₀) / [Q(1-P/P₀)]', fontsize=12)
        ax.set_title('BET Transform', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()

        # Add R² annotation
        ax.text(
            0.05, 0.95,
            f'R² = {self.bet_results["r_squared"]:.4f}\nS_BET = {self.bet_results["surface_area_m2_g"]:.1f} m²/g',
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5)
        )

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig

    def generate_report(self):
        """
        Generate comprehensive BET analysis report.

        Returns:
            Dictionary with all analysis results
        """
        if self.bet_results is None:
            self.calculate_bet_surface_area()

        if self.isotherm_type is None:
            self.classify_isotherm()

        pore_volume = self.calculate_pore_volume()
        psd = self.calculate_pore_size_distribution()

        report = {
            'bet_surface_area': self.bet_results,
            'isotherm_type': self.isotherm_type,
            'pore_volume_cm3_g': pore_volume,
            'pore_size_distribution': psd
        }

        return report


def analyze_bet_data(file_path, output_dir=None):
    """
    Analyze BET data from file.

    Args:
        file_path: Path to data file (CSV or TXT)
        output_dir: Directory to save plots and results

    Returns:
        BET analysis report
    """
    # Load data
    try:
        data = pd.read_csv(file_path)
        p_p0 = data.iloc[:, 0].values
        q_ads = data.iloc[:, 1].values
    except Exception as e:
        raise ValueError(f"Error loading data: {e}")

    # Create analyzer
    analyzer = BETAnalyzer(p_p0, q_ads)

    # Perform analysis
    report = analyzer.generate_report()

    # Generate plots
    if output_dir:
        import os
        os.makedirs(output_dir, exist_ok=True)

        analyzer.plot_isotherm(
            output_path=os.path.join(output_dir, 'bet_isotherm.png')
        )
        analyzer.plot_bet_transform(
            output_path=os.path.join(output_dir, 'bet_transform.png')
        )

        # Save report as JSON
        with open(os.path.join(output_dir, 'bet_report.json'), 'w') as f:
            json.dump(report, f, indent=2)

    return report


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='BET Surface Area Analysis')
    parser.add_argument('input_file', help='Path to BET data file (CSV)')
    parser.add_argument('--output', '-o', help='Output directory for plots and results')

    args = parser.parse_args()

    report = analyze_bet_data(args.input_file, args.output)

    print("\n=== BET Analysis Report ===\n")
    print(f"Surface Area: {report['bet_surface_area']['surface_area_m2_g']:.2f} m²/g")
    print(f"Isotherm Type: {report['isotherm_type']}")
    print(f"Pore Volume: {report['pore_volume_cm3_g']:.3f} cm³/g")
    print(f"Average Pore Diameter: {report['pore_size_distribution']['average_pore_diameter_nm']:.2f} nm")
