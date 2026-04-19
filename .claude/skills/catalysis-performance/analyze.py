#!/usr/bin/env python3
"""
Main Catalysis Performance Analysis Script

Orchestrates catalysis performance evaluation using specialized modules.
"""

import sys
import json
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Import analysis modules
from activity_metrics import ActivityMetricsCalculator
from selectivity_analysis import SelectivityAnalyzer
from stability_analysis import StabilityAnalyzer
from arrhenius_analysis import ArrheniusAnalyzer
from literature_comparison import LiteratureComparison


def load_data_file(file_path):
    """Load experimental data file."""
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    if file_path.suffix == '.csv':
        df = pd.read_csv(file_path)
    elif file_path.suffix in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)
    elif file_path.suffix == '.txt':
        df = pd.read_csv(file_path, sep=None, engine='python')
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

    return df


def analyze_activity(df, catalyst_props, reaction_conds):
    """Analyze catalytic activity."""
    calc = ActivityMetricsCalculator()
    results = {}

    # Extract data columns
    if 'Conversion' in df.columns:
        conversions = df['Conversion'].values
        results['conversion_mean'] = np.mean(conversions)
        results['conversion_std'] = np.std(conversions)

        stats = calc.calculate_statistics(conversions)
        results['conversion_stats'] = stats

    if 'Yield' in df.columns:
        yields = df['Yield'].values
        results['yield_mean'] = np.mean(yields)
        results['yield_std'] = np.std(yields)

    # Calculate TOF if active sites provided
    if 'active_sites_mol' in catalyst_props and 'Conversion' in df.columns:
        # Estimate reaction rate
        if 'flow_rate_mL_min' in reaction_conds and 'reactant_conc_mol_L' in reaction_conds:
            flow_rate = reaction_conds['flow_rate_mL_min']
            conc = reaction_conds['reactant_conc_mol_L']
            cat_mass = catalyst_props.get('mass_g', 1.0)

            conversion = results['conversion_mean'] / 100  # Convert to fraction
            rate = calc.calculate_reaction_rate(conversion, flow_rate, cat_mass, conc)

            active_sites = catalyst_props['active_sites_mol']
            tof = calc.calculate_tof(rate, active_sites)
            results['TOF_h-1'] = tof

    # Calculate space velocity
    if 'flow_rate_mL_min' in reaction_conds:
        flow_rate = reaction_conds['flow_rate_mL_min']
        cat_volume = catalyst_props.get('volume_mL', None)
        cat_mass = catalyst_props.get('mass_g', None)

        sv = calc.calculate_space_velocity(flow_rate, cat_volume, cat_mass)
        results.update(sv)

    return results


def analyze_selectivity(df):
    """Analyze product selectivity."""
    analyzer = SelectivityAnalyzer()
    results = {}

    # Check for product columns
    product_cols = [col for col in df.columns if col.startswith('Product_')]

    if product_cols:
        # Calculate selectivity
        product_amounts = {}
        for col in product_cols:
            product_amounts[col] = df[col].mean()

        selectivities = analyzer.calculate_selectivity(product_amounts)
        results['selectivities'] = selectivities

        # Calculate carbon balance if provided
        if 'Carbon_in' in df.columns and 'Carbon_out' in df.columns:
            carbon_balance = analyzer.calculate_carbon_balance(
                df['Carbon_in'].mean(),
                df['Carbon_out'].mean()
            )
            results['carbon_balance_%'] = carbon_balance

    return results


def analyze_stability(df):
    """Analyze catalyst stability."""
    analyzer = StabilityAnalyzer()
    results = {}

    if 'Time' in df.columns and 'Conversion' in df.columns:
        time = df['Time'].values
        activity = df['Conversion'].values

        # Try different deactivation models
        for model in ['exponential', 'power_law', 'linear']:
            try:
                stability_results = analyzer.analyze_time_on_stream(time, activity, model)
                results[f'{model}_model'] = stability_results

                # Use best fit (highest R²)
                if 'fit_parameters' in stability_results:
                    r_sq = stability_results['fit_parameters'].get('r_squared', 0)
                    if 'best_model' not in results or r_sq > results['best_r_squared']:
                        results['best_model'] = model
                        results['best_r_squared'] = r_sq
                        results['recommended_results'] = stability_results
            except:
                continue

    return results


def analyze_arrhenius(df):
    """Analyze Arrhenius kinetics."""
    analyzer = ArrheniusAnalyzer()
    results = {}

    if 'Temperature' in df.columns:
        # Check for rate constant or conversion
        if 'Rate_constant' in df.columns:
            temps = df['Temperature'].values
            rates = df['Rate_constant'].values

            arrhenius_results = analyzer.calculate_activation_energy(temps, rates)
            results.update(arrhenius_results)

        elif 'Conversion' in df.columns:
            temps = df['Temperature'].values
            convs = df['Conversion'].values

            temp_dep = analyzer.analyze_temperature_dependence(temps, convs)
            results['temperature_dependence'] = temp_dep

    return results


def compare_with_literature(experimental_results, literature_data):
    """Compare with literature values."""
    comparator = LiteratureComparison()

    # Load literature data
    for lit_entry in literature_data:
        comparator.add_literature_data(lit_entry['reference'], lit_entry['data'])

    comparison_results = {}

    # Compare key metrics
    if 'conversion_mean' in experimental_results:
        conv_comparison = comparator.compare_conversion(
            experimental_results['conversion_mean'],
            metric='conversion'
        )
        comparison_results['conversion_comparison'] = conv_comparison

    # Generate benchmark table
    exp_data = {
        'conversion': experimental_results.get('conversion_mean'),
        'selectivity': experimental_results.get('selectivity_mean'),
        'TOF': experimental_results.get('TOF_h-1')
    }

    benchmark_table = comparator.generate_benchmark_table(exp_data)
    comparison_results['benchmark_table'] = benchmark_table.to_dict()

    return comparison_results


def generate_report(results, material_id, project_path, reaction_conds):
    """Generate Obsidian markdown report."""
    timestamp = datetime.now().strftime("%Y-%m-%d")
    report_filename = f"{material_id}_performance_{timestamp}.md"
    report_path = Path(project_path) / "Reactions" / "Results" / report_filename

    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate markdown content
    content = f"""---
material_id: {material_id}
analysis: catalysis-performance
date: {timestamp}
tags: [catalysis, performance, {material_id}]
---

# Catalysis Performance: {material_id}

## Material

**Catalyst**: [[Materials/{material_id}]]
**Analysis Date**: {timestamp}

## Reaction Conditions

"""

    for key, value in reaction_conds.items():
        content += f"- **{key.replace('_', ' ').title()}**: {value}\n"

    content += "\n## Activity Metrics\n\n"

    if 'conversion_mean' in results:
        conv = results['conversion_mean']
        conv_std = results.get('conversion_std', 0)
        content += f"- **Conversion**: {conv:.2f} ± {conv_std:.2f}%\n"

    if 'yield_mean' in results:
        yld = results['yield_mean']
        yld_std = results.get('yield_std', 0)
        content += f"- **Yield**: {yld:.2f} ± {yld_std:.2f}%\n"

    if 'TOF_h-1' in results:
        content += f"- **TOF**: {results['TOF_h-1']:.1f} h⁻¹\n"

    if 'GHSV_h-1' in results:
        content += f"- **GHSV**: {results['GHSV_h-1']:.0f} h⁻¹\n"

    # Add more sections...
    content += "\n## Related Data\n\n"
    content += f"- Material: [[Materials/{material_id}]]\n"
    content += f"- Characterization: [[Characterization/XRD/{material_id}_XRD]]\n"
    content += f"- Synthesis: [[Synthesis/Protocols/{material_id}_synthesis]]\n"

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return report_path


def main():
    parser = argparse.ArgumentParser(description='Catalysis Performance Analysis')
    parser.add_argument('--data-file', required=True, help='Path to data file')
    parser.add_argument('--material-id', required=True, help='Material identifier')
    parser.add_argument('--project-path', required=True, help='Project directory path')
    parser.add_argument('--analysis-type', default='full',
                       choices=['activity', 'selectivity', 'stability', 'arrhenius', 'full'])
    parser.add_argument('--conditions', type=json.loads, default='{}', help='Reaction conditions (JSON)')
    parser.add_argument('--catalyst-props', type=json.loads, default='{}', help='Catalyst properties (JSON)')
    parser.add_argument('--literature', type=json.loads, default='[]', help='Literature data (JSON)')
    parser.add_argument('--output', help='Output JSON file')

    args = parser.parse_args()

    # Load data
    df = load_data_file(args.data_file)

    results = {}

    # Perform analyses
    if args.analysis_type in ['activity', 'full']:
        results['activity'] = analyze_activity(df, args.catalyst_props, args.conditions)

    if args.analysis_type in ['selectivity', 'full']:
        results['selectivity'] = analyze_selectivity(df)

    if args.analysis_type in ['stability', 'full']:
        results['stability'] = analyze_stability(df)

    if args.analysis_type in ['arrhenius', 'full']:
        results['arrhenius'] = analyze_arrhenius(df)

    # Literature comparison
    if args.literature:
        results['literature_comparison'] = compare_with_literature(results.get('activity', {}), args.literature)

    # Generate report
    report_path = generate_report(results, args.material_id, args.project_path, args.conditions)

    print(f"Analysis complete. Report saved to: {report_path}")

    # Save JSON output
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)

    return results


if __name__ == '__main__':
    main()
