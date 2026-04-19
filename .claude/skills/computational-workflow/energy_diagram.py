"""
Energy Diagram Generator for Reaction Mechanisms
Creates publication-quality reaction coordinate diagrams and potential energy surfaces
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class EnergyLevel:
    """Represents an energy level in a reaction coordinate diagram"""
    name: str
    energy: float  # Relative energy (kcal/mol)
    x_position: float  # X-axis position
    label: Optional[str] = None
    color: str = "blue"
    is_transition_state: bool = False


class EnergyDiagramGenerator:
    """Generate reaction coordinate diagrams and energy profiles"""

    def __init__(self, figsize: Tuple[int, int] = (10, 6)):
        """
        Initialize diagram generator

        Args:
            figsize: Figure size (width, height) in inches
        """
        self.figsize = figsize
        self.fig = None
        self.ax = None

    def create_reaction_coordinate_diagram(
        self,
        energy_levels: List[EnergyLevel],
        title: str = "Reaction Coordinate Diagram",
        ylabel: str = "Relative Energy (kcal/mol)",
        show_values: bool = True,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Create a reaction coordinate diagram

        Args:
            energy_levels: List of EnergyLevel objects
            title: Plot title
            ylabel: Y-axis label
            show_values: Show energy values on diagram
            save_path: Path to save figure (optional)

        Returns:
            Matplotlib figure object
        """
        self.fig, self.ax = plt.subplots(figsize=self.figsize)

        # Sort energy levels by x_position
        sorted_levels = sorted(energy_levels, key=lambda x: x.x_position)

        # Plot energy levels
        for i, level in enumerate(sorted_levels):
            # Determine line style
            linestyle = '--' if level.is_transition_state else '-'
            linewidth = 2.5 if level.is_transition_state else 3

            # Draw horizontal line for energy level
            x_start = level.x_position - 0.15
            x_end = level.x_position + 0.15
            self.ax.plot([x_start, x_end], [level.energy, level.energy],
                        color=level.color, linewidth=linewidth, linestyle=linestyle)

            # Add label below the line
            label_text = level.label if level.label else level.name
            self.ax.text(level.x_position, level.energy - 2,
                        label_text, ha='center', va='top', fontsize=10, fontweight='bold')

            # Add energy value above the line
            if show_values:
                value_text = f"{level.energy:.1f}"
                self.ax.text(level.x_position, level.energy + 1,
                            value_text, ha='center', va='bottom', fontsize=9)

            # Connect to next level with curved arrow
            if i < len(sorted_levels) - 1:
                next_level = sorted_levels[i + 1]
                self._draw_connection(level, next_level)

        # Set axis properties
        self.ax.set_xlabel("Reaction Coordinate", fontsize=12, fontweight='bold')
        self.ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
        self.ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        # Remove x-axis ticks (reaction coordinate is qualitative)
        self.ax.set_xticks([])

        # Add grid
        self.ax.grid(axis='y', alpha=0.3, linestyle='--')

        # Set y-axis to start at 0 or minimum energy
        y_min = min(level.energy for level in energy_levels)
        y_max = max(level.energy for level in energy_levels)
        y_range = y_max - y_min
        self.ax.set_ylim(min(0, y_min - 0.1 * y_range), y_max + 0.15 * y_range)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return self.fig

    def _draw_connection(self, level1: EnergyLevel, level2: EnergyLevel):
        """Draw curved connection between two energy levels"""
        x1 = level1.x_position + 0.15
        y1 = level1.energy
        x2 = level2.x_position - 0.15
        y2 = level2.energy

        # Create curved path
        x_mid = (x1 + x2) / 2
        y_mid = (y1 + y2) / 2

        # Use quadratic Bezier curve
        t = np.linspace(0, 1, 100)
        x_curve = (1 - t)**2 * x1 + 2 * (1 - t) * t * x_mid + t**2 * x2
        y_curve = (1 - t)**2 * y1 + 2 * (1 - t) * t * y_mid + t**2 * y2

        self.ax.plot(x_curve, y_curve, 'k-', linewidth=1.5, alpha=0.6)

    def create_multi_pathway_diagram(
        self,
        pathways: Dict[str, List[EnergyLevel]],
        title: str = "Reaction Pathways Comparison",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Create diagram comparing multiple reaction pathways

        Args:
            pathways: Dictionary mapping pathway names to energy level lists
            title: Plot title
            save_path: Path to save figure

        Returns:
            Matplotlib figure object
        """
        self.fig, self.ax = plt.subplots(figsize=self.figsize)

        colors = ['blue', 'red', 'green', 'orange', 'purple']

        for idx, (pathway_name, levels) in enumerate(pathways.items()):
            color = colors[idx % len(colors)]
            sorted_levels = sorted(levels, key=lambda x: x.x_position)

            # Plot pathway
            x_positions = [level.x_position for level in sorted_levels]
            energies = [level.energy for level in sorted_levels]

            self.ax.plot(x_positions, energies, 'o-', color=color,
                        linewidth=2.5, markersize=8, label=pathway_name, alpha=0.7)

            # Mark transition states
            for level in sorted_levels:
                if level.is_transition_state:
                    self.ax.plot(level.x_position, level.energy, 'D',
                               color=color, markersize=10, markeredgecolor='black',
                               markeredgewidth=1.5)

        self.ax.set_xlabel("Reaction Coordinate", fontsize=12, fontweight='bold')
        self.ax.set_ylabel("Relative Energy (kcal/mol)", fontsize=12, fontweight='bold')
        self.ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        self.ax.legend(fontsize=10, framealpha=0.9)
        self.ax.grid(axis='y', alpha=0.3, linestyle='--')
        self.ax.set_xticks([])

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return self.fig

    def create_potential_energy_surface(
        self,
        x_coords: np.ndarray,
        y_coords: np.ndarray,
        energies: np.ndarray,
        x_label: str = "Coordinate 1",
        y_label: str = "Coordinate 2",
        title: str = "Potential Energy Surface",
        contour_levels: int = 20,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Create 2D potential energy surface contour plot

        Args:
            x_coords: X-axis coordinates (1D array)
            y_coords: Y-axis coordinates (1D array)
            energies: Energy values (2D array, shape: len(y_coords) x len(x_coords))
            x_label: X-axis label
            y_label: Y-axis label
            title: Plot title
            contour_levels: Number of contour levels
            save_path: Path to save figure

        Returns:
            Matplotlib figure object
        """
        self.fig, self.ax = plt.subplots(figsize=self.figsize)

        # Create contour plot
        X, Y = np.meshgrid(x_coords, y_coords)
        contour = self.ax.contourf(X, Y, energies, levels=contour_levels,
                                   cmap='viridis', alpha=0.8)

        # Add contour lines
        contour_lines = self.ax.contour(X, Y, energies, levels=contour_levels,
                                       colors='black', linewidths=0.5, alpha=0.4)

        # Add colorbar
        cbar = plt.colorbar(contour, ax=self.ax)
        cbar.set_label('Energy (kcal/mol)', fontsize=11, fontweight='bold')

        # Find and mark minima and saddle points
        self._mark_critical_points(X, Y, energies)

        self.ax.set_xlabel(x_label, fontsize=12, fontweight='bold')
        self.ax.set_ylabel(y_label, fontsize=12, fontweight='bold')
        self.ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return self.fig

    def _mark_critical_points(self, X: np.ndarray, Y: np.ndarray, Z: np.ndarray):
        """Mark local minima and saddle points on PES"""
        # Simple gradient-based detection
        grad_x = np.gradient(Z, axis=1)
        grad_y = np.gradient(Z, axis=0)
        grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)

        # Find points with small gradient (potential critical points)
        threshold = np.percentile(grad_magnitude, 5)
        critical_mask = grad_magnitude < threshold

        # Mark a few critical points
        critical_indices = np.argwhere(critical_mask)
        if len(critical_indices) > 0:
            # Sample up to 5 critical points
            sample_size = min(5, len(critical_indices))
            sampled = critical_indices[::len(critical_indices)//sample_size][:sample_size]

            for idx in sampled:
                i, j = idx
                self.ax.plot(X[i, j], Y[i, j], 'r*', markersize=15,
                           markeredgecolor='white', markeredgewidth=1)

    def create_energy_profile_with_structures(
        self,
        energy_levels: List[EnergyLevel],
        structure_images: Optional[Dict[str, str]] = None,
        title: str = "Reaction Energy Profile",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Create energy profile with molecular structure images

        Args:
            energy_levels: List of EnergyLevel objects
            structure_images: Dictionary mapping level names to image file paths
            title: Plot title
            save_path: Path to save figure

        Returns:
            Matplotlib figure object
        """
        # Create main diagram
        fig = self.create_reaction_coordinate_diagram(
            energy_levels, title=title, save_path=None
        )

        # Add structure images if provided
        if structure_images:
            for level in energy_levels:
                if level.name in structure_images:
                    img_path = structure_images[level.name]
                    try:
                        img = plt.imread(img_path)
                        # Create inset axes for structure image
                        x_pos = level.x_position
                        y_pos = level.energy

                        # Position image above energy level
                        img_ax = self.fig.add_axes([x_pos/10 - 0.05, 0.7, 0.1, 0.15])
                        img_ax.imshow(img)
                        img_ax.axis('off')
                    except Exception as e:
                        print(f"Warning: Could not load image for {level.name}: {e}")

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig

    def create_thermodynamic_cycle(
        self,
        cycle_data: Dict[str, Dict[str, float]],
        title: str = "Thermodynamic Cycle",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Create Born-Haber or thermodynamic cycle diagram

        Args:
            cycle_data: Dictionary with steps and their ΔH, ΔG values
            title: Plot title
            save_path: Path to save figure

        Returns:
            Matplotlib figure object
        """
        self.fig, self.ax = plt.subplots(figsize=(12, 8))

        # Example layout for a square cycle
        positions = {
            'start': (0, 0),
            'step1': (3, 0),
            'step2': (3, 3),
            'step3': (0, 3)
        }

        # Draw cycle
        steps = list(cycle_data.keys())
        for i, step in enumerate(steps):
            start_pos = positions[f'step{i}'] if i > 0 else positions['start']
            end_pos = positions[f'step{i+1}'] if i < len(steps) - 1 else positions['start']

            # Draw arrow
            arrow = FancyArrowPatch(start_pos, end_pos,
                                   arrowstyle='->', mutation_scale=20,
                                   linewidth=2, color='blue')
            self.ax.add_patch(arrow)

            # Add label
            mid_x = (start_pos[0] + end_pos[0]) / 2
            mid_y = (start_pos[1] + end_pos[1]) / 2

            delta_H = cycle_data[step].get('ΔH', 0)
            label = f"{step}\nΔH = {delta_H:.1f} kcal/mol"
            self.ax.text(mid_x, mid_y, label, ha='center', va='center',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        self.ax.set_xlim(-1, 4)
        self.ax.set_ylim(-1, 4)
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return self.fig


def create_simple_energy_diagram(
    species_names: List[str],
    energies: List[float],
    transition_states: Optional[List[int]] = None,
    title: str = "Energy Diagram",
    save_path: Optional[str] = None
) -> plt.Figure:
    """
    Convenience function to create simple energy diagram

    Args:
        species_names: List of species names (e.g., ['R', 'TS', 'P'])
        energies: List of relative energies (kcal/mol)
        transition_states: Indices of transition states (optional)
        title: Plot title
        save_path: Path to save figure

    Returns:
        Matplotlib figure object
    """
    if transition_states is None:
        transition_states = []

    # Create EnergyLevel objects
    energy_levels = []
    for i, (name, energy) in enumerate(zip(species_names, energies)):
        is_ts = i in transition_states
        level = EnergyLevel(
            name=name,
            energy=energy,
            x_position=i,
            is_transition_state=is_ts,
            color='red' if is_ts else 'blue'
        )
        energy_levels.append(level)

    # Generate diagram
    generator = EnergyDiagramGenerator()
    fig = generator.create_reaction_coordinate_diagram(
        energy_levels, title=title, save_path=save_path
    )

    return fig


if __name__ == "__main__":
    # Example usage
    print("Energy Diagram Generator - Example")

    # Example 1: Simple reaction coordinate diagram
    levels = [
        EnergyLevel("Reactant", 0.0, 0, label="R", color="blue"),
        EnergyLevel("TS1", 25.3, 1, label="TS₁", color="red", is_transition_state=True),
        EnergyLevel("Intermediate", 5.2, 2, label="I", color="green"),
        EnergyLevel("TS2", 18.7, 3, label="TS₂", color="red", is_transition_state=True),
        EnergyLevel("Product", -15.4, 4, label="P", color="blue")
    ]

    generator = EnergyDiagramGenerator()
    fig = generator.create_reaction_coordinate_diagram(
        levels,
        title="Example Reaction Mechanism",
        save_path="example_energy_diagram.png"
    )
    plt.show()

    print("Example diagram saved to: example_energy_diagram.png")
