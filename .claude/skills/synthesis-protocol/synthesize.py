"""
Synthesis Protocol Main Script
Orchestrates protocol creation, batch tracking, safety data, and Obsidian report generation
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from protocol_templates import ProtocolTemplates, SynthesisProtocol, Reagent
from batch_tracker import BatchTracker, BatchRecord
from safety_data import SafetyDataManager


class SynthesisWorkflow:
    """Main orchestration class for synthesis documentation"""

    def __init__(self, project_path: Optional[str] = None):
        self.project_path = Path(project_path) if project_path else Path(".")
        self.registry_path = self.project_path / "Synthesis" / "batch_registry.json"
        self.tracker = BatchTracker(str(self.registry_path))
        self.safety_mgr = SafetyDataManager()
        self.templates = ProtocolTemplates()

    def create_protocol(
        self,
        synthesis_method: str,
        material_id: str,
        reagents: List[Dict],
        conditions: Dict,
        zotero_reference: str = "",
        notes: str = ""
    ) -> Dict:
        """
        Create a new synthesis protocol and generate Obsidian note

        Args:
            synthesis_method: Synthesis method type
            material_id: Material identifier
            reagents: List of reagent dicts
            conditions: Synthesis conditions
            zotero_reference: Zotero citation key
            notes: Additional notes

        Returns:
            Dictionary with protocol data and file paths
        """
        # Get safety information
        safety_section = self.safety_mgr.format_safety_section(reagents)

        # Generate protocol note
        timestamp = datetime.now().strftime("%Y-%m-%d")
        protocol_filename = f"{material_id}_synthesis_protocol.md"
        protocol_path = self.project_path / "Synthesis" / "Protocols" / protocol_filename

        protocol_path.parent.mkdir(parents=True, exist_ok=True)

        content = self._generate_protocol_note(
            material_id=material_id,
            synthesis_method=synthesis_method,
            reagents=reagents,
            conditions=conditions,
            safety_section=safety_section,
            zotero_reference=zotero_reference,
            notes=notes,
            timestamp=timestamp
        )

        with open(protocol_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[OK] Protocol saved: {protocol_path}")

        return {
            "material_id": material_id,
            "synthesis_method": synthesis_method,
            "protocol_path": str(protocol_path),
            "reagents": reagents,
            "conditions": conditions
        }

    def log_batch(
        self,
        material_id: str,
        synthesis_method: str,
        reagents: List[Dict],
        conditions: Dict,
        yield_data: Optional[Dict] = None,
        operator: str = "",
        batch_id: Optional[str] = None,
        notes: str = "",
        zotero_reference: str = ""
    ) -> BatchRecord:
        """
        Log a synthesis batch

        Args:
            material_id: Material identifier
            synthesis_method: Synthesis method
            reagents: Reagent list
            conditions: Synthesis conditions
            yield_data: Yield information dict
            operator: Operator name
            batch_id: Custom batch ID
            notes: Notes
            zotero_reference: Zotero citation key

        Returns:
            Created BatchRecord
        """
        record = self.tracker.create_batch(
            material_id=material_id,
            synthesis_method=synthesis_method,
            reagents=reagents,
            conditions=conditions,
            operator=operator,
            batch_id=batch_id,
            zotero_reference=zotero_reference
        )

        if yield_data:
            record = self.tracker.update_yield(
                batch_id=record.batch_id,
                yield_mass_g=yield_data.get("mass_g"),
                theoretical_mass_g=yield_data.get("theoretical_g"),
                notes=notes
            )

        # Generate batch record note
        self._generate_batch_note(record)

        print(f"[OK] Batch logged: {record.batch_id}")
        if record.yield_percent:
            print(f"  Yield: {record.yield_percent:.1f}%")

        return record

    def _generate_protocol_note(
        self,
        material_id: str,
        synthesis_method: str,
        reagents: List[Dict],
        conditions: Dict,
        safety_section: str,
        zotero_reference: str,
        notes: str,
        timestamp: str
    ) -> str:
        """Generate Obsidian-compatible protocol markdown note"""

        content = f"""---
material_id: {material_id}
synthesis_method: {synthesis_method}
date_created: {timestamp}
type: synthesis-protocol
tags: [synthesis, protocol, {material_id}, {synthesis_method}]
---

# Synthesis Protocol: {material_id}

## Overview

- **Material**: [[Materials/{material_id}|{material_id}]]
- **Method**: {synthesis_method.replace('_', ' ').title()}
- **Date Created**: {timestamp}
"""

        if zotero_reference:
            content += f"- **Reference**: [{zotero_reference}]\n"

        content += "\n## Reagents\n\n"
        content += "| Reagent | Amount | Unit | CAS | Purity | Supplier |\n"
        content += "|---------|--------|------|-----|--------|----------|\n"

        for r in reagents:
            content += (f"| {r.get('name', '')} | {r.get('amount', '')} | "
                       f"{r.get('unit', '')} | {r.get('cas_number', '-')} | "
                       f"{r.get('purity', '-')} | {r.get('supplier', '-')} |\n")

        content += "\n## Synthesis Conditions\n\n"
        for key, value in conditions.items():
            content += f"- **{key.replace('_', ' ').title()}**: {value}\n"

        content += "\n## Procedure\n\n"
        content += "_Add detailed step-by-step procedure here_\n\n"
        content += "1. \n2. \n3. \n\n"

        content += "\n## Post-Synthesis Treatment\n\n"
        if "calcination_C" in conditions:
            content += f"- **Calcination**: {conditions['calcination_C']}°C"
            if "calcination_time_h" in conditions:
                content += f" for {conditions['calcination_time_h']} h"
            content += " in air\n"

        if "reduction_C" in conditions:
            content += f"- **Reduction**: {conditions['reduction_C']}°C"
            if "reduction_time_h" in conditions:
                content += f" for {conditions['reduction_time_h']} h"
            content += " in H₂/Ar\n"

        content += "\n"
        content += safety_section

        content += "\n## Batch Records\n\n"
        content += f"See [[Synthesis/Batches/{material_id}_batches|Batch Records]]\n\n"

        content += "## Characterization\n\n"
        content += f"- [[Characterization/XRD/{material_id}_XRD|XRD]]\n"
        content += f"- [[Characterization/BET/{material_id}_BET|BET]]\n"
        content += f"- [[Characterization/XPS/{material_id}_XPS|XPS]]\n\n"

        if notes:
            content += f"## Notes\n\n{notes}\n\n"

        return content

    def _generate_batch_note(self, record: BatchRecord):
        """Generate Obsidian note for a batch record"""
        batch_dir = self.project_path / "Synthesis" / "Batches"
        batch_dir.mkdir(parents=True, exist_ok=True)

        batch_path = batch_dir / f"{record.batch_id}.md"

        content = f"""---
batch_id: {record.batch_id}
material_id: {record.material_id}
date: {record.date}
type: synthesis-batch
status: {record.status}
tags: [synthesis, batch, {record.material_id}]
---

# Batch Record: {record.batch_id}

## Details

- **Material**: [[Materials/{record.material_id}|{record.material_id}]]
- **Protocol**: [[Synthesis/Protocols/{record.material_id}_synthesis_protocol|Protocol]]
- **Method**: {record.synthesis_method.replace('_', ' ').title()}
- **Date**: {record.date}
- **Operator**: {record.operator or 'N/A'}
- **Status**: {record.status}

## Yield

| Parameter | Value |
|-----------|-------|
| Actual Mass | {f"{record.yield_mass_g:.3f} g" if record.yield_mass_g else "N/A"} |
| Theoretical Mass | {f"{record.theoretical_mass_g:.3f} g" if record.theoretical_mass_g else "N/A"} |
| Yield | {f"{record.yield_percent:.1f}%" if record.yield_percent else "N/A"} |
| Appearance | {record.appearance or "N/A"} |

## Conditions

"""
        for key, value in record.conditions.items():
            content += f"- **{key.replace('_', ' ').title()}**: {value}\n"

        if record.notes:
            content += f"\n## Notes\n\n{record.notes}\n"

        if record.characterization_links:
            content += "\n## Characterization\n\n"
            for link in record.characterization_links:
                content += f"- [[{link}]]\n"

        if record.zotero_reference:
            content += f"\n## Reference\n\n[{record.zotero_reference}]\n"

        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[OK] Batch note saved: {batch_path}")

    def generate_synthesis_summary(self, material_id: str) -> str:
        """Generate summary of all batches for a material"""
        summary = self.tracker.get_batch_summary(material_id)
        table = self.tracker.generate_batch_table(material_id)

        report = f"# Synthesis Summary: {material_id}\n\n"
        report += f"- **Total Batches**: {summary.get('n_batches', 0)}\n"

        if "yield_mean_percent" in summary:
            report += f"- **Average Yield**: {summary['yield_mean_percent']:.1f} ± {summary['yield_std_percent']:.1f}%\n"
            report += f"- **Yield Range**: {summary['yield_min_percent']:.1f}% – {summary['yield_max_percent']:.1f}%\n"

        if "date_range" in summary:
            report += f"- **Date Range**: {summary['date_range']}\n"

        report += f"\n## Batch Records\n\n{table}\n"

        return report


def main():
    parser = argparse.ArgumentParser(description='Synthesis Protocol Manager')
    parser.add_argument('--action', required=True,
                       choices=['new_protocol', 'log_batch', 'query_safety', 'generate_report'])
    parser.add_argument('--material-id', help='Material identifier')
    parser.add_argument('--synthesis-method', help='Synthesis method')
    parser.add_argument('--reagents', type=json.loads, default='[]', help='Reagents JSON')
    parser.add_argument('--conditions', type=json.loads, default='{}', help='Conditions JSON')
    parser.add_argument('--yield-data', type=json.loads, default=None, help='Yield data JSON')
    parser.add_argument('--batch-id', help='Batch ID')
    parser.add_argument('--operator', default='', help='Operator name')
    parser.add_argument('--notes', default='', help='Notes')
    parser.add_argument('--zotero-ref', default='', help='Zotero citation key')
    parser.add_argument('--project-path', default='.', help='Project path')

    args = parser.parse_args()

    workflow = SynthesisWorkflow(project_path=args.project_path)

    if args.action == 'new_protocol':
        result = workflow.create_protocol(
            synthesis_method=args.synthesis_method,
            material_id=args.material_id,
            reagents=args.reagents,
            conditions=args.conditions,
            zotero_reference=args.zotero_ref,
            notes=args.notes
        )
        print(json.dumps(result, indent=2))

    elif args.action == 'log_batch':
        record = workflow.log_batch(
            material_id=args.material_id,
            synthesis_method=args.synthesis_method,
            reagents=args.reagents,
            conditions=args.conditions,
            yield_data=args.yield_data,
            operator=args.operator,
            batch_id=args.batch_id,
            notes=args.notes,
            zotero_reference=args.zotero_ref
        )
        print(f"Batch ID: {record.batch_id}")

    elif args.action == 'query_safety':
        safety_mgr = SafetyDataManager()
        section = safety_mgr.format_safety_section(args.reagents)
        print(section)

    elif args.action == 'generate_report':
        report = workflow.generate_synthesis_summary(args.material_id)
        print(report)


if __name__ == '__main__':
    main()
