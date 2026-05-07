#!/usr/bin/env python3
"""
Generic log analyzer for test failures
Extracts FAILED CONSISTENTLY tests and recommends ticket structure
"""

import os
import re
import json
import argparse
from collections import defaultdict


def normalize_path(file_path):
    """Normalize file path"""
    if file_path.startswith('test/'):
        return file_path[5:]
    return file_path


def extract_failed_consistently(log_file):
    """Extract all FAILED CONSISTENTLY tests"""
    all_failures = set()

    with open(log_file, 'r', errors='ignore') as f:
        for line in f:
            if 'FAILED CONSISTENTLY:' in line:
                # Pattern: FAILED CONSISTENTLY: test/path/file.py::TestClass::test_method
                match = re.search(r'FAILED CONSISTENTLY:\s+(\S+?)::(\w+)::(\w+)', line)
                if match:
                    full_path = match.group(1)
                    test_class = match.group(2)
                    test_method = match.group(3)
                    normalized = normalize_path(full_path)
                    all_failures.add((normalized, test_class))

    return all_failures


def extract_detailed_errors(log_file, failures, max_per_class=10):
    """Extract detailed error messages from FAILED lines"""
    class_errors = defaultdict(list)

    with open(log_file, 'r', errors='ignore') as f:
        for line in f:
            # Match FAILED lines with errors
            match = re.match(r'FAILED\s+\[[\d\.]+s\]\s+(\S+?)::(\w+)::(\w+)(?:\s+-\s+(.+))?$', line)

            if match:
                fail_path = match.group(1)
                fail_class = match.group(2)
                fail_method = match.group(3)
                error_msg = match.group(4) if match.group(4) else "No error message captured"

                normalized = normalize_path(fail_path)

                # Check if this matches our failures
                if (normalized, fail_class) in failures:
                    key = f"{normalized}::{fail_class}"
                    if len(class_errors[key]) < max_per_class:
                        class_errors[key].append({
                            'method': fail_method,
                            'error': error_msg,
                            'full_path': f"{fail_path}::{fail_class}::{fail_method}"
                        })

    return dict(class_errors)


def club_by_file(failures):
    """Club test classes by file"""
    files_to_classes = defaultdict(set)

    for file_path, test_class in failures:
        files_to_classes[file_path].add(test_class)

    return files_to_classes


def main():
    parser = argparse.ArgumentParser(description='Analyze test logs for ticket creation')
    parser.add_argument('--log-file', required=True, help='Path to test log file')
    parser.add_argument('--platform', required=True, help='Test platform (e.g., sGPU, CPU, Distributed)')
    parser.add_argument('--output', default='analysis.json', help='Output file for analysis')
    parser.add_argument('--clubbing', default='file', choices=['file', 'directory', 'class'],
                       help='Clubbing strategy')

    args = parser.parse_args()

    print(f"Analyzing log file: {args.log_file}")
    print(f"Platform: {args.platform}")
    print()

    # Extract failures
    failures = extract_failed_consistently(args.log_file)
    print(f"Total failures: {len(failures)}")

    # Club by file
    files_to_classes = club_by_file(failures)
    print(f"Unique files: {len(files_to_classes)}")
    print()

    # Extract detailed errors
    print("Extracting detailed error messages...")
    class_errors = extract_detailed_errors(args.log_file, failures)
    print(f"Extracted errors for {len(class_errors)} test classes")
    print()

    # Build analysis output
    tickets = []
    for file_path in sorted(files_to_classes.keys()):
        test_classes = sorted(files_to_classes[file_path])
        failure_count = sum(len(class_errors.get(f"{file_path}::{cls}", [])) for cls in test_classes)

        tickets.append({
            'file_path': file_path,
            'test_classes': test_classes,
            'class_count': len(test_classes),
            'failure_count': failure_count
        })

    analysis = {
        'platform': args.platform,
        'log_file': args.log_file,
        'total_failures': len(failures),
        'unique_files': len(files_to_classes),
        'recommended_tickets': len(tickets),
        'clubbing_strategy': args.clubbing,
        'tickets': tickets
    }

    # Save analysis
    with open(args.output, 'w') as f:
        json.dump(analysis, f, indent=2)

    print(f"✅ Analysis saved to {args.output}")
    print(f"   Recommended tickets: {len(tickets)}")
    print(f"   Total failures: {len(failures)}")


if __name__ == '__main__':
    main()
