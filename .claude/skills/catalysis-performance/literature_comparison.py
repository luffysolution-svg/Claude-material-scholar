#!/usr/bin/env python3
"""
Literature Comparison Module

Compares experimental results with literature values including:
- Benchmark table generation
- Performance ranking
- Statistical comparison
- Literature data extraction
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind
import json


class LiteratureComparison:
    """Compare experimental results with literature."""

    def __init__(self):
        """Initialize literature comparison."""
        self.literature_data = []

    def add_literature_data(self, reference, data):
        """
        Add literature data for comparison.

        Args:
            reference: Citation or reference identifier
            data: Dictionary with performance metrics
        """
        entry = {
            'reference': reference,
            'data': data
        }
        self.literature_data.append(entry)

    def load_from_zotero_notes(self, notes_data):
        """
        Load literature data from Zotero notes.

        Args:
            notes_data: List of dictionaries from Zotero notes
        """
        for note in notes_data:
            if 'reference' in note and 'performance_data' in note:
                self.add_literature_data(note['reference'], note['performance_data'])

    def compare_conversion(self, experimental_conversion, metric='conversion'):
        """
        Compare experimental conversion with literature.

        Args:
            experimental_conversion: Experimental conversion value
            metric: Metric name (default: 'conversion')

        Returns:
            Dictionary with comparison results
        """
        if not self.literature_data:
            return {'error': 'No literature data available'}

        lit_values = []
        references = []

        for entry in self.literature_data:
            if metric in entry['data']:
                lit_values.append(entry['data'][metric])
                references.append(entry['reference'])

        if not lit_values:
            return {'error': f'No literature data for metric: {metric}'}

        lit_values = np.array(lit_values)

        # Calculate statistics
        lit_mean = np.mean(lit_values)
        lit_std = np.std(lit_values)
        lit_min = np.min(lit_values)
        lit_max = np.max(lit_values)

        # Percentile ranking
        percentile = (np.sum(lit_values < experimental_conversion) / len(lit_values)) * 100

        # Performance category
        if experimental_conversion >= lit_max:
            category = 'Best-in-class'
        elif experimental_conversion >= lit_mean + lit_std:
            category = 'Above average'
        elif experimental_conversion >= lit_mean:
            category = 'Average'
        elif experimental_conversion >= lit_mean - lit_std:
            category = 'Below average'
        else:
            category = 'Poor'

        results = {
            'experimental_value': experimental_conversion,
            'literature_mean': lit_mean,
            'literature_std': lit_std,
            'literature_min': lit_min,
            'literature_max': lit_max,
            'percentile_rank': percentile,
            'performance_category': category,
            'n_references': len(lit_values),
            'improvement_over_mean_%': ((experimental_conversion - lit_mean) / lit_mean * 100) if lit_mean > 0 else 0
        }

        return results

    def generate_benchmark_table(self, experimental_data, metrics=['conversion', 'selectivity', 'TOF']):
        """
        Generate benchmark comparison table.

        Args:
            experimental_data: Dictionary with experimental metrics
            metrics: List of metrics to compare

        Returns:
            DataFrame with benchmark comparison
        """
        rows = []

        # Add experimental data
        exp_row = {'Reference': 'This work', 'Type': 'Experimental'}
        for metric in metrics:
            exp_row[metric] = experimental_data.get(metric, None)
        rows.append(exp_row)

        # Add literature data
        for entry in self.literature_data:
            lit_row = {'Reference': entry['reference'], 'Type': 'Literature'}
            for metric in metrics:
                lit_row[metric] = entry['data'].get(metric, None)
            rows.append(lit_row)

        df = pd.DataFrame(rows)

        # Calculate rankings for each metric
        for metric in metrics:
            if metric in df.columns:
                df[f'{metric}_rank'] = df[metric].rank(ascending=False, method='min')

        return df

    def statistical_comparison(self, experimental_values, metric='conversion'):
        """
        Perform statistical comparison with literature.

        Args:
            experimental_values: List of experimental replicate values
            metric: Metric name

        Returns:
            Dictionary with statistical test results
        """
        if not self.literature_data:
            return {'error': 'No literature data available'}

        lit_values = []
        for entry in self.literature_data:
            if metric in entry['data']:
                lit_values.append(entry['data'][metric])

        if len(lit_values) < 2 or len(experimental_values) < 2:
            return {'error': 'Insufficient data for statistical comparison'}

        # Perform t-test
        t_stat, p_value = ttest_ind(experimental_values, lit_values)

        # Determine significance
        if p_value < 0.001:
            significance = 'Highly significant (p < 0.001)'
        elif p_value < 0.01:
            significance = 'Very significant (p < 0.01)'
        elif p_value < 0.05:
            significance = 'Significant (p < 0.05)'
        else:
            significance = 'Not significant (p ≥ 0.05)'

        exp_mean = np.mean(experimental_values)
        lit_mean = np.mean(lit_values)

        results = {
            't_statistic': t_stat,
            'p_value': p_value,
            'significance': significance,
            'experimental_mean': exp_mean,
            'literature_mean': lit_mean,
            'difference': exp_mean - lit_mean,
            'better_than_literature': exp_mean > lit_mean
        }

        return results

    def rank_catalysts(self, experimental_data, weight_factors=None):
        """
        Rank catalysts including experimental and literature data.

        Args:
            experimental_data: Dictionary with experimental metrics
            weight_factors: Dictionary with weights for each metric

        Returns:
            DataFrame with ranked catalysts
        """
        if weight_factors is None:
            weight_factors = {'conversion': 0.4, 'selectivity': 0.4, 'TOF': 0.2}

        # Collect all data
        all_data = [{'reference': 'This work', **experimental_data}]
        for entry in self.literature_data:
            all_data.append({'reference': entry['reference'], **entry['data']})

        df = pd.DataFrame(all_data)

        # Normalize metrics (0-1 scale)
        normalized_df = df.copy()
        metrics = list(weight_factors.keys())

        for metric in metrics:
            if metric in df.columns:
                max_val = df[metric].max()
                min_val = df[metric].min()
                if max_val > min_val:
                    normalized_df[f'{metric}_norm'] = (df[metric] - min_val) / (max_val - min_val)
                else:
                    normalized_df[f'{metric}_norm'] = 1.0

        # Calculate weighted score
        normalized_df['weighted_score'] = 0
        for metric, weight in weight_factors.items():
            if f'{metric}_norm' in normalized_df.columns:
                normalized_df['weighted_score'] += normalized_df[f'{metric}_norm'] * weight

        # Rank by weighted score
        normalized_df['rank'] = normalized_df['weighted_score'].rank(ascending=False, method='min')
        normalized_df = normalized_df.sort_values('rank')

        return normalized_df

    def plot_benchmark_comparison(self, experimental_data, metric='conversion', output_path=None):
        """
        Plot benchmark comparison bar chart.

        Args:
            experimental_data: Dictionary with experimental metrics
            metric: Metric to plot
            output_path: Path to save plot

        Returns:
            matplotlib figure
        """
        # Collect data
        references = ['This work']
        values = [experimental_data.get(metric, 0)]

        for entry in self.literature_data:
            if metric in entry['data']:
                references.append(entry['reference'])
                values.append(entry['data'][metric])

        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))

        colors = ['#2E86AB' if ref == 'This work' else '#A23B72' for ref in references]

        bars = ax.bar(range(len(references)), values, color=colors, alpha=0.8, edgecolor='black')

        # Highlight this work
        bars[0].set_linewidth(3)

        ax.set_xlabel('Reference', fontsize=12, fontweight='bold')
        ax.set_ylabel(f'{metric.capitalize()} (%)', fontsize=12, fontweight='bold')
        ax.set_title(f'Benchmark Comparison: {metric.capitalize()}', fontsize=14, fontweight='bold')
        ax.set_xticks(range(len(references)))
        ax.set_xticklabels(references, rotation=45, ha='right')
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        # Add value labels on bars
        for i, (bar, val) in enumerate(zip(bars, values)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{val:.1f}',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig

    def generate_comparison_summary(self, experimental_data):
        """
        Generate text summary of comparison with literature.

        Args:
            experimental_data: Dictionary with experimental metrics

        Returns:
            String with comparison summary
        """
        summary = "## Literature Comparison Summary\n\n"

        for metric, value in experimental_data.items():
            comparison = self.compare_conversion(value, metric)

            if 'error' not in comparison:
                summary += f"### {metric.capitalize()}\n\n"
                summary += f"- **Experimental value**: {value:.2f}\n"
                summary += f"- **Literature mean**: {comparison['literature_mean']:.2f} ± {comparison['literature_std']:.2f}\n"
                summary += f"- **Literature range**: {comparison['literature_min']:.2f} - {comparison['literature_max']:.2f}\n"
                summary += f"- **Percentile rank**: {comparison['percentile_rank']:.1f}%\n"
                summary += f"- **Performance category**: {comparison['performance_category']}\n"
                summary += f"- **Improvement over mean**: {comparison['improvement_over_mean_%']:.1f}%\n\n"

        return summary
