#!/usr/bin/env python3
"""
Materials Research Project Initialization Script

This script initializes a new materials research project with:
- Obsidian-compatible directory structure
- Project hub from template
- Zotero collection creation (optional)
- Project registry binding
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
import argparse


def create_directory_structure(base_path, project_name):
    """Create the Obsidian-compatible directory structure."""
    project_path = base_path / project_name

    directories = [
        "Materials",
        "Characterization/XRD",
        "Characterization/BET",
        "Characterization/TEM",
        "Characterization/XPS",
        "Characterization/Electrochemistry",
        "Reactions/Results",
        "Reactions/Conditions",
        "Synthesis/Protocols",
        "Synthesis/Batches",
        "Computational/DFT",
        "Computational/MD",
        "Papers",
        "Writing/Manuscripts",
        "Writing/Presentations",
        "Daily"
    ]

    for directory in directories:
        dir_path = project_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to preserve empty directories
        (dir_path / ".gitkeep").touch()

    return project_path


def generate_hub_file(project_path, project_name, research_focus, pi_name):
    """Generate 00-Hub.md from template."""
    template_path = Path(__file__).parent.parent.parent.parent / "Research" / "templates" / "00-Hub.md"

    if not template_path.exists():
        print(f"Warning: Template not found at {template_path}")
        return

    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()

    # Replace template variables
    current_date = datetime.now().strftime("%Y-%m-%d")
    project_tag = project_name.lower().replace(" ", "-")

    content = template_content.replace("{{PROJECT_NAME}}", project_name)
    content = content.replace("{{DATE}}", current_date)
    content = content.replace("{{PROJECT_TAG}}", project_tag)
    content = content.replace("{{RESEARCH_FOCUS}}", research_focus)
    content = content.replace("{{PI_NAME}}", pi_name or "TBD")
    content = content.replace("{{OBJECTIVE_1}}", "Define research objectives")
    content = content.replace("{{OBJECTIVE_2}}", "Synthesize and characterize materials")
    content = content.replace("{{OBJECTIVE_3}}", "Evaluate catalytic performance")
    content = content.replace("{{NEXT_STEP_1}}", "Literature review")
    content = content.replace("{{NEXT_STEP_2}}", "Material synthesis planning")

    # Placeholder for Zotero collections
    content = content.replace("{{ZOTERO_COLLECTION_CORE}}", "TBD")
    content = content.replace("{{ZOTERO_COLLECTION_CATALYSTS}}", "TBD")
    content = content.replace("{{ZOTERO_COLLECTION_CHAR}}", "TBD")
    content = content.replace("{{ZOTERO_COLLECTION_MECH}}", "TBD")
    content = content.replace("{{ZOTERO_COLLECTION_SYNTH}}", "TBD")
    content = content.replace("{{ZOTERO_COLLECTION_COMP}}", "TBD")

    hub_path = project_path / "00-Hub.md"
    with open(hub_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[OK] Created project hub: {hub_path}")


def create_project_readme(project_path, project_name, research_focus):
    """Create README.md in project directory."""
    readme_content = f"""# {project_name}

## Research Focus

{research_focus}

## Project Structure

- **00-Hub.md**: Project overview and quick links
- **Materials/**: Catalyst materials and compositions
- **Characterization/**: XRD, BET, TEM, XPS, electrochemistry data
- **Reactions/**: Catalysis experiments and performance results
- **Synthesis/**: Synthesis protocols and batch records
- **Computational/**: DFT calculations and mechanism analysis
- **Papers/**: Literature notes and references
- **Writing/**: Manuscripts, presentations, and reports
- **Daily/**: Daily research notes and lab notebook entries

## Getting Started

1. Review and update 00-Hub.md with your research objectives
2. Run literature search: Use `/materials-literature` or materials-literature skill
3. Document synthesis procedures in Synthesis/Protocols/
4. Record characterization data in appropriate subdirectories
5. Track catalysis experiments in Reactions/

## Zotero Integration

This project is configured to work with Zotero for reference management.
Collections should be created for:
- Core Papers
- Catalysts
- Characterization Methods
- Reaction Mechanisms
- Synthesis Methods
- Computational Studies

## Commands

- `/characterization` - Analyze characterization data
- `/catalysis-results` - Evaluate catalysis performance
- `/dft-analysis` - Parse computational results
- `/synthesis-log` - Document synthesis procedures
- `/manuscript-draft` - Generate manuscript draft

## Notes

- Use Obsidian for best experience with bidirectional linking
- All markdown files support YAML frontmatter for metadata
- Link between notes using [[Note Name]] syntax
"""

    readme_path = project_path / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"[OK] Created project README: {readme_path}")


def update_project_registry(project_name, project_path):
    """Update .claude/project-memory/registry.yaml with project binding."""
    registry_dir = Path.cwd() / ".claude" / "project-memory"
    registry_dir.mkdir(parents=True, exist_ok=True)

    registry_path = registry_dir / "registry.yaml"

    registry_entry = f"""
# Project: {project_name}
{project_name}:
  path: {project_path}
  type: materials-research
  created: {datetime.now().isoformat()}
"""

    # Append to registry (or create if doesn't exist)
    with open(registry_path, 'a', encoding='utf-8') as f:
        f.write(registry_entry)

    print(f"[OK] Updated project registry: {registry_path}")


def generate_initialization_report(project_name, project_path, research_focus):
    """Generate initialization report."""
    report = f"""
{'='*60}
MATERIALS RESEARCH PROJECT INITIALIZED
{'='*60}

Project Name: {project_name}
Research Focus: {research_focus}
Project Path: {project_path}
Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Directory Structure Created:
  [OK] Materials/
  [OK] Characterization/ (XRD, BET, TEM, XPS, Electrochemistry)
  [OK] Reactions/ (Results, Conditions)
  [OK] Synthesis/ (Protocols, Batches)
  [OK] Computational/ (DFT, MD)
  [OK] Papers/
  [OK] Writing/ (Manuscripts, Presentations)
  [OK] Daily/

Files Created:
  [OK] 00-Hub.md (Project overview)
  [OK] README.md (Setup instructions)

Next Steps:
  1. Review and customize 00-Hub.md
  2. Set up Zotero collections for literature management
  3. Run literature search for your research topic
  4. Begin documenting synthesis protocols
  5. Start characterization data collection

Recommended Commands:
  - Use existing 'literature-review' skill for paper search
  - Use 'scientific-writing' skill for manuscript preparation
  - Use 'exploratory-data-analysis' for characterization data

{'='*60}
"""
    print(report)


def main():
    parser = argparse.ArgumentParser(description="Initialize materials research project")
    parser.add_argument("project_name", help="Name of the research project")
    parser.add_argument("research_focus", help="Brief description of research focus")
    parser.add_argument("--pi-name", default="", help="Principal investigator name")
    parser.add_argument("--base-path", default="Research", help="Base path for projects")

    args = parser.parse_args()

    # Determine base path
    base_path = Path.cwd() / args.base_path
    base_path.mkdir(parents=True, exist_ok=True)

    # Create project structure
    print(f"\nInitializing project: {args.project_name}")
    print(f"Research focus: {args.research_focus}\n")

    project_path = create_directory_structure(base_path, args.project_name)
    print(f"[OK] Created directory structure at: {project_path}")

    generate_hub_file(project_path, args.project_name, args.research_focus, args.pi_name)
    create_project_readme(project_path, args.project_name, args.research_focus)
    update_project_registry(args.project_name, project_path)

    generate_initialization_report(args.project_name, project_path, args.research_focus)

    return 0


if __name__ == "__main__":
    sys.exit(main())
