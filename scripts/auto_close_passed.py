#!/usr/bin/env python3
"""
Auto-close tickets ONLY when tests explicitly show PASSED in logs

This script is conservative - it ONLY closes tickets when it finds
explicit PASSED markers for the test, not just absence of failure.
"""

import os
import re
import argparse
import requests
from requests.auth import HTTPBasicAuth


def get_jira_credentials():
    """Get JIRA credentials from environment"""
    return {
        'url': os.getenv('JIRA_URL'),
        'email': os.getenv('JIRA_EMAIL'),
        'token': os.getenv('JIRA_API_TOKEN')
    }


def normalize_path(file_path):
    """Normalize file path - strip 'test/' prefix"""
    if file_path.startswith('test/'):
        return file_path[5:]
    return file_path


def extract_passed_tests(log_file):
    """
    Extract ONLY tests with explicit PASSED markers

    Looks for patterns like:
    - PASSED [0.5s] test/test_cuda.py::TestCuda::test_memory
    - test_memory (test_cuda.TestCuda) ... ok
    - PASSED test/test_cuda.py::TestCuda::test_memory
    """
    passed_tests = set()

    print(f"Scanning {log_file} for PASSED markers...")

    with open(log_file, 'r', errors='ignore') as f:
        for line in f:
            # Pattern 1: pytest PASSED format
            # PASSED [0.5s] test/test_cuda.py::TestCuda::test_memory
            if 'PASSED' in line:
                match = re.search(r'PASSED\s+(?:\[[\d\.]+s\]\s+)?(\S+?)::(\w+)::(\w+)', line)
                if match:
                    path = normalize_path(match.group(1))
                    cls = match.group(2)
                    method = match.group(3)
                    passed_tests.add((path, cls, method))

            # Pattern 2: unittest ok format
            # test_memory (test_cuda.TestCuda) ... ok
            elif '... ok' in line:
                match = re.search(r'(\w+)\s+\((\S+?)\.(\w+)\)\s+\.\.\.\s+ok', line)
                if match:
                    method = match.group(1)
                    module = match.group(2)
                    cls = match.group(3)
                    # Try to construct path from module
                    path = module.replace('.', '/') + '.py'
                    passed_tests.add((path, cls, method))

    print(f"  Found {len(passed_tests)} explicitly PASSED tests")
    return passed_tests


def query_jira(jql, creds):
    """Query JIRA with JQL"""
    url = f"{creds['url']}/rest/api/3/search"
    auth = HTTPBasicAuth(creds['email'], creds['token'])
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "jql": jql,
        "maxResults": 1000,
        "fields": ["key", "summary"]
    }

    response = requests.post(url, json=payload, headers=headers, auth=auth)

    if response.status_code == 200:
        return response.json()['issues']
    return []


def get_ticket_tests(ticket_key, summary, creds):
    """
    Extract test file and class from ticket summary

    Examples:
    - "[QA][PyTorch UT][Hermetic Build][sGPU] test_cuda.py - TestCuda failure"
    - "[QA][PyTorch UT][Hermetic Build][Distributed] test_*.py - TestClass1, TestClass2"
    """
    tests = set()

    # Extract filename
    filename_match = re.search(r'(test_\w+\.py)', summary)
    if not filename_match:
        return tests

    filename = filename_match.group(1)

    # Extract class names (may be multiple)
    # Pattern: ] filename - ClassName1, ClassName2 failure
    class_match = re.search(r'-\s+(.+?)\s+failure', summary)
    if not class_match:
        return tests

    classes_str = class_match.group(1)

    # Split by comma
    for cls_part in classes_str.split(','):
        cls_part = cls_part.strip()
        # Remove "and" connectors
        for cls in cls_part.split(' and '):
            cls = cls.strip()
            # Simple identifier check
            if cls and cls.replace('_', '').isalnum():
                tests.add((filename, cls))

    return tests


def close_ticket(ticket_key, comment, creds):
    """Close ticket with Done resolution"""

    # Step 1: Get available transitions
    url = f"{creds['url']}/rest/api/3/issue/{ticket_key}/transitions"
    auth = HTTPBasicAuth(creds['email'], creds['token'])
    headers = {"Accept": "application/json"}

    response = requests.get(url, headers=headers, auth=auth)

    if response.status_code != 200:
        return False, f"Cannot get transitions: {response.status_code}"

    transitions = response.json()['transitions']

    # Find "Done" or "Close" transition
    transition_id = None
    for trans in transitions:
        if trans['name'].lower() in ['done', 'close', 'closed', 'resolve', 'resolved']:
            transition_id = trans['id']
            break

    if not transition_id:
        return False, "No Done/Close transition available"

    # Step 2: Transition to Done
    url = f"{creds['url']}/rest/api/3/issue/{ticket_key}/transitions"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "transition": {"id": transition_id},
        "fields": {
            "resolution": {"name": "Done"}
        },
        "update": {
            "comment": [{
                "add": {
                    "body": {
                        "version": 1,
                        "type": "doc",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": comment}]
                        }]
                    }
                }
            }]
        }
    }

    response = requests.post(url, json=payload, headers=headers, auth=auth)

    if response.status_code in [200, 204]:
        return True, None
    else:
        return False, f"Error {response.status_code}: {response.text[:200]}"


def main():
    parser = argparse.ArgumentParser(
        description='Auto-close tickets when tests explicitly show PASSED in logs',
        epilog='Example:\n'
               '  %(prog)s --log latest_build.log --jql "status != Closed AND labels = pytorch_hermetic"\n\n'
               'Note: Only closes tickets where ALL tests show explicit PASSED markers',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--log', required=True, help='Log file with PASSED test results')
    parser.add_argument('--jql', required=True, help='JQL to find tickets to check')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be closed without actually closing')
    parser.add_argument('--build-info', help='Build information to include in comment (e.g., "PyTorch 2.12-RC8")')

    args = parser.parse_args()

    # Get credentials
    creds = get_jira_credentials()
    if not all(creds.values()):
        print("❌ Error: Set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN environment variables")
        return

    print("=" * 80)
    print("AUTO-CLOSE PASSED TICKETS (EXPLICIT PASS REQUIRED)")
    print("=" * 80)
    print()

    # Step 1: Extract explicitly PASSED tests
    passed_tests = extract_passed_tests(args.log)

    if not passed_tests:
        print("\n❌ No PASSED tests found in log!")
        print("   Make sure the log contains explicit PASSED markers")
        return

    # Convert to (filename, class) for matching
    passed_test_keys = {(path.split('/')[-1], cls) for path, cls, method in passed_tests}

    print()
    print(f"PASSED test classes: {len(passed_test_keys)}")
    for path, cls in sorted(passed_test_keys)[:10]:
        print(f"  - {path}::{cls}")
    if len(passed_test_keys) > 10:
        print(f"  ... and {len(passed_test_keys) - 10} more")
    print()

    # Step 2: Query tickets
    print("Querying JIRA...")
    tickets = query_jira(args.jql, creds)
    print(f"  Found {len(tickets)} tickets to check")
    print()

    # Step 3: Check each ticket
    print("Checking tickets...")
    print()

    to_close = []
    still_failing = []

    for ticket in tickets:
        ticket_key = ticket['key']
        summary = ticket['fields']['summary']

        # Extract tests from ticket
        ticket_tests = get_ticket_tests(ticket_key, summary, creds)

        if not ticket_tests:
            print(f"{ticket_key}: Could not parse tests from summary")
            continue

        # Check if ALL ticket tests are in PASSED list
        all_passed = ticket_tests.issubset(passed_test_keys)

        if all_passed:
            print(f"{ticket_key}: ✅ All tests PASSED")
            to_close.append(ticket_key)
        else:
            not_passed = ticket_tests - passed_test_keys
            print(f"{ticket_key}: ❌ Still has tests without PASSED marker ({len(not_passed)} tests)")
            still_failing.append(ticket_key)

    # Step 4: Close tickets
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Tickets checked: {len(tickets)}")
    print(f"All tests PASSED: {len(to_close)}")
    print(f"Still failing or no PASSED marker: {len(still_failing)}")
    print()

    if not to_close:
        print("✅ No tickets to close")
        return

    print(f"Tickets to close: {', '.join(to_close)}")
    print()

    if args.dry_run:
        print("🔍 DRY RUN - No tickets will be closed")
        return

    # Close tickets
    print("Closing tickets...")
    closed_count = 0
    failed_count = 0

    build_info = args.build_info or os.path.basename(args.log)

    for ticket_key in to_close:
        print(f"  {ticket_key}...", end=" ", flush=True)

        comment = f"Auto-closed: All tests showing explicit PASSED markers in {build_info}"
        success, error = close_ticket(ticket_key, comment, creds)

        if success:
            print("✅")
            closed_count += 1
        else:
            print(f"❌ {error}")
            failed_count += 1

    print()
    print("=" * 80)
    print(f"Successfully closed: {closed_count}")
    print(f"Failed to close: {failed_count}")
    print("=" * 80)


if __name__ == '__main__':
    main()
