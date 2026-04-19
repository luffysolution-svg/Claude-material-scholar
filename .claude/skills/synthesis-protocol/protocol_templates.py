"""
Synthesis Protocol Templates
Standard procedures for common catalyst synthesis methods
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Reagent:
    name: str
    amount: float
    unit: str
    cas_number: str = ""
    purity: str = ""
    supplier: str = ""
    role: str = ""  # precursor, support, solvent, precipitant, etc.


@dataclass
class SynthesisStep:
    step_number: int
    description: str
    temperature_C: Optional[float] = None
    time_h: Optional[float] = None
    atmosphere: str = "air"
    notes: str = ""


@dataclass
class SynthesisProtocol:
    method: str
    material_id: str
    reagents: List[Reagent]
    steps: List[SynthesisStep]
    target_loading: Optional[float] = None  # wt%
    calcination_temp_C: Optional[float] = None
    calcination_time_h: Optional[float] = None
    calcination_atmosphere: str = "air"
    reduction_temp_C: Optional[float] = None
    reduction_time_h: Optional[float] = None
    reduction_atmosphere: str = "H2/Ar"
    reference: str = ""
    notes: str = ""


class ProtocolTemplates:
    """Standard synthesis protocol templates for common catalyst preparation methods"""

    @staticmethod
    def incipient_wetness_impregnation(
        support_name: str,
        support_mass_g: float,
        metal_precursor: str,
        metal_loading_wt: float,
        metal_mw: float,
        precursor_mw: float,
        material_id: str
    ) -> SynthesisProtocol:
        """
        Incipient wetness impregnation protocol

        Args:
            support_name: Name of support material (e.g., Al2O3)
            support_mass_g: Mass of support (g)
            metal_precursor: Name of metal precursor salt
            metal_loading_wt: Target metal loading (wt%)
            metal_mw: Molecular weight of metal (g/mol)
            precursor_mw: Molecular weight of precursor (g/mol)
            material_id: Material identifier

        Returns:
            SynthesisProtocol object
        """
        # Calculate precursor amount
        metal_mass = support_mass_g * metal_loading_wt / (100 - metal_loading_wt)
        precursor_mass = metal_mass * precursor_mw / metal_mw

        reagents = [
            Reagent(name=support_name, amount=support_mass_g, unit="g", role="support"),
            Reagent(name=metal_precursor, amount=round(precursor_mass, 3), unit="g", role="precursor"),
            Reagent(name="Deionized water", amount=round(support_mass_g * 0.8, 1), unit="mL", role="solvent")
        ]

        steps = [
            SynthesisStep(1, f"Weigh {support_mass_g} g of {support_name} support"),
            SynthesisStep(2, f"Dissolve {round(precursor_mass, 3)} g of {metal_precursor} in {round(support_mass_g * 0.8, 1)} mL deionized water"),
            SynthesisStep(3, "Add metal precursor solution dropwise to support with continuous stirring"),
            SynthesisStep(4, "Mix thoroughly until uniform impregnation", temperature_C=25, time_h=0.5),
            SynthesisStep(5, "Age at room temperature", temperature_C=25, time_h=2),
            SynthesisStep(6, "Dry in oven", temperature_C=120, time_h=12),
            SynthesisStep(7, f"Calcine in air", temperature_C=500, time_h=4, atmosphere="air")
        ]

        return SynthesisProtocol(
            method="incipient_wetness_impregnation",
            material_id=material_id,
            reagents=reagents,
            steps=steps,
            target_loading=metal_loading_wt,
            calcination_temp_C=500,
            calcination_time_h=4,
            notes=f"Target {metal_loading_wt} wt% {metal_precursor.split('(')[0]} on {support_name}"
        )

    @staticmethod
    def coprecipitation(
        metal_precursors: List[Dict],
        precipitant: str,
        precipitant_conc_M: float,
        target_ph: float,
        material_id: str
    ) -> SynthesisProtocol:
        """
        Coprecipitation protocol

        Args:
            metal_precursors: List of dicts with name, amount_g, mw, role
            precipitant: Precipitating agent (e.g., Na2CO3, NaOH, NH3)
            precipitant_conc_M: Precipitant concentration (mol/L)
            target_ph: Target pH for precipitation
            material_id: Material identifier

        Returns:
            SynthesisProtocol object
        """
        reagents = [
            Reagent(name=p["name"], amount=p["amount_g"], unit="g", role=p.get("role", "precursor"))
            for p in metal_precursors
        ]
        reagents.append(Reagent(
            name=precipitant,
            amount=precipitant_conc_M,
            unit="mol/L",
            role="precipitant"
        ))
        reagents.append(Reagent(name="Deionized water", amount=500, unit="mL", role="solvent"))

        steps = [
            SynthesisStep(1, "Dissolve metal precursors in 250 mL deionized water with stirring"),
            SynthesisStep(2, f"Prepare {precipitant_conc_M} M {precipitant} solution in 250 mL water"),
            SynthesisStep(3, f"Add precipitant dropwise to metal solution at 60°C with vigorous stirring, maintaining pH = {target_ph}", temperature_C=60, time_h=1),
            SynthesisStep(4, "Age precipitate under stirring", temperature_C=60, time_h=2),
            SynthesisStep(5, "Filter and wash with hot deionized water (3×) until neutral pH"),
            SynthesisStep(6, "Dry precipitate", temperature_C=120, time_h=12),
            SynthesisStep(7, "Calcine in air", temperature_C=450, time_h=4, atmosphere="air")
        ]

        return SynthesisProtocol(
            method="coprecipitation",
            material_id=material_id,
            reagents=reagents,
            steps=steps,
            calcination_temp_C=450,
            calcination_time_h=4,
            notes=f"Coprecipitation at pH {target_ph} using {precipitant}"
        )

    @staticmethod
    def sol_gel(
        alkoxide_precursor: str,
        alkoxide_amount_g: float,
        dopant_precursors: Optional[List[Dict]],
        acid_catalyst: str,
        material_id: str
    ) -> SynthesisProtocol:
        """
        Sol-gel synthesis protocol

        Args:
            alkoxide_precursor: Main alkoxide precursor (e.g., TEOS, Al(OiPr)3)
            alkoxide_amount_g: Amount of alkoxide (g)
            dopant_precursors: Optional dopant precursors
            acid_catalyst: Acid catalyst (e.g., HNO3, HCl)
            material_id: Material identifier

        Returns:
            SynthesisProtocol object
        """
        reagents = [
            Reagent(name=alkoxide_precursor, amount=alkoxide_amount_g, unit="g", role="precursor"),
            Reagent(name="Ethanol (anhydrous)", amount=50, unit="mL", role="solvent"),
            Reagent(name="Deionized water", amount=10, unit="mL", role="hydrolysis"),
            Reagent(name=acid_catalyst, amount=0.5, unit="mL", role="catalyst")
        ]

        if dopant_precursors:
            for d in dopant_precursors:
                reagents.append(Reagent(name=d["name"], amount=d["amount_g"], unit="g", role="dopant"))

        steps = [
            SynthesisStep(1, f"Dissolve {alkoxide_amount_g} g {alkoxide_precursor} in 50 mL anhydrous ethanol"),
            SynthesisStep(2, "Add dopant precursors if applicable and stir until dissolved"),
            SynthesisStep(3, f"Add {acid_catalyst} catalyst and stir for 30 min", temperature_C=25, time_h=0.5),
            SynthesisStep(4, "Add deionized water dropwise to initiate hydrolysis", temperature_C=25, time_h=0.5),
            SynthesisStep(5, "Stir until gel forms", temperature_C=25, time_h=4),
            SynthesisStep(6, "Age gel", temperature_C=60, time_h=24),
            SynthesisStep(7, "Dry gel (xerogel) or supercritical dry (aerogel)", temperature_C=120, time_h=24),
            SynthesisStep(8, "Calcine to remove organics", temperature_C=500, time_h=4, atmosphere="air")
        ]

        return SynthesisProtocol(
            method="sol_gel",
            material_id=material_id,
            reagents=reagents,
            steps=steps,
            calcination_temp_C=500,
            calcination_time_h=4,
            notes=f"Sol-gel synthesis using {alkoxide_precursor} with {acid_catalyst} catalyst"
        )

    @staticmethod
    def hydrothermal(
        precursors: List[Dict],
        mineralizer: Optional[str],
        temperature_C: float,
        time_h: float,
        material_id: str,
        autoclave_fill_percent: float = 70
    ) -> SynthesisProtocol:
        """
        Hydrothermal synthesis protocol

        Args:
            precursors: List of precursor dicts with name, amount_g
            mineralizer: Mineralizing agent (e.g., NaOH, HF)
            temperature_C: Hydrothermal temperature (°C)
            time_h: Hydrothermal time (h)
            material_id: Material identifier
            autoclave_fill_percent: Autoclave fill percentage

        Returns:
            SynthesisProtocol object
        """
        reagents = [
            Reagent(name=p["name"], amount=p["amount_g"], unit="g", role="precursor")
            for p in precursors
        ]
        reagents.append(Reagent(name="Deionized water", amount=50, unit="mL", role="solvent"))

        if mineralizer:
            reagents.append(Reagent(name=mineralizer, amount=2, unit="g", role="mineralizer"))

        steps = [
            SynthesisStep(1, "Dissolve/disperse precursors in deionized water with stirring"),
            SynthesisStep(2, f"Add {mineralizer} if applicable and adjust pH" if mineralizer else "Adjust pH if needed"),
            SynthesisStep(3, f"Transfer to Teflon-lined autoclave ({autoclave_fill_percent}% fill)"),
            SynthesisStep(4, f"Seal autoclave and heat", temperature_C=temperature_C, time_h=time_h),
            SynthesisStep(5, "Cool to room temperature naturally"),
            SynthesisStep(6, "Filter and wash product with deionized water and ethanol"),
            SynthesisStep(7, "Dry product", temperature_C=80, time_h=12)
        ]

        return SynthesisProtocol(
            method="hydrothermal",
            material_id=material_id,
            reagents=reagents,
            steps=steps,
            notes=f"Hydrothermal synthesis at {temperature_C}°C for {time_h} h"
        )

    @staticmethod
    def deposition_precipitation(
        support_name: str,
        support_mass_g: float,
        metal_precursor: str,
        metal_amount_g: float,
        precipitant: str,
        target_ph: float,
        material_id: str
    ) -> SynthesisProtocol:
        """
        Deposition-precipitation protocol

        Args:
            support_name: Support material name
            support_mass_g: Support mass (g)
            metal_precursor: Metal precursor name
            metal_amount_g: Metal precursor amount (g)
            precipitant: Precipitating agent
            target_ph: Target pH
            material_id: Material identifier

        Returns:
            SynthesisProtocol object
        """
        reagents = [
            Reagent(name=support_name, amount=support_mass_g, unit="g", role="support"),
            Reagent(name=metal_precursor, amount=metal_amount_g, unit="g", role="precursor"),
            Reagent(name=precipitant, amount=0.1, unit="mol/L", role="precipitant"),
            Reagent(name="Deionized water", amount=200, unit="mL", role="solvent")
        ]

        steps = [
            SynthesisStep(1, f"Suspend {support_mass_g} g {support_name} in 200 mL deionized water"),
            SynthesisStep(2, f"Dissolve {metal_amount_g} g {metal_precursor} in suspension"),
            SynthesisStep(3, f"Heat suspension to 70°C with stirring", temperature_C=70, time_h=0.5),
            SynthesisStep(4, f"Add {precipitant} dropwise to reach pH {target_ph}", temperature_C=70, time_h=1),
            SynthesisStep(5, "Age at 70°C with stirring", temperature_C=70, time_h=2),
            SynthesisStep(6, "Filter and wash with hot deionized water"),
            SynthesisStep(7, "Dry", temperature_C=120, time_h=12),
            SynthesisStep(8, "Calcine", temperature_C=400, time_h=4, atmosphere="air")
        ]

        return SynthesisProtocol(
            method="deposition_precipitation",
            material_id=material_id,
            reagents=reagents,
            steps=steps,
            calcination_temp_C=400,
            calcination_time_h=4,
            notes=f"Deposition-precipitation at pH {target_ph} using {precipitant}"
        )

    @staticmethod
    def get_template_names() -> List[str]:
        return [
            "incipient_wetness_impregnation",
            "coprecipitation",
            "sol_gel",
            "hydrothermal",
            "deposition_precipitation"
        ]
