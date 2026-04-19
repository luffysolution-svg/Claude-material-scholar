"""
Materials Paper Review - Main Script
"""

import sys
import json
import argparse
from pathlib import Path
from manuscript_checker import ManuscriptReviewer


def main():
    parser = argparse.ArgumentParser(description='Materials Science Manuscript Review')
    parser.add_argument('--manuscript', required=True, help='Path to manuscript file')
    parser.add_argument('--journal', default='general', help='Target journal')
    parser.add_argument('--research-type', default='heterogeneous_catalysis', help='Research type')
    parser.add_argument('--output', help='Output path for review report')
    args = parser.parse_args()

    manuscript_path = Path(args.manuscript)
    if not manuscript_path.exists():
        print(f"Error: Manuscript not found: {manuscript_path}")
        sys.exit(1)

    content = manuscript_path.read_text(encoding='utf-8', errors='ignore')

    reviewer = ManuscriptReviewer(journal=args.journal, research_type=args.research_type)
    report = reviewer.review_manuscript(content, str(manuscript_path))
    formatted = reviewer.format_report(report)

    sys.stdout.buffer.write(formatted.encode('utf-8', errors='replace'))
    sys.stdout.buffer.write(b'\n')

    if args.output:
        Path(args.output).write_text(formatted, encoding='utf-8')
        sys.stdout.buffer.write(f"\nReport saved: {args.output}\n".encode('utf-8'))


if __name__ == '__main__':
    main()
