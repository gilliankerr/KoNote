#!/usr/bin/env python
"""
Validate .po translation files for common errors.

Checks for duplicate msgid entries that would cause compilemessages to fail.
Run this before compilemessages to get clear, actionable error messages.
"""

import re
import sys
from pathlib import Path
from collections import defaultdict


def find_duplicate_msgids(po_file_path):
    """Find duplicate msgid entries in a .po file."""
    with open(po_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all msgid entries with their line numbers
    msgid_locations = defaultdict(list)

    for i, line in enumerate(content.split('\n'), start=1):
        if line.startswith('msgid "') and line != 'msgid ""':
            # Extract the msgid string
            match = re.match(r'^msgid "(.+)"$', line)
            if match:
                msgid = match.group(1)
                msgid_locations[msgid].append(i)

    # Find duplicates (msgids appearing more than once)
    duplicates = {
        msgid: lines
        for msgid, lines in msgid_locations.items()
        if len(lines) > 1
    }

    return duplicates


def main():
    """Check all .po files in locale directories."""
    locale_dir = Path(__file__).parent.parent / 'locale'

    if not locale_dir.exists():
        print("No locale directory found - skipping translation validation")
        return 0

    po_files = list(locale_dir.glob('*/LC_MESSAGES/*.po'))

    if not po_files:
        print("No .po files found - skipping translation validation")
        return 0

    errors_found = False

    for po_file in po_files:
        duplicates = find_duplicate_msgids(po_file)

        if duplicates:
            errors_found = True
            rel_path = po_file.relative_to(locale_dir.parent)

            print(f"\n{'='*60}")
            print(f"ERROR: Duplicate translations in {rel_path}")
            print(f"{'='*60}")
            print(f"\nFound {len(duplicates)} duplicate msgid entries:\n")

            for msgid, lines in duplicates.items():
                print(f'  "{msgid}"')
                print(f'    appears on lines: {", ".join(map(str, lines))}')
                print()

            print("HOW TO FIX:")
            print("-----------")
            print(f"1. Open {rel_path}")
            print("2. Search for each duplicate msgid listed above")
            print("3. Keep ONE copy (usually the first one) and delete the others")
            print("4. Make sure to delete the entire block (msgid + msgstr lines)")
            print()

    if errors_found:
        print("Translation validation FAILED - fix duplicates before deploying")
        return 1

    print(f"Translation validation passed - checked {len(po_files)} file(s)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
