#!/usr/bin/env python3
"""
Stability Testing Module

Analyzes catalyst stability including:
- Time-on-stream analysis
- Deactivation kinetics
- Regeneration cycles
- Stability metrics
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import linregress
import json


class StabilityAnalyzer:
    """Analyzer for catalyst stability."""

    def __init__(self):
        """Initialize stability analyzer."""
        self.results = {}

    @staticmethod
    def exponential_decay(t, A, k, C):
        """
        Exponential decay model for deactivation.

        X(t) = A * exp(-k*t) + C

        Args:
            t: Time
            A: Initial activity amplitude
            k: Deactivation rate constant
            C: Residual activity

        Returns:
            Activity at time t
        """
        return A * np.exp(-k * t) + C

    @staticmethod
    def power_law_decay(t, A, n, C):
        """
        Power law decay model.

        X(t) = A * t^(-n) + C

        Args:
            t: Time
            A: Amplitude
            n: Decay exponent
            C: Residual activity

        Returns:
            Activity at time t
        """
        return A * np.power(t + 1, -n) + C

    @staticmethod
    def linear_decay(t, X0, k):
        """
        Linear decay model.

        X(t) = X0 - k*t

        Args:
            t: Time
            X0: Initial activity
            k: Deactivation rate

        Returns:
            Activity at time t
        """
        return X0 - k * t

    def analyze_time_on_stream(self, time, activity, model='exponential'):
        """
        Analyze time-on-stream data.

        Args:
            time: Array of time values (hours)
            activity: Array of activity values (conversion, yield, etc.)
            model: Deactivation model ('exponential', 'power_law', 'linear')

        Returns:
            Dictionary with stability analysis results
        """
        time = np.array(time)
        activity = np.array(activity)

        # Skip leading zero-activity points (e.g. t=0 before reaction starts)
        nonzero = activity > 0
        if nonzero.any():
            time = time[nonzero]
            activity = activity[nonzero]

        # Initial and final activity
        initial_activity = activity[0]
        final_activity = activity[-1]
        total_time = time[-1] - time[0]

        # Activity retention
        retention = (final_activity / initial_activity * 100) if initial_activity > 0 else 0

        # Fit deactivation model
        try:
            if model == 'exponential':
                # Initial guess
                A_guess = initial_activity - final_activity
                k_guess = 0.01
                C_guess = final_activity

                popt, pcov = curve_fit(
                    self.exponential_decay,
                    time,
                    activity,
                    p0=[A_guess, k_guess, C_guess],
                    maxfev=5000
                )

                A, k, C = popt
                fitted_activity = self.exponential_decay(time, A, k, C)

                # Calculate R²
                ss_res = np.sum((activity - fitted_activity) ** 2)
                ss_tot = np.sum((activity - np.mean(activity)) ** 2)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

                fit_params = {
                    'model': 'exponential',
                    'A': A,
                    'k_deactivation': k,
                    'C_residual': C,
                    'r_squared': r_squared,
                    'half_life_h': np.log(2) / k if k > 0 else None
                }

            elif model == 'power_law':
                A_guess = initial_activity
                n_guess = 0.5
                C_guess = final_activity

                popt, pcov = curve_fit(
                    self.power_law_decay,
                    time,
                    activity,
                    p0=[A_guess, n_guess, C_guess],
                    maxfev=5000
                )

                A, n, C = popt
                fitted_activity = self.power_law_decay(time, A, n, C)

                ss_res = np.sum((activity - fitted_activity) ** 2)
                ss_tot = np.sum((activity - np.mean(activity)) ** 2)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

                fit_params = {
                    'model': 'power_law',
                    'A': A,
                    'n_exponent': n,
                    'C_residual': C,
                    'r_squared': r_squared
                }

            elif model == 'linear':
                slope, intercept, r_value, p_value, std_err = linregress(time, activity)

                fitted_activity = self.linear_decay(time, intercept, -slope)

                fit_params = {
                    'model': 'linear',
                    'X0_initial': intercept,
                    'k_deactivation': -slope,
                    'r_squared': r_value ** 2
                }

            else:
                raise ValueError(f"Unknown model: {model}")

        except Exception as e:
            fit_params = {'error': str(e)}
            fitted_activity = None

        # Calculate deactivation rate (% per hour)
        if total_time > 0:
            deactivation_rate = ((initial_activity - final_activity) / initial_activity / total_time) * 100
        else:
            deactivation_rate = 0

        results = {
            'initial_activity': initial_activity,
            'final_activity': final_activity,
            'activity_retention_%': retention,
            'total_time_h': total_time,
            'deactivation_rate_%_per_h': deactivation_rate,
            'fit_parameters': fit_params,
            'time': time.tolist(),
            'activity': activity.tolist(),
            'fitted_activity': fitted_activity.tolist() if fitted_activity is not None else None
        }

        return results

    def analyze_regeneration_cycles(self, cycle_data):
        """
        Analyze regeneration cycles.

        Args:
            cycle_data: List of dictionaries with cycle information
                       [{'cycle': 1, 'initial_activity': x, 'final_activity': y, 'time': t}, ...]

        Returns:
            Dictionary with regeneration analysis
        """
        cycles = []
        initial_activities = []
        final_activities = []
        retentions = []

        for cycle in cycle_data:
            cycle_num = cycle['cycle']
            initial = cycle['initial_activity']
            final = cycle['final_activity']

            retention = (final / initial * 100) if initial > 0 else 0

            cycles.append(cycle_num)
            initial_activities.append(initial)
            final_activities.append(final)
            retentions.append(retention)

        # Calculate activity loss per cycle
        if len(initial_activities) > 1:
            activity_loss_per_cycle = []
            for i in range(1, len(initial_activities)):
                loss = initial_activities[i-1] - initial_activities[i]
                loss_pct = (loss / initial_activities[0] * 100) if initial_activities[0] > 0 else 0
                activity_loss_per_cycle.append(loss_pct)

            avg_loss_per_cycle = np.mean(activity_loss_per_cycle)
        else:
            avg_loss_per_cycle = 0

        # Predict cycles to 50% activity
        if len(cycles) >= 2 and avg_loss_per_cycle > 0:
            current_activity = initial_activities[-1]
            target_activity = initial_activities[0] * 0.5
            remaining_loss = current_activity - target_activity
            cycles_to_50pct = cycles[-1] + (remaining_loss / (avg_loss_per_cycle / 100 * initial_activities[0]))
        else:
            cycles_to_50pct = None

        results = {
            'num_cycles': len(cycles),
            'cycles': cycles,
            'initial_activities': initial_activities,
            'final_activities': final_activities,
            'retentions_%': retentions,
            'avg_loss_per_cycle_%': avg_loss_per_cycle,
            'predicted_cycles_to_50%': cycles_to_50pct
        }

        return results

    def calculate_stability_metrics(self, time, activity):
        """
        Calculate various stability metrics.

        Args:
            time: Array of time values
            activity: Array of activity values

        Returns:
            Dictionary with stability metrics
        """
        time = np.array(time)
        activity = np.array(activity)

        # Time to 90%, 80%, 50% activity
        initial = activity[0]

        def find_time_to_activity(target_pct):
            target = initial * (target_pct / 100)
            idx = np.where(activity <= target)[0]
            if len(idx) > 0:
                return time[idx[0]]
            return None

        t90 = find_time_to_activity(90)
        t80 = find_time_to_activity(80)
        t50 = find_time_to_activity(50)

        # Average activity over time
        avg_activity = np.mean(activity)

        # Activity standard deviation (measure of stability)
        std_activity = np.std(activity)
        cv = (std_activity / avg_activity * 100) if avg_activity > 0 else 0

        # Stability index (area under curve normalized)
        auc = np.trapz(activity, time)
        max_auc = initial * (time[-1] - time[0])
        stability_index = (auc / max_auc * 100) if max_auc > 0 else 0

        metrics = {
            'time_to_90%_h': t90,
            'time_to_80%_h': t80,
            'time_to_50%_h': t50,
            'average_activity': avg_activity,
            'std_activity': std_activity,
            'coefficient_of_variation_%': cv,
            'stability_index_%': stability_index
        }

        return metrics

    def plot_stability(self, time, activity, fitted_activity=None, output_path=None, title="Stability Test"):
        """
        Plot stability data.

        Args:
            time: Array of time values
            activity: Array of measured activity
            fitted_activity: Array of fitted activity (optional)
            output_path: Path to save plot
            title: Plot title

        Returns:
            matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot measured data
        ax.plot(time, activity, 'bo-', linewidth=2, markersize=8, label='Measured')

        # Plot fitted data if available
        if fitted_activity is not None:
            ax.plot(time, fitted_activity, 'r--', linewidth=2, label='Fitted')

        ax.set_xlabel('Time on Stream (h)', fontsize=12)
        ax.set_ylabel('Activity (Conversion, %)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig

    def plot_regeneration_cycles(self, cycles, initial_activities, output_path=None, title="Regeneration Cycles"):
        """
        Plot regeneration cycle data.

        Args:
            cycles: List of cycle numbers
            initial_activities: List of initial activities for each cycle
            output_path: Path to save plot
            title: Plot title

        Returns:
            matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(cycles, initial_activities, 'go-', linewidth=2, markersize=10, label='Initial Activity')

        # Add 50% activity line
        if len(initial_activities) > 0:
            ax.axhline(y=initial_activities[0] * 0.5, color='r', linestyle='--', linewidth=2, label='50% Activity')

        ax.set_xlabel('Cycle Number', fontsize=12)
        ax.set_ylabel('Initial Activity (%)', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')

        return fig
