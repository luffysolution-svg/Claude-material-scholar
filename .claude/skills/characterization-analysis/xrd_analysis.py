#!/usr/bin/env python3
"""
XRD Analysis Module

Analyzes X-ray diffraction data including:
- Peak identification
- Phase matching
- Crystallite size calculation (Scherrer equation)
- Lattice parameter determination
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, peak_widths
from scipy.optimize import curve_fit
import json


class XRDAnalyzer:
    """Analyzer for X-ray diffraction data."""

    def __init__(self, two_theta=None, intensity=None, wavelength=1.5406):
        """
        Initialize XRD analyzer.

        Args:
            two_theta: Array of 2theta angles (degrees), optional
            intensity: Array of intensity values, optional
            wavelength: X-ray wavelength in Angstroms (default: Cu Ka = 1.5406 A)
        """
        self.two_theta = np.array(two_theta) if two_theta is not None else None
        self.intensity = np.array(intensity) if intensity is not None else None
        self.wavelength = wavelength
        self.peaks = None
        self.peak_properties = None

    def load_data(self, two_theta, intensity):
        """Load or replace XRD data."""
        self.two_theta = np.array(two_theta)
        self.intensity = np.array(intensity)

    def find_peaks(self, two_theta=None, intensity=None, prominence=0.1, min_distance=5):
        """
        Identify peaks in XRD pattern.

        Args:
            two_theta: 2theta array (uses instance data if None)
            intensity: intensity array (uses instance data if None)
            prominence: Minimum prominence of peaks (relative to max intensity)
            min_distance: Minimum distance between peaks (in data points)

        Returns:
            Dictionary with peak positions and properties
        """
        if two_theta is not None:
            self.load_data(two_theta, intensity)
        if self.intensity is None:
            raise ValueError("No data loaded. Pass two_theta/intensity or call load_data() first.")

        # Normalize intensity
        norm_intensity = self.intensity / np.max(self.intensity)

        # Find peaks
        peaks, properties = find_peaks(
            norm_intensity,
            prominence=prominence,
            distance=min_distance
        )

        self.peaks = peaks
        self.peak_properties = properties

        # Calculate peak widths (FWHM)
        widths, width_heights, left_ips, right_ips = peak_widths(
            norm_intensity,
            peaks,
            rel_height=0.5
        )

        # Convert width from data points to 2θ degrees
        two_theta_widths = []
        for i, peak_idx in enumerate(peaks):
            left_idx = int(left_ips[i])
            right_idx = int(right_ips[i])
            fwhm = self.two_theta[right_idx] - self.two_theta[left_idx]
            two_theta_widths.append(fwhm)

        results = {
            'peak_indices': peaks.tolist(),
            'peak_positions': self.two_theta[peaks].tolist(),
            'peak_intensities': self.intensity[peaks].tolist(),
            'peak_widths_fwhm': two_theta_widths,
            'relative_intensities': (self.intensity[peaks] / np.max(self.intensity[peaks])).tolist()
        }

        return results

    def calculate_crystallite_size(self, peak_2theta, fwhm_deg, K=0.9):
        """
        Calculate crystallite size using Scherrer equation.

        D = (K * λ) / (β * cos(θ))

        Args:
            peak_2theta: Peak position in 2θ (degrees)
            fwhm_deg: Full width at half maximum (degrees)
            K: Scherrer constant (default: 0.9 for spherical crystals)

        Returns:
            Crystallite size in nanometers
        """
        # Convert to radians
        theta = np.radians(peak_2theta / 2)
        beta = np.radians(fwhm_deg)

        # Scherrer equation
        D = (K * self.wavelength) / (beta * np.cos(theta))

        # Convert from Angstroms to nanometers
        D_nm = D / 10

        return D_nm

    def calculate_d_spacing(self, two_theta):
        """
        Calculate d-spacing using Bragg's law: nλ = 2d sinθ

        Args:
            two_theta: Peak position in 2θ (degrees)

        Returns:
            d-spacing in Angstroms
        """
        theta = np.radians(two_theta / 2)
        d = self.wavelength / (2 * np.sin(theta))
        return d

    def match_phases(self, peak_positions, phase_database):
        """
        Match observed peaks with known phases.

        Args:
            peak_positions: List of observed peak positions (2θ)
            phase_database: Dictionary of known phases with their characteristic peaks

        Returns:
            List of matched phases with confidence scores
        """
        matches = []

        for phase_name, phase_peaks in phase_database.items():
            matched_peaks = 0
            total_phase_peaks = len(phase_peaks)

            for phase_peak in phase_peaks:
                # Check if any observed peak is within ±0.5° of phase peak
                if any(abs(obs_peak - phase_peak) < 0.5 for obs_peak in peak_positions):
                    matched_peaks += 1

            if matched_peaks > 0:
                confidence = matched_peaks / total_phase_peaks
                matches.append({
                    'phase': phase_name,
                    'matched_peaks': matched_peaks,
                    'total_peaks': total_phase_peaks,
                    'confidence': confidence
                })

        # Sort by confidence
        matches.sort(key=lambda x: x['confidence'], reverse=True)

        return matches

    def plot_pattern(self, output_path=None, title="XRD Pattern", show_peaks=True):
        """
        Plot XRD pattern with identified peaks.

        Args:
            output_path: Path to save plot (optional)
            title: Plot title
            show_peaks: Whether to mark identified peaks

        Returns:
            matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        # Plot XRD pattern
        ax.plot(self.two_theta, self.intensity, 'b-', linewidth=1.5, label='XRD Pattern')

        # Mark peaks if identified
        if show_peaks and self.peaks is not None:
            ax.plot(
                self.two_theta[self.peaks],
                self.intensity[self.peaks],
                'ro',
                markersize=8,
                label='Identified Peaks'
            )

            # Annotate major peaks
            for i, peak_idx in enumerate(self.peaks):
                if self.intensity[peak_idx] > 0.3 * np.max(self.intensity):
                    ax.annotate(
                        f'{self.two_theta[peak_idx]:.2f}°',
                        xy=(self.two_theta[peak_idx], self.intensity[peak_idx]),
                        xytext=(0, 10),
                        textcoords='offset points',
                        ha='center',
                        fontsize=9,
                        rotation=45
                    )

        ax.set_xlabel('2θ (degrees)', fontsize=12)
        ax.set_ylabel('Intensity (a.u.)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"[OK] Plot saved to {output_path}")

        return fig

    def generate_report(self, material_id, phase_matches=None):
        """
        Generate comprehensive XRD analysis report.

        Args:
            material_id: Material identifier
            phase_matches: List of matched phases (optional)

        Returns:
            Dictionary with analysis results
        """
        if self.peaks is None:
            self.find_peaks()

        peak_data = self.find_peaks()

        # Calculate crystallite sizes for major peaks
        crystallite_sizes = []
        for i, (pos, fwhm) in enumerate(zip(peak_data['peak_positions'], peak_data['peak_widths_fwhm'])):
            size = self.calculate_crystallite_size(pos, fwhm)
            d_spacing = self.calculate_d_spacing(pos)
            crystallite_sizes.append({
                'peak_2theta': pos,
                'fwhm': fwhm,
                'd_spacing': d_spacing,
                'crystallite_size_nm': size
            })

        # Average crystallite size
        avg_crystallite_size = np.mean([cs['crystallite_size_nm'] for cs in crystallite_sizes])

        report = {
            'material_id': material_id,
            'wavelength': self.wavelength,
            'num_peaks': len(self.peaks),
            'peak_data': peak_data,
            'crystallite_analysis': crystallite_sizes,
            'average_crystallite_size_nm': avg_crystallite_size,
            'phase_matches': phase_matches if phase_matches else []
        }

        return report


def load_xrd_data(file_path):
    """
    Load XRD data from file.

    Supports common formats:
    - CSV: two columns (2θ, intensity)
    - TXT: space or tab separated
    - XY: two columns

    Args:
        file_path: Path to XRD data file

    Returns:
        Tuple of (two_theta, intensity) arrays
    """
    try:
        # Try CSV first
        data = pd.read_csv(file_path, header=None)
        two_theta = data.iloc[:, 0].values
        intensity = data.iloc[:, 1].values
    except:
        # Try space/tab separated
        data = np.loadtxt(file_path)
        two_theta = data[:, 0]
        intensity = data[:, 1]

    return two_theta, intensity


# Common phase database (simplified)
COMMON_PHASES = {
    'Ni (metallic)': [44.5, 51.8, 76.4],
    'NiO': [37.2, 43.3, 62.9, 75.4, 79.4],
    'Al2O3 (gamma)': [37.6, 39.5, 45.8, 60.9, 67.0],
    'Al2O3 (alpha)': [25.6, 35.1, 37.8, 43.4, 52.5, 57.5],
    'Pt (metallic)': [39.8, 46.2, 67.5, 81.3],
    'PtO2': [28.0, 32.0, 46.0, 54.7],
    'CeO2': [28.5, 33.1, 47.5, 56.3],
    'ZrO2 (monoclinic)': [28.2, 31.5, 34.2, 35.3, 50.2],
    'TiO2 (anatase)': [25.3, 37.8, 48.0, 53.9, 55.1, 62.7],
    'TiO2 (rutile)': [27.4, 36.1, 41.2, 44.0, 54.3, 56.6]
}


if __name__ == '__main__':
    # Example usage
    import argparse

    parser = argparse.ArgumentParser(description='Analyze XRD data')
    parser.add_argument('file', help='XRD data file')
    parser.add_argument('--material-id', required=True, help='Material identifier')
    parser.add_argument('--wavelength', type=float, default=1.5406, help='X-ray wavelength (Å)')
    parser.add_argument('--output', help='Output plot path')

    args = parser.parse_args()

    # Load data
    two_theta, intensity = load_xrd_data(args.file)

    # Analyze
    analyzer = XRDAnalyzer(two_theta, intensity, wavelength=args.wavelength)
    report = analyzer.generate_report(args.material_id)

    # Match phases
    peak_positions = report['peak_data']['peak_positions']
    phase_matches = analyzer.match_phases(peak_positions, COMMON_PHASES)
    report['phase_matches'] = phase_matches

    # Plot
    analyzer.plot_pattern(output_path=args.output, title=f"XRD Pattern: {args.material_id}")

    # Print report
    print(json.dumps(report, indent=2))
