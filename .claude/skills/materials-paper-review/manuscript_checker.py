"""
Materials Science Manuscript Review
Comprehensive self-review checklist for materials science papers
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ReviewItem:
    category: str
    item: str
    status: str = "unchecked"  # pass, fail, warning, unchecked
    notes: str = ""
    severity: str = "major"  # major, minor, suggestion


@dataclass
class ReviewReport:
    manuscript_path: str
    journal: str
    research_type: str
    items: List[ReviewItem] = field(default_factory=list)
    score: float = 0.0

    def add_item(self, category: str, item: str, status: str,
                 notes: str = "", severity: str = "major"):
        self.items.append(ReviewItem(category, item, status, notes, severity))

    def calculate_score(self):
        if not self.items:
            return 0.0
        passed = sum(1 for i in self.items if i.status == "pass")
        total = sum(1 for i in self.items if i.status != "unchecked")
        self.score = (passed / total * 100) if total > 0 else 0.0
        return self.score


# Journal-specific requirements
JOURNAL_REQUIREMENTS = {
    "ACS Catalysis": {
        "word_limit": 8000,
        "abstract_limit": 200,
        "required_sections": ["Introduction", "Experimental", "Results", "Discussion", "Conclusions"],
        "required_characterization": ["XRD", "BET", "TEM"],
        "required_performance": ["TOF", "selectivity", "stability"],
        "citation_style": "ACS",
        "figure_format": "TIFF or EPS, 300 dpi minimum"
    },
    "Journal of Catalysis": {
        "word_limit": 10000,
        "abstract_limit": 250,
        "required_sections": ["Introduction", "Experimental", "Results and Discussion", "Conclusions"],
        "required_characterization": ["XRD", "BET"],
        "required_performance": ["conversion", "selectivity"],
        "citation_style": "numbered",
        "figure_format": "EPS or TIFF, 300 dpi"
    },
    "Nature Materials": {
        "word_limit": 3000,
        "abstract_limit": 150,
        "required_sections": ["Introduction", "Results", "Discussion", "Methods"],
        "required_characterization": ["XRD", "TEM"],
        "required_performance": [],
        "citation_style": "numbered",
        "figure_format": "PDF or EPS, 300 dpi"
    },
    "Advanced Materials": {
        "word_limit": 5000,
        "abstract_limit": 200,
        "required_sections": ["Introduction", "Results and Discussion", "Conclusions", "Experimental"],
        "required_characterization": ["XRD", "TEM", "XPS"],
        "required_performance": [],
        "citation_style": "numbered",
        "figure_format": "TIFF or EPS, 300 dpi"
    },
    "general": {
        "word_limit": None,
        "abstract_limit": None,
        "required_sections": ["Introduction", "Experimental", "Results", "Discussion", "Conclusions"],
        "required_characterization": ["XRD"],
        "required_performance": [],
        "citation_style": "any",
        "figure_format": "300 dpi minimum"
    }
}

# Characterization completeness requirements by research type
CHARACTERIZATION_REQUIREMENTS = {
    "heterogeneous_catalysis": {
        "essential": ["XRD", "BET surface area", "TEM/SEM"],
        "recommended": ["XPS", "H2-TPR", "CO chemisorption", "ICP-OES"],
        "performance": ["conversion", "selectivity", "TOF", "stability", "activation energy"]
    },
    "electrocatalysis": {
        "essential": ["XRD", "TEM", "XPS"],
        "recommended": ["BET", "Raman", "XANES/EXAFS"],
        "performance": ["overpotential", "Tafel slope", "TOF", "stability", "Faradaic efficiency"]
    },
    "computational": {
        "essential": ["DFT method", "basis set", "convergence criteria"],
        "recommended": ["benchmark calculations", "dispersion correction", "solvation model"],
        "performance": ["activation energy", "reaction energy", "adsorption energy"]
    },
    "synthesis": {
        "essential": ["XRD", "TEM", "elemental analysis"],
        "recommended": ["BET", "TGA", "NMR/FTIR"],
        "performance": ["yield", "purity", "reproducibility"]
    }
}


class ManuscriptReviewer:
    """Review materials science manuscripts for completeness and quality"""

    def __init__(self, journal: str = "general", research_type: str = "heterogeneous_catalysis"):
        self.journal = journal
        self.research_type = research_type
        self.journal_reqs = JOURNAL_REQUIREMENTS.get(journal, JOURNAL_REQUIREMENTS["general"])
        self.char_reqs = CHARACTERIZATION_REQUIREMENTS.get(
            research_type, CHARACTERIZATION_REQUIREMENTS["heterogeneous_catalysis"]
        )

    def review_manuscript(self, content: str, manuscript_path: str) -> ReviewReport:
        """
        Perform comprehensive manuscript review

        Args:
            content: Manuscript text content
            manuscript_path: Path to manuscript file

        Returns:
            ReviewReport with all check results
        """
        report = ReviewReport(
            manuscript_path=manuscript_path,
            journal=self.journal,
            research_type=self.research_type
        )

        # Run all review checks
        self._check_structure(content, report)
        self._check_abstract(content, report)
        self._check_characterization(content, report)
        self._check_performance_data(content, report)
        self._check_statistics(content, report)
        self._check_figures_tables(content, report)
        self._check_citations(content, report)
        self._check_experimental_details(content, report)
        self._check_journal_requirements(content, report)

        report.calculate_score()
        return report

    def _check_structure(self, content: str, report: ReviewReport):
        """Check manuscript structure and required sections"""
        required = self.journal_reqs["required_sections"]

        for section in required:
            # Check for section header (case-insensitive)
            # Use raw string concat to avoid f-string/regex quantifier conflict
            escaped = re.escape(section)
            pattern = r'#{1,3}\s+' + escaped + r'|^' + escaped + r'\s*$'
            found = bool(re.search(pattern, content, re.IGNORECASE | re.MULTILINE))
            report.add_item(
                "Structure",
                f"Section: {section}",
                "pass" if found else "fail",
                "" if found else f"Missing required section: {section}"
            )

        # Check for title
        has_title = bool(re.search(r'^#\s+\S', content, re.MULTILINE))
        report.add_item("Structure", "Title present", "pass" if has_title else "fail",
                       severity="major")

        # Check for keywords
        has_keywords = bool(re.search(r'keyword', content, re.IGNORECASE))
        report.add_item("Structure", "Keywords present", "pass" if has_keywords else "warning",
                       severity="minor")

    def _check_abstract(self, content: str, report: ReviewReport):
        """Check abstract quality and length"""
        abstract_match = re.search(
            r'(?:^#{1,3}\s+(?:abstract|summary).*?$)\n+(.*?)(?=\n#{1,3}\s|\Z)',
            content, re.IGNORECASE | re.DOTALL | re.MULTILINE
        )

        if not abstract_match:
            report.add_item("Abstract", "Abstract present", "fail",
                           "No abstract found", severity="major")
            return

        abstract_text = abstract_match.group(1).strip()
        word_count = len(abstract_text.split())

        report.add_item("Abstract", "Abstract present", "pass")

        # Check length
        limit = self.journal_reqs.get("abstract_limit")
        if limit:
            status = "pass" if word_count <= limit else "fail"
            report.add_item("Abstract", f"Abstract length (≤{limit} words)",
                           status, f"Current: {word_count} words")

        # Check for key elements
        for element in ["catalyst", "reaction", "result", "conclusion"]:
            found = bool(re.search(element, abstract_text, re.IGNORECASE))
            report.add_item("Abstract", f"Abstract mentions {element}",
                           "pass" if found else "warning", severity="minor")

        # Check for quantitative data in abstract
        has_numbers = bool(re.search(r'\d+\.?\d*\s*%|\d+\.?\d*\s*h⁻¹|\d+\.?\d*\s*kJ', abstract_text))
        report.add_item("Abstract", "Quantitative data in abstract",
                       "pass" if has_numbers else "warning",
                       "Include key quantitative results", severity="minor")

    def _check_characterization(self, content: str, report: ReviewReport):
        """Check characterization completeness"""
        essential = self.char_reqs["essential"]
        recommended = self.char_reqs["recommended"]

        for tech in essential:
            # Handle "TEM/SEM" style entries — match either part
            parts = [p.strip() for p in tech.split('/')]
            found = any(bool(re.search(re.escape(p), content, re.IGNORECASE)) for p in parts)
            report.add_item("Characterization", f"Essential: {tech}",
                           "pass" if found else "fail",
                           f"Missing essential characterization: {tech}", severity="major")

        for tech in recommended:
            found = bool(re.search(re.escape(tech), content, re.IGNORECASE))
            report.add_item("Characterization", f"Recommended: {tech}",
                           "pass" if found else "warning",
                           f"Consider adding: {tech}", severity="minor")

        # Check for characterization of fresh vs. used catalyst
        if self.research_type == "heterogeneous_catalysis":
            has_used = bool(re.search(r'used\s+catalyst|spent\s+catalyst|post.reaction', content, re.IGNORECASE))
            report.add_item("Characterization", "Used/spent catalyst characterization",
                           "pass" if has_used else "warning",
                           "Characterize catalyst after reaction to understand deactivation",
                           severity="minor")

    def _check_performance_data(self, content: str, report: ReviewReport):
        """Check catalytic performance data completeness"""
        required_perf = self.char_reqs["performance"]

        for metric in required_perf:
            found = bool(re.search(re.escape(metric), content, re.IGNORECASE))
            report.add_item("Performance Data", f"Metric: {metric}",
                           "pass" if found else "warning",
                           f"Consider reporting: {metric}", severity="minor")

        # Check for reaction conditions
        conditions = ["temperature", "pressure", "flow rate", "GHSV", "WHSV"]
        for cond in conditions:
            found = bool(re.search(re.escape(cond), content, re.IGNORECASE))
            report.add_item("Performance Data", f"Condition: {cond}",
                           "pass" if found else "warning", severity="minor")

        # Check for stability data
        has_stability = bool(re.search(r'stability|time.on.stream|deactivation|regeneration', content, re.IGNORECASE))
        report.add_item("Performance Data", "Stability/durability data",
                       "pass" if has_stability else "warning",
                       "Include time-on-stream stability data", severity="minor")

    def _check_statistics(self, content: str, report: ReviewReport):
        """Check statistical reporting"""
        # Check for error bars / standard deviation
        has_error = bool(re.search(r'±|std|standard deviation|error bar|confidence', content, re.IGNORECASE))
        report.add_item("Statistics", "Error bars/uncertainty reported",
                       "pass" if has_error else "warning",
                       "Report experimental uncertainty (±std or ±SEM)", severity="minor")

        # Check for replicate experiments
        has_replicates = bool(re.search(r'triplicate|duplicate|replicate|n\s*=\s*\d', content, re.IGNORECASE))
        report.add_item("Statistics", "Replicate experiments mentioned",
                       "pass" if has_replicates else "warning",
                       "Mention number of replicates", severity="minor")

    def _check_figures_tables(self, content: str, report: ReviewReport):
        """Check figures and tables"""
        # Count figures
        fig_count = len(re.findall(r'(?:Figure|Fig\.)\s*\d+', content, re.IGNORECASE))
        report.add_item("Figures/Tables", f"Figures present ({fig_count})",
                       "pass" if fig_count > 0 else "fail", severity="major")

        # Check figure captions
        has_captions = bool(re.search(r'(?:Figure|Fig\.)\s*\d+[.:]\s*\S', content, re.IGNORECASE))
        report.add_item("Figures/Tables", "Figure captions present",
                       "pass" if has_captions else "fail", severity="major")

        # Check for comparison table
        has_table = bool(re.search(r'\|.*\|.*\|', content))
        report.add_item("Figures/Tables", "Comparison table present",
                       "pass" if has_table else "warning",
                       "Include literature comparison table", severity="minor")

    def _check_citations(self, content: str, report: ReviewReport):
        """Check citation completeness"""
        # Count citations
        citation_count = len(re.findall(r'\[\d+\]|\[[\w,\s]+\d{4}\w*\]', content))
        report.add_item("Citations", f"Citations present ({citation_count})",
                       "pass" if citation_count > 5 else "warning",
                       f"Found {citation_count} citations", severity="minor")

        # Check for seminal references
        seminal_topics = ["Sabatier", "Brønsted-Evans-Polanyi", "volcano plot", "d-band theory"]
        for topic in seminal_topics:
            if re.search(re.escape(topic), content, re.IGNORECASE):
                report.add_item("Citations", f"Seminal reference: {topic}",
                               "warning", f"Ensure {topic} is properly cited", severity="minor")

    def _check_experimental_details(self, content: str, report: ReviewReport):
        """Check experimental section completeness"""
        exp_section = re.search(
            r'(?:^#{1,3}\s+(?:experimental|methods?).*?$)\n+(.*?)(?=\n#{1,3}\s|\Z)',
            content, re.IGNORECASE | re.DOTALL | re.MULTILINE
        )

        if not exp_section:
            report.add_item("Experimental", "Experimental section present", "fail", severity="major")
            return

        exp_text = exp_section.group(1)

        # Check for synthesis details
        has_synthesis = bool(re.search(r'synthesis|preparation|calcin|impregnation', exp_text, re.IGNORECASE))
        report.add_item("Experimental", "Synthesis procedure described",
                       "pass" if has_synthesis else "fail", severity="major")

        # Check for characterization methods
        has_char_methods = bool(re.search(r'XRD|BET|XPS|TEM|ICP', exp_text, re.IGNORECASE))
        report.add_item("Experimental", "Characterization methods described",
                       "pass" if has_char_methods else "fail", severity="major")

        # Check for catalytic test conditions
        has_test = bool(re.search(r'catalytic|reaction|temperature|flow|GHSV', exp_text, re.IGNORECASE))
        report.add_item("Experimental", "Catalytic test conditions described",
                       "pass" if has_test else "fail", severity="major")

        # Check for reagent grades/suppliers
        has_suppliers = bool(re.search(r'Sigma|Aldrich|Alfa|Aesar|purity|grade|%\s+pure', exp_text, re.IGNORECASE))
        report.add_item("Experimental", "Reagent grades/suppliers mentioned",
                       "pass" if has_suppliers else "warning",
                       "Specify reagent purity and supplier", severity="minor")

    def _check_journal_requirements(self, content: str, report: ReviewReport):
        """Check journal-specific requirements"""
        # Word count
        word_limit = self.journal_reqs.get("word_limit")
        if word_limit:
            word_count = len(content.split())
            status = "pass" if word_count <= word_limit else "fail"
            report.add_item("Journal Requirements", f"Word count (≤{word_limit})",
                           status, f"Current: ~{word_count} words", severity="major")

        # Required characterization for journal
        for tech in self.journal_reqs.get("required_characterization", []):
            found = bool(re.search(re.escape(tech), content, re.IGNORECASE))
            report.add_item("Journal Requirements", f"Required by {self.journal}: {tech}",
                           "pass" if found else "fail",
                           f"{self.journal} requires {tech} characterization", severity="major")

    def format_report(self, report: ReviewReport) -> str:
        """Format review report as markdown"""
        md = f"""# Manuscript Review Report

**Journal**: {report.journal}
**Research Type**: {report.research_type}
**Overall Score**: {report.score:.1f}%

---

"""
        # Group by category
        categories = {}
        for item in report.items:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)

        # Status icons
        icons = {"pass": "[PASS]", "fail": "[FAIL]", "warning": "[WARN]️", "unchecked": "[ ]"}

        for category, items in categories.items():
            passed = sum(1 for i in items if i.status == "pass")
            total = len(items)
            md += f"## {category} ({passed}/{total})\n\n"

            for item in items:
                icon = icons.get(item.status, "[ ]")
                md += f"- {icon} **{item.item}**"
                if item.notes:
                    md += f"\n  > {item.notes}"
                md += "\n"
            md += "\n"

        # Summary
        failures = [i for i in report.items if i.status == "fail" and i.severity == "major"]
        warnings = [i for i in report.items if i.status in ("fail", "warning") and i.severity == "minor"]

        if failures:
            md += "## Critical Issues (Must Fix)\n\n"
            for item in failures:
                md += f"1. **{item.category}**: {item.item}"
                if item.notes:
                    md += f" — {item.notes}"
                md += "\n"
            md += "\n"

        if warnings:
            md += "## Suggestions (Recommended)\n\n"
            for item in warnings[:10]:  # Top 10
                md += f"- {item.category}: {item.item}"
                if item.notes:
                    md += f" — {item.notes}"
                md += "\n"

        return md
