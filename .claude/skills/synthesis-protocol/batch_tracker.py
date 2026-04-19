"""
Batch Tracker for Synthesis Records
Tracks synthesis batches, conditions, yields, and links to characterization data
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class BatchRecord:
    """Record for a single synthesis batch"""
    batch_id: str
    material_id: str
    synthesis_method: str
    date: str
    operator: str = ""
    reagents: List[Dict] = field(default_factory=list)
    conditions: Dict = field(default_factory=dict)
    yield_mass_g: Optional[float] = None
    theoretical_mass_g: Optional[float] = None
    yield_percent: Optional[float] = None
    appearance: str = ""
    notes: str = ""
    characterization_links: List[str] = field(default_factory=list)
    zotero_reference: str = ""
    status: str = "completed"  # planned, in_progress, completed, failed

    def calculate_yield(self):
        if self.yield_mass_g and self.theoretical_mass_g:
            self.yield_percent = (self.yield_mass_g / self.theoretical_mass_g) * 100


class BatchTracker:
    """Track and manage synthesis batch records"""

    def __init__(self, registry_path: str):
        """
        Initialize batch tracker

        Args:
            registry_path: Path to JSON registry file
        """
        self.registry_path = Path(registry_path)
        self.batches: Dict[str, BatchRecord] = {}
        self._load_registry()

    def _load_registry(self):
        """Load existing batch records from registry"""
        if self.registry_path.exists():
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for batch_id, record_data in data.items():
                    self.batches[batch_id] = BatchRecord(**record_data)

    def _save_registry(self):
        """Save batch records to registry"""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        data = {bid: asdict(record) for bid, record in self.batches.items()}
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def create_batch(
        self,
        material_id: str,
        synthesis_method: str,
        reagents: List[Dict],
        conditions: Dict,
        operator: str = "",
        batch_id: Optional[str] = None,
        zotero_reference: str = ""
    ) -> BatchRecord:
        """
        Create a new batch record

        Args:
            material_id: Material identifier
            synthesis_method: Synthesis method used
            reagents: List of reagent dictionaries
            conditions: Synthesis conditions dictionary
            operator: Operator name
            batch_id: Custom batch ID (auto-generated if None)
            zotero_reference: Zotero citation key

        Returns:
            Created BatchRecord
        """
        if batch_id is None:
            date_str = datetime.now().strftime("%Y%m%d")
            count = sum(1 for b in self.batches.values() if b.material_id == material_id)
            batch_id = f"{material_id}-{date_str}-{count+1:03d}"

        record = BatchRecord(
            batch_id=batch_id,
            material_id=material_id,
            synthesis_method=synthesis_method,
            date=datetime.now().strftime("%Y-%m-%d"),
            operator=operator,
            reagents=reagents,
            conditions=conditions,
            zotero_reference=zotero_reference
        )

        self.batches[batch_id] = record
        self._save_registry()
        return record

    def update_yield(
        self,
        batch_id: str,
        yield_mass_g: float,
        theoretical_mass_g: Optional[float] = None,
        appearance: str = "",
        notes: str = ""
    ) -> BatchRecord:
        """
        Update yield information for a batch

        Args:
            batch_id: Batch identifier
            yield_mass_g: Actual yield mass (g)
            theoretical_mass_g: Theoretical yield mass (g)
            appearance: Visual appearance description
            notes: Additional notes

        Returns:
            Updated BatchRecord
        """
        if batch_id not in self.batches:
            raise KeyError(f"Batch not found: {batch_id}")

        record = self.batches[batch_id]
        record.yield_mass_g = yield_mass_g
        record.appearance = appearance
        record.notes = notes

        if theoretical_mass_g:
            record.theoretical_mass_g = theoretical_mass_g

        record.calculate_yield()
        record.status = "completed"

        self._save_registry()
        return record

    def add_characterization_link(self, batch_id: str, link: str):
        """Link characterization data to a batch"""
        if batch_id not in self.batches:
            raise KeyError(f"Batch not found: {batch_id}")

        self.batches[batch_id].characterization_links.append(link)
        self._save_registry()

    def get_batches_for_material(self, material_id: str) -> List[BatchRecord]:
        """Get all batches for a given material"""
        return [b for b in self.batches.values() if b.material_id == material_id]

    def get_batch_summary(self, material_id: str) -> Dict:
        """
        Get summary statistics for all batches of a material

        Args:
            material_id: Material identifier

        Returns:
            Summary dictionary with yield statistics
        """
        batches = self.get_batches_for_material(material_id)

        if not batches:
            return {"material_id": material_id, "n_batches": 0}

        yields = [b.yield_percent for b in batches if b.yield_percent is not None]

        summary = {
            "material_id": material_id,
            "n_batches": len(batches),
            "batch_ids": [b.batch_id for b in batches],
            "date_range": f"{min(b.date for b in batches)} to {max(b.date for b in batches)}"
        }

        if yields:
            import numpy as np
            summary["yield_mean_percent"] = float(np.mean(yields))
            summary["yield_std_percent"] = float(np.std(yields))
            summary["yield_min_percent"] = float(np.min(yields))
            summary["yield_max_percent"] = float(np.max(yields))

        return summary

    def generate_batch_table(self, material_id: Optional[str] = None) -> str:
        """
        Generate markdown table of batch records

        Args:
            material_id: Filter by material (None = all batches)

        Returns:
            Markdown table string
        """
        batches = self.get_batches_for_material(material_id) if material_id else list(self.batches.values())

        if not batches:
            return "No batch records found."

        header = "| Batch ID | Material | Date | Method | Yield (g) | Yield (%) | Status |\n"
        header += "|----------|----------|------|--------|-----------|-----------|--------|\n"

        rows = []
        for b in sorted(batches, key=lambda x: x.date, reverse=True):
            yield_g = f"{b.yield_mass_g:.2f}" if b.yield_mass_g else "-"
            yield_pct = f"{b.yield_percent:.1f}" if b.yield_percent else "-"
            rows.append(
                f"| {b.batch_id} | {b.material_id} | {b.date} | "
                f"{b.synthesis_method} | {yield_g} | {yield_pct} | {b.status} |"
            )

        return header + "\n".join(rows)
