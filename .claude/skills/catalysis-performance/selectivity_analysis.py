#!/usr/bin/env python3
"""
Selectivity Analysis Module

Analyzes product selectivity including:
- Product distribution
- Regioselectivity
- Stereoselectivity
- Carbon balance
- Selectivity trends
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import sem, t
import json


class SelectivityAnalyzer:
    """Analyzer for product selectivity."""

    def __init__(self):
        """Initialize selectivity analyzer."""
        self.results = {}

    def calculate_selectivity(self, product_amounts, target_product_idx=0):
        """
        Calculate selectivity for each product.

        Selectivity (%) = (amount of product i / total products) × 100

        Args:
            product_amounts: Dictionary or list of product amounts {product_name: amount}
            target_product_idx: Index or name of target product

        Returns:
            Dictionary with selectivity for each product
        """
        if isinstance(product_amounts, dict):
            products = product_amounts
            total = sum(products.values())
        else:
            products = {f"Product_{i}": amt for i, amt in enumerate(product_amounts)}
            total = sum(product_amounts)

        if total == 0:
            return {prod: 0.0 for prod in products.keys()}

        selectivities = {prod: (amt / total) * 100 for prod, amt in products.items()}

        return selectivities

    def calculate_target_selectivity(self, target_product, total_products):
        """
        Calculate selectivity toward target product.

        Args:
            target_product: Amount of target product
            total_products: Total amount of all products

        Returns:
            Target selectivity percentage
        """
        if total_products == 0:
            return 0.0

        selectivity = (target_product / total_products) * 100
        return min(100.0, selectivity)

    def calculate_carbon_balance(self, carbon_in, carbon_out):
        """
        Calculate carbon balance.

        Carbon balance (%) = (carbon out / carbon in) × 100

        Args:
            carbon_in: Total carbon atoms in reactants
            carbon_out: Total carbon atoms in products

        Returns:
            Carbon balance percentage
        """
        if carbon_in == 0:
            return 0.0

        balance = (carbon_out / carbon_in) * 100
        return balance

    def calculate_product_distribution(self, products_dict):
        """
        Calculate product distribution with molar and mass basis.

        Args:
            products_dict: Dictionary {product_name: {'moles': x, 'mw': y}}

        Returns:
            Dictionary with molar and mass distributions
        """
        total_moles = sum(p['moles'] for p in products_dict.values())
        total_mass = sum(p['moles'] * p.get('mw', 1) for p in products_dict.values())

        distribution = {}

        for product, data in products_dict.items():
            moles = data['moles']
            mw = data.get('mw', 1)
            mass = moles * mw

            distribution[product] = {
                'moles': moles,
                'mass': mass,
                'molar_fraction': moles / total_moles if total_moles > 0 else 0,
                'mass_fraction': mass / total_mass if total_mass > 0 else 0,
                'molar_selectivity_%': (moles / total_moles * 100) if total_moles > 0 else 0,
                'mass_selectivity_%': (mass / total_mass * 100) if total_mass > 0 else 0
            }

        return distribution

    def calculate_regioselectivity(self, isomer_amounts):
        """
        Calculate regioselectivity (ratio of positional isomers).

        Args:
            isomer_amounts: Dictionary {isomer_name: amount}

        Returns:
            Dictionary with regioselectivity ratios
        """
        total = sum(isomer_amounts.values())

        if total == 0:
            return {}

        regioselectivity = {}

        isomer_list = list(isomer_amounts.keys())
        for i, isomer1 in enumerate(isomer_list):
            for isomer2 in isomer_list[i+1:]:
                ratio_name = f"{isomer1}/{isomer2}"
                if isomer_amounts[isomer2] > 0:
                    ratio = isomer_amounts[isomer1] / isomer_amounts[isomer2]
                    regioselectivity[ratio_name] = ratio
                else:
                    regioselectivity[ratio_name] = float('inf')

        # Also include percentages
        for isomer, amount in isomer_amounts.items():
            regioselectivity[f"{isomer}_%"] = (amount / total) * 100

        return regioselectivity

    def calculate_stereoselectivity(self, enantiomer_amounts):
        """
        Calculate stereoselectivity (enantiomeric excess, diastereomeric ratio).

        Args:
            enantiomer_amounts: Dictionary {enantiomer_name: amount}

        Returns:
            Dictionary with ee, de, or dr values
        """
        results = {}

        if len(enantiomer_amounts) == 2:
            # Enantiomeric excess (ee)
            amounts = list(enantiomer_amounts.values())
            major = max(amounts)
            minor = min(amounts)
            total = sum(amounts)

            if total > 0:
                ee = ((major - minor) / total) * 100
                results['enantiomeric_excess_%'] = ee
                results['major_enantiomer_%'] = (major / total) * 100
                results['minor_enantiomer_%'] = (minor / total) * 100

        elif len(enantiomer_amounts) > 2:
            # Diastereomeric ratio (dr)
            total = sum(enantiomer_amounts.values())
            for name, amount in enantiomer_amounts.items():
                results[f"{name}_%"] = (amount / total) * 100 if total > 0 else 0

            # Calculate major:minor ratio
            amounts = sorted(enantiomer_amounts.values(), reverse=True)
            if len(amounts) >= 2 and amounts[1] > 0:
                results['dr_major:minor'] = amounts[0] / amounts[1]

        return results

    def analyze_selectivity_trends(self, conditions, selectivities):
        """
        Analyze selectivity trends with reaction conditions.

        Args:
            conditions: Array of condition values (e.g., temperature, pressure)
            selectivities: Array of selectivity values

        Returns:
            Dictionary with trend analysis
        """
        conditions = np.array(conditions)
        selectivities = np.array(selectivities)

        # Linear fit
        coeffs = np.polyfit(conditions, selectivities, 1)
        slope = coeffs[0]
        intercept = coeffs[1]

        # Calculate R²
        y_pred = np.polyval(coeffs, conditions)
        ss_res = np.sum((selectivities - y_pred)**2)
        ss_tot = np.sum((selectivities - np.mean(selectivities))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # Determine trend
        if abs(slope) < 0.01:
            trend = "constant"
        elif slope > 0:
            trend = "increasing"
        else:
            trend = "decreasing"

        results = {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_squared,
            'trend': trend,
            'correlation': 'strong' if r_squared > 0.8 else 'moderate' if r_squared > 0.5 else 'weak'
        }

        return results

    def calculate_selectivity_statistics(self, selectivity_replicates):
        """
        Calculate statistics for replicate selectivity measurements.

        Args:
            selectivity_replicates: List of selectivity values

        Returns:
            Dictionary with statistical metrics
        """
        data = np.array(selectivity_replicates)

        if len(data) < 2:
            return {
                'mean': data[0] if len(data) == 1 else None,
                'std': None,
                'sem': None,
                'ci_95': None
            }

        mean = np.mean(data)
        std = np.std(data, ddof=1)
        standard_error = sem(data)

        # 95% confidence interval
        confidence = 0.95
        dof = len(data) - 1
        t_value = t.ppf((1 + confidence) / 2, dof)
        ci = t_value * standard_error

        results = {
            'mean': mean,
            'std': std,
            'sem': standard_error,
            'ci_95': (mean - ci, mean + ci),
            'relative_std_%': (std / mean * 100) if mean > 0 else None
        }

        return results

    def plot_product_distribution(self, products_dict, output_path=None, title="Product Distribution"):
        """
        Plot product distribution as pie chart and bar chart.

        Args:
            products_dict: Dictionary with product distribution
            output_path: Path to save plot
            title: Plot title

        Returns:
            matplotlib figure object
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        products = list(products_dict.keys())
        selectivities = [products_dict[p]['molar_selectivity_%'] for p in products]

        # Pie chart
        colors = plt.cm.Set3(np.linspace(0, 1, len(products)))
        ax1.pie(selectivities, labels=products, autopct='%1.1f%%', colors=colors, startangle=90)
        ax1.set_title(f"{title} - Molar Basis")

        # Bar chart
        ax2.bar(products, selectivities, color=colors, edgecolor='black', linewidth=1.5)
        ax2.set_ylabel('Selectivity (%)', fontsize=12)
        ax2.set_title(f"{title} - Selectivity")
        ax2.set_ylim(0, 100)
        ax2.grid(axis='y', alpha=0.3)

        # Rotate x labels if needed
        if len(max(products, key=len)) > 10:
            ax2.set_xticklabels(products, rotation=45, ha='right')

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig

    def plot_selectivity_vs_conversion(self, conversions, selectivities, product_names=None,
                                      output_path=None, title="Selectivity vs Conversion"):
        """
        Plot selectivity as function of conversion.

        Args:
            conversions: Array of conversion values
            selectivities: Array or dict of selectivity values for each product
            product_names: List of product names
            output_path: Path to save plot
            title: Plot title

        Returns:
            matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        conversions = np.array(conversions)

        if isinstance(selectivities, dict):
            for product, sel_values in selectivities.items():
                ax.plot(conversions, sel_values, marker='o', linewidth=2, markersize=8, label=product)
        else:
            selectivities = np.array(selectivities)
            label = product_names[0] if product_names else "Product"
            ax.plot(conversions, selectivities, marker='o', linewidth=2, markersize=8, label=label)

        ax.set_xlabel('Conversion (%)', fontsize=12)
        ax.set_ylabel('Selectivity (%)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig

    def generate_selectivity_report(self, analysis_results):
        """
        Generate text report of selectivity analysis.

        Args:
            analysis_results: Dictionary with all selectivity results

        Returns:
            Formatted text report
        """
        report = "# Selectivity Analysis Report\n\n"

        if 'product_distribution' in analysis_results:
            report += "## Product Distribution\n\n"
            for product, data in analysis_results['product_distribution'].items():
                report += f"- **{product}**: {data['molar_selectivity_%']:.2f}% (molar), {data['mass_selectivity_%']:.2f}% (mass)\n"
            report += "\n"

        if 'carbon_balance' in analysis_results:
            cb = analysis_results['carbon_balance']
            report += f"## Carbon Balance\n\n**{cb:.2f}%**\n\n"
            if cb < 95:
                report += "*Note: Carbon balance < 95% suggests undetected products or measurement errors.*\n\n"

        if 'regioselectivity' in analysis_results:
            report += "## Regioselectivity\n\n"
            for key, value in analysis_results['regioselectivity'].items():
                if '/' in key:
                    report += f"- {key} ratio: {value:.2f}\n"
                else:
                    report += f"- {key}: {value:.2f}%\n"
            report += "\n"

        if 'stereoselectivity' in analysis_results:
            report += "## Stereoselectivity\n\n"
            for key, value in analysis_results['stereoselectivity'].items():
                report += f"- {key}: {value:.2f}\n"
            report += "\n"

        return report
