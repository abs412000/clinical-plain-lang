#!/usr/bin/env python3
"""
cli.py
------
Command-line interface for clinical-plain-lang (Gemini version).

Usage:
    python cli.py --file myreport.txt --audience patient
    python cli.py --file myreport.txt --all-audiences
"""

import argparse
import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from converter import ClinicalPlainLangConverter, format_report


def main():
    parser = argparse.ArgumentParser(
        description="Convert clinical/medical documents into plain language summaries using Google Gemini.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --file report.txt --audience patient
  python cli.py --file report.txt --all-audiences
  python cli.py --file report.txt --audience public --output result.json
  cat report.txt | python cli.py --stdin --audience caregiver
        """
    )

    # Input
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--file", "-f", type=str, help="Path to input clinical document (txt)")
    input_group.add_argument("--stdin", action="store_true", help="Read input from stdin")

    # Audience
    audience_group = parser.add_mutually_exclusive_group(required=True)
    audience_group.add_argument(
        "--audience", "-a",
        choices=["patient", "public", "caregiver"],
        help="Target audience for plain language output"
    )
    audience_group.add_argument(
        "--all-audiences",
        action="store_true",
        help="Generate output for all three audience levels"
    )

    # Output
    parser.add_argument("--output", "-o", type=str, help="Save JSON results to this file")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress progress messages")
    parser.add_argument("--json", action="store_true", help="Print raw JSON output instead of formatted report")

    args = parser.parse_args()

    # ── Read input ──
    if args.stdin:
        clinical_text = sys.stdin.read()
    else:
        if not os.path.exists(args.file):
            print(f"ERROR: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            clinical_text = f.read()

    if not clinical_text.strip():
        print("ERROR: Input text is empty.", file=sys.stderr)
        sys.exit(1)

    # ── Check API key ──
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable not set.", file=sys.stderr)
        print("Set it using: $env:GEMINI_API_KEY = 'your-api-key-here'  (PowerShell)", file=sys.stderr)
        print("           or: export GEMINI_API_KEY='your-api-key-here'  (bash/zsh)", file=sys.stderr)
        sys.exit(1)

    # ── Run conversion ──
    try:
        converter = ClinicalPlainLangConverter()

        if args.all_audiences:
            if not args.quiet:
                print("Converting for all audiences (patient, public, caregiver)...")
            results = converter.convert_all_audiences(clinical_text)

            if args.json or args.output:
                output_data = results
            else:
                for audience, result in results.items():
                    print(format_report(result))

        else:
            if not args.quiet:
                print(f"Converting for audience: {args.audience}...")
            result = converter.convert(clinical_text, audience=args.audience)

            if args.json or args.output:
                output_data = result
            else:
                print(format_report(result))

        # ── Save JSON if requested ──
        if args.output or args.json:
            json_str = json.dumps(output_data, indent=2, ensure_ascii=False)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(json_str)
                if not args.quiet:
                    print(f"\nResults saved to: {args.output}")
            if args.json:
                print(json_str)

    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()