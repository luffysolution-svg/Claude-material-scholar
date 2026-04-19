"""
Safety Data Module
Retrieves and formats safety information for synthesis reagents
Uses PubChem data and local hazard database
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass


# GHS hazard pictogram codes and descriptions
GHS_PICTOGRAMS = {
    "GHS01": "Explosive",
    "GHS02": "Flammable",
    "GHS03": "Oxidizing",
    "GHS04": "Compressed Gas",
    "GHS05": "Corrosive",
    "GHS06": "Toxic",
    "GHS07": "Harmful/Irritant",
    "GHS08": "Health Hazard",
    "GHS09": "Environmental Hazard"
}

# Common reagent safety data (CAS → safety info)
COMMON_REAGENTS_SAFETY = {
    "13478-00-7": {  # Ni(NO3)2·6H2O
        "name": "Nickel(II) nitrate hexahydrate",
        "ghs_codes": ["GHS03", "GHS07", "GHS08", "GHS09"],
        "signal_word": "Danger",
        "hazard_statements": ["H272 - May intensify fire; oxidizer",
                              "H302 - Harmful if swallowed",
                              "H317 - May cause an allergic skin reaction",
                              "H331 - Toxic if inhaled",
                              "H334 - May cause allergy or asthma symptoms",
                              "H341 - Suspected of causing genetic defects",
                              "H350i - May cause cancer by inhalation",
                              "H360D - May damage the unborn child",
                              "H372 - Causes damage to organs through prolonged exposure",
                              "H410 - Very toxic to aquatic life with long lasting effects"],
        "precautionary": ["P201 - Obtain special instructions before use",
                         "P260 - Do not breathe dust/fume/gas/mist/vapours/spray",
                         "P273 - Avoid release to the environment",
                         "P280 - Wear protective gloves/protective clothing/eye protection",
                         "P308+P313 - IF exposed or concerned: Get medical advice/attention"],
        "ppe": ["Nitrile gloves", "Lab coat", "Safety goggles", "Fume hood"],
        "disposal": "Collect in labeled waste container; dispose as heavy metal waste"
    },
    "7732-18-5": {  # Water
        "name": "Water",
        "ghs_codes": [],
        "signal_word": "None",
        "hazard_statements": ["Not classified as hazardous"],
        "precautionary": [],
        "ppe": [],
        "disposal": "Drain to sewer"
    },
    "1344-28-1": {  # Al2O3
        "name": "Aluminum oxide",
        "ghs_codes": ["GHS07"],
        "signal_word": "Warning",
        "hazard_statements": ["H335 - May cause respiratory irritation"],
        "precautionary": ["P261 - Avoid breathing dust",
                         "P271 - Use only outdoors or in a well-ventilated area"],
        "ppe": ["Dust mask", "Safety goggles"],
        "disposal": "Dispose as inert solid waste"
    },
    "7647-01-0": {  # HCl
        "name": "Hydrochloric acid",
        "ghs_codes": ["GHS05", "GHS07"],
        "signal_word": "Danger",
        "hazard_statements": ["H290 - May be corrosive to metals",
                              "H314 - Causes severe skin burns and eye damage",
                              "H335 - May cause respiratory irritation"],
        "precautionary": ["P234 - Keep only in original container",
                         "P260 - Do not breathe vapours",
                         "P280 - Wear protective gloves/clothing/eye protection",
                         "P301+P330+P331 - IF SWALLOWED: Rinse mouth; do NOT induce vomiting",
                         "P303+P361+P353 - IF ON SKIN: Remove contaminated clothing; rinse skin"],
        "ppe": ["Chemical-resistant gloves", "Lab coat", "Face shield", "Fume hood"],
        "disposal": "Neutralize with base; dispose as acid waste"
    },
    "1310-73-2": {  # NaOH
        "name": "Sodium hydroxide",
        "ghs_codes": ["GHS05"],
        "signal_word": "Danger",
        "hazard_statements": ["H290 - May be corrosive to metals",
                              "H314 - Causes severe skin burns and eye damage"],
        "precautionary": ["P234 - Keep only in original container",
                         "P260 - Do not breathe dust",
                         "P280 - Wear protective gloves/clothing/eye protection",
                         "P301+P330+P331 - IF SWALLOWED: Rinse mouth; do NOT induce vomiting"],
        "ppe": ["Chemical-resistant gloves", "Lab coat", "Safety goggles"],
        "disposal": "Neutralize with acid; dispose as base waste"
    }
}


@dataclass
class SafetyInfo:
    """Safety information for a chemical reagent"""
    cas_number: str
    name: str
    ghs_codes: List[str]
    signal_word: str
    hazard_statements: List[str]
    precautionary_statements: List[str]
    ppe_required: List[str]
    disposal_instructions: str
    source: str = "local_database"


class SafetyDataManager:
    """Manage safety data for synthesis reagents"""

    def __init__(self):
        self.local_db = COMMON_REAGENTS_SAFETY

    def get_safety_info(self, cas_number: str, name: str = "") -> SafetyInfo:
        """
        Get safety information for a reagent

        Args:
            cas_number: CAS registry number
            name: Chemical name (used if CAS not found)

        Returns:
            SafetyInfo object
        """
        # Check local database first
        if cas_number in self.local_db:
            data = self.local_db[cas_number]
            return SafetyInfo(
                cas_number=cas_number,
                name=data["name"],
                ghs_codes=data["ghs_codes"],
                signal_word=data["signal_word"],
                hazard_statements=data["hazard_statements"],
                precautionary_statements=data["precautionary"],
                ppe_required=data["ppe"],
                disposal_instructions=data.get("disposal", "Consult local regulations"),
                source="local_database"
            )

        # Return generic safety info if not found
        return SafetyInfo(
            cas_number=cas_number,
            name=name or f"Unknown compound (CAS: {cas_number})",
            ghs_codes=["GHS07"],  # Default to harmful/irritant
            signal_word="Warning",
            hazard_statements=["Safety data not available - treat as potentially hazardous"],
            precautionary_statements=["P260 - Avoid breathing dust/vapours",
                                      "P280 - Wear protective equipment"],
            ppe_required=["Gloves", "Safety goggles", "Lab coat"],
            disposal_instructions="Consult local regulations for disposal",
            source="default"
        )

    def get_batch_safety_summary(self, reagents: List[Dict]) -> Dict:
        """
        Get safety summary for all reagents in a synthesis

        Args:
            reagents: List of reagent dicts with cas_number and name

        Returns:
            Safety summary dictionary
        """
        all_ghs = set()
        all_ppe = set()
        highest_signal = "None"
        signal_priority = {"None": 0, "Warning": 1, "Danger": 2}

        reagent_safety = []
        for reagent in reagents:
            cas = reagent.get("cas_number", "")
            name = reagent.get("name", "")

            if cas:
                info = self.get_safety_info(cas, name)
                all_ghs.update(info.ghs_codes)
                all_ppe.update(info.ppe_required)

                if signal_priority.get(info.signal_word, 0) > signal_priority.get(highest_signal, 0):
                    highest_signal = info.signal_word

                reagent_safety.append({
                    "name": info.name,
                    "cas": cas,
                    "signal_word": info.signal_word,
                    "ghs_codes": info.ghs_codes,
                    "key_hazards": info.hazard_statements[:3]
                })

        return {
            "overall_signal_word": highest_signal,
            "ghs_pictograms": list(all_ghs),
            "ghs_descriptions": [GHS_PICTOGRAMS.get(g, g) for g in all_ghs],
            "required_ppe": list(all_ppe),
            "reagent_details": reagent_safety,
            "special_precautions": self._identify_special_precautions(all_ghs)
        }

    def _identify_special_precautions(self, ghs_codes: set) -> List[str]:
        """Identify special precautions based on GHS codes"""
        precautions = []

        if "GHS01" in ghs_codes:
            precautions.append("EXPLOSIVE: Use blast shield; minimize quantities")
        if "GHS02" in ghs_codes:
            precautions.append("FLAMMABLE: Keep away from ignition sources; use fume hood")
        if "GHS03" in ghs_codes:
            precautions.append("OXIDIZER: Keep away from flammables and combustibles")
        if "GHS05" in ghs_codes:
            precautions.append("CORROSIVE: Use chemical-resistant gloves and face shield")
        if "GHS06" in ghs_codes:
            precautions.append("TOXIC: Use fume hood; avoid skin contact and inhalation")
        if "GHS08" in ghs_codes:
            precautions.append("HEALTH HAZARD: Minimize exposure; use appropriate respiratory protection")
        if "GHS09" in ghs_codes:
            precautions.append("ENVIRONMENTAL HAZARD: Prevent release to environment; collect waste")

        return precautions

    def format_safety_section(self, reagents: List[Dict]) -> str:
        """
        Format safety information as markdown section

        Args:
            reagents: List of reagent dicts

        Returns:
            Markdown-formatted safety section
        """
        summary = self.get_batch_safety_summary(reagents)

        md = "## Safety Information\n\n"
        md += f"**Overall Hazard Level**: {summary['overall_signal_word']}\n\n"

        if summary['ghs_descriptions']:
            md += f"**GHS Hazards**: {', '.join(summary['ghs_descriptions'])}\n\n"

        if summary['required_ppe']:
            md += "**Required PPE**:\n"
            for ppe in summary['required_ppe']:
                md += f"- {ppe}\n"
            md += "\n"

        if summary['special_precautions']:
            md += "**Special Precautions**:\n"
            for prec in summary['special_precautions']:
                md += f"- [WARN]️ {prec}\n"
            md += "\n"

        md += "### Reagent Hazards\n\n"
        md += "| Reagent | CAS | Signal Word | Key Hazards |\n"
        md += "|---------|-----|-------------|-------------|\n"

        for r in summary['reagent_details']:
            hazards = "; ".join(r['key_hazards'][:2]) if r['key_hazards'] else "See SDS"
            md += f"| {r['name']} | {r['cas']} | {r['signal_word']} | {hazards} |\n"

        return md
