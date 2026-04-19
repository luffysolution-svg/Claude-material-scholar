#!/usr/bin/env python3
"""
Main Characterization Analysis Script

Orchestrates characterization data analysis using technique-specific modules.
"""

import sys
import json
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

# Import analysis modules
from xrd_analysis import XRDAnalyzer
from bet_analysis import BETAnalyzer
from xps_analysis import XPSAnalyzer
from electrochemistry_analysis import ElectrochemistryAnalyzer
from report_generator import CharacterizationReportGenerator


def load_data_file(file_path, technique):
    """
    Load data file based on technique.

    Args:
        file_path: Path to data file
        technique: Characterization technique

    Returns:
        Dictionary with loaded data
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    # Determine file format
    if file_path.suffix in ['.csv', '.txt']:
        # Try to read as CSV
        try:
            df = pd.read_csv(file_path, sep=None, engine='python')
        except Exception as e:
            # Try space-separated
            df = pd.read_csv(file_path, delim_whitespace=True, header=None)
    elif file_path.suffix == '.xlsx':
        df = pd.read_excel(file_path)
    elif file_path.suffix == '.xy':
        # XY format (space or tab separated)
        df = pd.read_csv(file_path, delim_whitespace=True, header=None)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

    # Extract columns based on technique
    if technique == 'XRD':
        # Expect: 2θ, Intensity
        two_theta = df.iloc[:, 0].values
        intensity = df.iloc[:, 1].values
        return {'two_theta': two_theta, 'intensity': intensity}

    elif technique == 'BET':
        # Expect: P/P0, Quantity Adsorbed
        p_p0 = df.iloc[:, 0].values
        q_ads = df.iloc[:, 1].values
        return {'p_p0': p_p0, 'q_ads': q_ads}

    elif technique == 'XPS':
        # Expect: Binding Energy, Intensity
        be = df.iloc[:, 0].values
        intensity = df.iloc[:, 1].values
        return {'binding_energy': be, 'intensity': intensity}

    elif technique == 'Electrochemistry':
        # Variable format depending on measurement type
        if df.shape[1] == 2:
            # CV or Tafel: x, y
            x = df.iloc[:, 0].values
            y = df.iloc[:, 1].values
            return {'x': x, 'y': y}
        elif df.shape[1] == 3:
            # EIS: Frequency, Z_real, Z_imag
            freq = df.iloc[:, 0].values
            z_real = df.iloc[:, 1].values
            z_imag = df.iloc[:, 2].values
            return {'frequency': freq, 'z_real': z_real, 'z_imag': z_imag}

    else:
        raise ValueError(f"Unknown technique: {technique}")


def analyze_xrd(data, options, material_id, project_path):
    """Analyze XRD data."""
    wavelength = options.get('wavelength', 1.5406)
    prominence = options.get('prominence', 0.1)
    phase_database = options.get('phase_database', {})

    # Initialize analyzer
    analyzer = XRDAnalyzer(data['two_theta'], data['intensity'], wavelength)

    # Find peaks
    peaks = analyzer.find_peaks(prominence=prominence)

    # Calculate crystallite sizes
    crystallite_sizes = {}
    for i, peak_pos in enumerate(peaks['peak_positions']):
        fwhm = peaks['peak_widths_fwhm'][i]
        size = analyzer.calculate_crystallite_size(peak_pos, fwhm)
        crystallite_sizes[f"{peak_pos:.2f}"] = size

    # Calculate d-spacings
    d_spacings = [analyzer.calculate_d_spacing(pos) for pos in peaks['peak_positions']]
    peaks['d_spacings'] = d_spacings

    # Match phases
    phases = []
    if phase_database:
        phases = analyzer.match_phases(peaks['peak_positions'], phase_database)

    # Generate plot
    plot_path = Path(project_path) / "Characterization" / "XRD" / f"{material_id}_XRD_pattern.png"
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    analyzer.plot_pattern(output_path=str(plot_path), title=f"XRD Pattern: {material_id}")

    # Compile results
    results = {
        'peaks': peaks,
        'crystallite_sizes': crystallite_sizes,
        'phases': phases
    }

    # Generate report
    report_gen = CharacterizationReportGenerator(project_path, material_id)
    report_path = report_gen.generate_xrd_report(results, plot_path)

    return results, report_path


def analyze_bet(data, options, material_id, project_path):
    """Analyze BET data."""
    p_p0_range = options.get('p_p0_range', (0.05, 0.3))
    cross_section = options.get('cross_section', 0.162)

    # Initialize analyzer
    analyzer = BETAnalyzer(data['p_p0'], data['q_ads'])

    # Calculate BET surface area
    bet_results = analyzer.calculate_bet_surface_area(p_p0_range=p_p0_range, cross_section=cross_section)

    # Classify isotherm
    isotherm_type = analyzer.classify_isotherm()

    # Calculate pore volume
    pore_volume = analyzer.calculate_pore_volume()

    # Calculate pore size distribution
    psd = analyzer.calculate_pore_size_distribution()

    # Generate plot
    plot_path = Path(project_path) / "Characterization" / "BET" / f"{material_id}_BET_isotherm.png"
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    analyzer.plot_isotherm(output_path=str(plot_path), title=f"BET Isotherm: {material_id}")

    # Compile results
    results = {
        'bet_results': bet_results,
        'isotherm_type': isotherm_type,
        'pore_volume': pore_volume,
        'pore_size_distribution': psd
    }

    # Generate report
    report_gen = CharacterizationReportGenerator(project_path, material_id)
    report_path = report_gen.generate_bet_report(results, plot_path)

    return results, report_path


def analyze_xps(data, options, material_id, project_path):
    """Analyze XPS data."""
    peak_type = options.get('peak_type', 'voigt')
    background = options.get('background', 'shirley')
    calibration_peak = options.get('calibration_peak', None)

    # Initialize analyzer
    analyzer = XPSAnalyzer(data['binding_energy'], data['intensity'])

    # Calibrate if reference provided
    if calibration_peak:
        # Assume C 1s peak for calibration
        peaks_info = analyzer.find_peaks()
        if peaks_info['peak_positions_eV']:
            # Use highest peak as reference
            ref_peak = peaks_info['peak_positions_eV'][np.argmax(peaks_info['peak_intensities'])]
            offset = analyzer.calibrate_binding_energy(ref_peak, calibration_peak)

    # Find peaks
    peaks = analyzer.find_peaks()

    # Fit peaks (example: fit all identified peaks)
    fitted_peaks = []
    for peak_pos in peaks['peak_positions_eV']:
        be_range = (peak_pos - 5, peak_pos + 5)
        fit_result = analyzer.fit_peak(be_range, peak_type, background)
        if 'error' not in fit_result:
            fitted_peaks.append(fit_result)

    # Determine elemental composition (use element from options if provided)
    element = options.get('element', 'Unknown')
    elements = [element] * len(fitted_peaks)
    sensitivity_factors = {element: 1.0}
    try:
        composition = analyzer.calculate_atomic_composition(elements, sensitivity_factors)
    except Exception:
        composition = {}

    # Identify oxidation states
    peak_positions = [fp['parameters'].get('center', 0) for fp in fitted_peaks if 'parameters' in fp]
    try:
        ox_list = analyzer.identify_oxidation_states(element, peak_positions)
        # Convert list to dict format expected by report_generator
        oxidation_states = {element: ox_list} if isinstance(ox_list, list) else ox_list
    except Exception:
        oxidation_states = {}

    # Generate plot
    plot_path = Path(project_path) / "Characterization" / "XPS" / f"{material_id}_XPS_spectrum.png"
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    analyzer.plot_spectrum(output_path=str(plot_path), title=f"XPS Spectrum: {material_id}")

    # Compile results
    results = {
        'peaks': peaks,
        'fitted_peaks': fitted_peaks,
        'composition': composition,
        'oxidation_states': oxidation_states
    }

    # Generate report
    report_gen = CharacterizationReportGenerator(project_path, material_id)
    report_path = report_gen.generate_xps_report(results, plot_path)

    return results, report_path


def analyze_electrochemistry(data, options, material_id, project_path, measurement_type):
    """Analyze electrochemistry data."""
    analyzer = ElectrochemistryAnalyzer()

    if measurement_type == 'CV':
        scan_rate = options.get('scan_rate', 50)
        results = analyzer.analyze_cv(data['x'], data['y'], scan_rate)
        plot_path = Path(project_path) / "Characterization" / "Electrochemistry" / f"{material_id}_CV.png"
        plot_path.parent.mkdir(parents=True, exist_ok=True)
        analyzer.plot_cv(output_path=str(plot_path), title=f"CV: {material_id}")

    elif measurement_type == 'Tafel':
        results = analyzer.analyze_tafel(data['x'], data['y'])
        plot_path = Path(project_path) / "Characterization" / "Electrochemistry" / f"{material_id}_Tafel.png"
        plot_path.parent.mkdir(parents=True, exist_ok=True)
        analyzer.plot_tafel(output_path=str(plot_path), title=f"Tafel Plot: {material_id}")

    elif measurement_type == 'EIS':
        results = analyzer.analyze_eis(data['frequency'], data['z_real'], data['z_imag'])
        plot_path = Path(project_path) / "Characterization" / "Electrochemistry" / f"{material_id}_EIS.png"
        plot_path.parent.mkdir(parents=True, exist_ok=True)
        analyzer.plot_nyquist(output_path=str(plot_path), title=f"Nyquist Plot: {material_id}")

    else:
        raise ValueError(f"Unknown electrochemistry measurement type: {measurement_type}")

    # Generate report
    report_gen = CharacterizationReportGenerator(project_path, material_id)
    report_path = report_gen.generate_electrochemistry_report(results, plot_path, measurement_type)

    return results, report_path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Characterization Data Analysis')
    parser.add_argument('--technique', required=True, choices=['XRD', 'BET', 'XPS', 'Electrochemistry'])
    parser.add_argument('--data-file', required=True, help='Path to data file')
    parser.add_argument('--material-id', required=True, help='Material identifier')
    parser.add_argument('--project-path', required=True, help='Path to Research project directory')
    parser.add_argument('--options', default='{}', help='JSON string of analysis options')
    parser.add_argument('--measurement-type', help='For electrochemistry: CV, Tafel, or EIS')

    args = parser.parse_args()

    # Parse options
    options = json.loads(args.options)

    # Load data
    print(f"Loading {args.technique} data from {args.data_file}...")
    data = load_data_file(args.data_file, args.technique)

    # Analyze
    print(f"Analyzing {args.technique} data...")
    if args.technique == 'XRD':
        results, report_path = analyze_xrd(data, options, args.material_id, args.project_path)
    elif args.technique == 'BET':
        results, report_path = analyze_bet(data, options, args.material_id, args.project_path)
    elif args.technique == 'XPS':
        results, report_path = analyze_xps(data, options, args.material_id, args.project_path)
    elif args.technique == 'Electrochemistry':
        if not args.measurement_type:
            raise ValueError("--measurement-type required for Electrochemistry (CV, Tafel, or EIS)")
        results, report_path = analyze_electrochemistry(data, options, args.material_id, args.project_path, args.measurement_type)

    print(f"\n[OK] Analysis complete!")
    print(f"[OK] Report saved to: {report_path}")

    # Save results as JSON
    results_json_path = report_path.parent / f"{args.material_id}_{args.technique}_results.json"
    with open(results_json_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"[OK] Results saved to: {results_json_path}")


if __name__ == '__main__':
    main()
