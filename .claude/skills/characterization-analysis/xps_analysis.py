#!/usr/bin/env python3
"""
XPS Analysis Module

Analyzes X-ray photoelectron spectroscopy data including:
- Peak fitting (Gaussian, Lorentzian, Voigt)
- Elemental composition
- Oxidation state determination
- Binding energy calibration
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.signal import find_peaks
import json


class XPSAnalyzer:
    """Analyzer for XPS (X-ray Photoelectron Spectroscopy) data."""

    def __init__(self, binding_energy, intensity):
        """
        Initialize XPS analyzer.

        Args:
            binding_energy: Array of binding energy values (eV)
            intensity: Array of intensity/counts values
        """
        self.be = np.array(binding_energy)
        self.intensity = np.array(intensity)
        self.peaks = None
        self.fitted_peaks = []

    @staticmethod
    def gaussian(x, amplitude, center, sigma):
        """Gaussian peak function."""
        return amplitude * np.exp(-(x - center)**2 / (2 * sigma**2))

    @staticmethod
    def lorentzian(x, amplitude, center, gamma):
        """Lorentzian peak function."""
        return amplitude * gamma**2 / ((x - center)**2 + gamma**2)

    @staticmethod
    def voigt(x, amplitude, center, sigma, gamma):
        """
        Voigt profile (convolution of Gaussian and Lorentzian).
        Simplified approximation.
        """
        # Pseudo-Voigt approximation
        f_g = 1.36603 * (gamma / sigma) - 0.47719 * (gamma / sigma)**2 + 0.11116 * (gamma / sigma)**3
        f_l = 1 - f_g

        gaussian_part = np.exp(-(x - center)**2 / (2 * sigma**2))
        lorentzian_part = gamma**2 / ((x - center)**2 + gamma**2)

        return amplitude * (f_g * gaussian_part + f_l * lorentzian_part)

    @staticmethod
    def shirley_background(x, y, tol=1e-5, max_iter=50):
        """
        Calculate Shirley background.

        Args:
            x: Binding energy array
            y: Intensity array
            tol: Convergence tolerance
            max_iter: Maximum iterations

        Returns:
            Background array
        """
        background = np.zeros_like(y)

        for iteration in range(max_iter):
            background_old = background.copy()

            # Calculate cumulative sum from right to left
            cumsum = np.cumsum(y - background)

            # Normalize
            k = (y[0] - y[-1]) / (cumsum[-1] if cumsum[-1] != 0 else 1)
            background = y[-1] + k * cumsum

            # Check convergence
            if np.max(np.abs(background - background_old)) < tol:
                break

        return background

    def calibrate_binding_energy(self, reference_peak_be, expected_be):
        """
        Calibrate binding energy scale using a reference peak (e.g., C 1s at 284.8 eV).

        Args:
            reference_peak_be: Measured binding energy of reference peak
            expected_be: Expected binding energy of reference peak (e.g., 284.8 for C 1s)

        Returns:
            Calibration offset in eV
        """
        offset = expected_be - reference_peak_be
        self.be = self.be + offset

        return offset

    def find_peaks(self, prominence=0.05, min_distance=10):
        """
        Identify peaks in XPS spectrum.

        Args:
            prominence: Minimum prominence of peaks (relative to max intensity)
            min_distance: Minimum distance between peaks (in data points)

        Returns:
            Dictionary with peak positions and properties
        """
        # Normalize intensity
        norm_intensity = self.intensity / np.max(self.intensity)

        # Find peaks
        peaks, properties = find_peaks(
            norm_intensity,
            prominence=prominence,
            distance=min_distance
        )

        self.peaks = peaks

        results = {
            'peak_indices': peaks.tolist(),
            'peak_positions_eV': self.be[peaks].tolist(),
            'peak_intensities': self.intensity[peaks].tolist(),
            'relative_intensities': (self.intensity[peaks] / np.max(self.intensity[peaks])).tolist()
        }

        return results

    def fit_peak(self, be_range, peak_type='voigt', background='shirley'):
        """
        Fit a peak in specified binding energy range.

        Args:
            be_range: Tuple of (min_be, max_be) for fitting
            peak_type: 'gaussian', 'lorentzian', or 'voigt'
            background: 'shirley', 'linear', or 'none'

        Returns:
            Dictionary with fitted parameters
        """
        # Select data in range
        mask = (self.be >= be_range[0]) & (self.be <= be_range[1])
        be_fit = self.be[mask]
        intensity_fit = self.intensity[mask]

        if len(be_fit) < 10:
            return {'error': 'Insufficient data points in range'}

        # Calculate background
        if background == 'shirley':
            bg = self.shirley_background(be_fit, intensity_fit)
        elif background == 'linear':
            bg = np.linspace(intensity_fit[0], intensity_fit[-1], len(intensity_fit))
        else:
            bg = np.zeros_like(intensity_fit)

        # Subtract background
        intensity_corrected = intensity_fit - bg

        # Initial guess for parameters
        amplitude_guess = np.max(intensity_corrected)
        center_guess = be_fit[np.argmax(intensity_corrected)]
        width_guess = (be_range[1] - be_range[0]) / 4

        try:
            if peak_type == 'gaussian':
                popt, pcov = curve_fit(
                    self.gaussian,
                    be_fit,
                    intensity_corrected,
                    p0=[amplitude_guess, center_guess, width_guess],
                    maxfev=5000
                )
                fitted_intensity = self.gaussian(be_fit, *popt)
                params = {'amplitude': popt[0], 'center': popt[1], 'sigma': popt[2], 'FWHM': 2.355 * popt[2]}

            elif peak_type == 'lorentzian':
                popt, pcov = curve_fit(
                    self.lorentzian,
                    be_fit,
                    intensity_corrected,
                    p0=[amplitude_guess, center_guess, width_guess],
                    maxfev=5000
                )
                fitted_intensity = self.lorentzian(be_fit, *popt)
                params = {'amplitude': popt[0], 'center': popt[1], 'gamma': popt[2], 'FWHM': 2 * popt[2]}

            elif peak_type == 'voigt':
                popt, pcov = curve_fit(
                    self.voigt,
                    be_fit,
                    intensity_corrected,
                    p0=[amplitude_guess, center_guess, width_guess, width_guess/2],
                    maxfev=5000
                )
                fitted_intensity = self.voigt(be_fit, *popt)
                params = {'amplitude': popt[0], 'center': popt[1], 'sigma': popt[2], 'gamma': popt[3]}

            # Calculate peak area
            peak_area = np.trapz(fitted_intensity, be_fit)

            # Calculate R-squared
            ss_res = np.sum((intensity_corrected - fitted_intensity)**2)
            ss_tot = np.sum((intensity_corrected - np.mean(intensity_corrected))**2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            result = {
                'peak_type': peak_type,
                'parameters': params,
                'peak_area': peak_area,
                'r_squared': r_squared,
                'be_range': be_range,
                'fitted_data': {
                    'binding_energy': be_fit.tolist(),
                    'intensity': intensity_fit.tolist(),
                    'background': bg.tolist(),
                    'fitted_peak': fitted_intensity.tolist()
                }
            }

            self.fitted_peaks.append(result)
            return result

        except Exception as e:
            return {'error': f'Fitting failed: {str(e)}'}

    def identify_oxidation_states(self, element, peak_positions):
        """
        Identify oxidation states based on binding energy shifts.

        Args:
            element: Element symbol (e.g., 'Ni', 'Cu', 'Fe')
            peak_positions: List of fitted peak positions (eV)

        Returns:
            List of identified oxidation states
        """
        # Database of common oxidation states and their binding energies
        # This is a simplified database - expand as needed
        oxidation_state_db = {
            'Ni': {
                '2p3/2': {
                    'Ni0': 852.6,
                    'NiO': 854.0,
                    'Ni(OH)2': 856.0,
                    'NiOOH': 856.5
                }
            },
            'Cu': {
                '2p3/2': {
                    'Cu0': 932.7,
                    'Cu2O': 932.5,
                    'CuO': 933.6,
                    'Cu(OH)2': 935.0
                }
            },
            'Fe': {
                '2p3/2': {
                    'Fe0': 706.8,
                    'FeO': 709.5,
                    'Fe2O3': 711.0,
                    'Fe3O4': 710.0
                }
            },
            'C': {
                '1s': {
                    'C-C': 284.8,
                    'C-O': 286.5,
                    'C=O': 288.0,
                    'O-C=O': 289.0
                }
            }
        }

        if element not in oxidation_state_db:
            return [{'error': f'Element {element} not in database'}]

        # Get first orbital (simplified - assumes 2p3/2 or 1s)
        orbital = list(oxidation_state_db[element].keys())[0]
        states = oxidation_state_db[element][orbital]

        # Match peaks to oxidation states
        identifications = []
        for peak_be in peak_positions:
            best_match = None
            min_diff = float('inf')

            for state, ref_be in states.items():
                diff = abs(peak_be - ref_be)
                if diff < min_diff:
                    min_diff = diff
                    best_match = state

            if min_diff < 1.5:  # Within 1.5 eV tolerance
                identifications.append({
                    'peak_be': peak_be,
                    'oxidation_state': best_match,
                    'reference_be': states[best_match],
                    'shift': peak_be - states[best_match]
                })

        return identifications

    def calculate_atomic_composition(self, peak_areas, elements, sensitivity_factors):
        """
        Calculate atomic composition from peak areas.

        Args:
            peak_areas: Dictionary of {element: peak_area}
            elements: List of element symbols
            sensitivity_factors: Dictionary of {element: sensitivity_factor}

        Returns:
            Dictionary of atomic percentages
        """
        # Normalize by sensitivity factors
        normalized_areas = {}
        for element in elements:
            if element in peak_areas and element in sensitivity_factors:
                normalized_areas[element] = peak_areas[element] / sensitivity_factors[element]

        # Calculate atomic percentages
        total = sum(normalized_areas.values())
        atomic_percent = {element: (area / total) * 100 for element, area in normalized_areas.items()}

        return atomic_percent

    def plot_spectrum(self, output_path=None, title="XPS Spectrum", show_peaks=True, show_fits=True):
        """
        Plot XPS spectrum with fitted peaks.

        Args:
            output_path: Path to save plot (optional)
            title: Plot title
            show_peaks: Whether to mark identified peaks
            show_fits: Whether to show fitted peaks

        Returns:
            matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        # Plot spectrum (reversed x-axis for XPS convention)
        ax.plot(self.be, self.intensity, 'b-', linewidth=1.5, label='XPS Spectrum')

        # Mark peaks if identified
        if show_peaks and self.peaks is not None:
            ax.plot(
                self.be[self.peaks],
                self.intensity[self.peaks],
                'ro',
                markersize=8,
                label='Identified Peaks'
            )

        # Show fitted peaks
        if show_fits and len(self.fitted_peaks) > 0:
            for i, fit in enumerate(self.fitted_peaks):
                if 'fitted_data' in fit:
                    be_fit = np.array(fit['fitted_data']['binding_energy'])
                    fitted = np.array(fit['fitted_data']['fitted_peak'])
                    bg = np.array(fit['fitted_data']['background'])

                    ax.plot(be_fit, fitted + bg, 'r--', linewidth=2, label=f'Fit {i+1}' if i == 0 else '')
                    ax.plot(be_fit, bg, 'g--', linewidth=1, alpha=0.5, label='Background' if i == 0 else '')

        ax.set_xlabel('Binding Energy (eV)', fontsize=12)
        ax.set_ylabel('Intensity (a.u.)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.invert_xaxis()  # XPS convention: high BE on left

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig

    def generate_report(self):
        """
        Generate analysis report.

        Returns:
            Dictionary with complete analysis results
        """
        report = {
            'data_points': len(self.be),
            'binding_energy_range': [float(np.min(self.be)), float(np.max(self.be))],
            'identified_peaks': self.find_peaks() if self.peaks is None else {
                'peak_positions_eV': self.be[self.peaks].tolist(),
                'peak_intensities': self.intensity[self.peaks].tolist()
            },
            'fitted_peaks': self.fitted_peaks,
            'analysis_timestamp': pd.Timestamp.now().isoformat()
        }

        return report


def analyze_xps_file(file_path, element=None, calibrate=True):
    """
    Convenience function to analyze XPS data from file.

    Args:
        file_path: Path to data file (CSV or TXT)
        element: Element symbol for oxidation state identification
        calibrate: Whether to calibrate to C 1s at 284.8 eV

    Returns:
        XPSAnalyzer object with results
    """
    # Load data
    try:
        data = pd.read_csv(file_path, sep=None, engine='python')
        be = data.iloc[:, 0].values
        intensity = data.iloc[:, 1].values
    except Exception as e:
        raise ValueError(f"Failed to load data: {str(e)}")

    # Create analyzer
    analyzer = XPSAnalyzer(be, intensity)

    # Calibrate if requested
    if calibrate and element == 'C':
        peaks = analyzer.find_peaks()
        if peaks['peak_positions_eV']:
            # Assume first peak is C 1s
            c1s_peak = peaks['peak_positions_eV'][0]
            offset = analyzer.calibrate_binding_energy(c1s_peak, 284.8)
            print(f"Calibrated binding energy: offset = {offset:.2f} eV")

    return analyzer
