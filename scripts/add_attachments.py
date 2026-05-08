#!/usr/bin/env python3
"""
Add attachments to JIRA tickets
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


def add_attachment(ticket_key, file_path, creds):
    """Add an attachment to a ticket"""
    url = f"{creds['url']}/rest/api/3/issue/{ticket_key}/attachments"
    auth = HTTPBasicAuth(creds['email'], creds['token'])
    headers = {
        "Accept": "application/json",
        "X-Atlassian-Token": "no-check"
    }

    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f)}
        response = requests.post(url, files=files, headers=headers, auth=auth)

    if response.status_code in [200, 201]:
        return True, None
    else:
        return False, f"Error {response.status_code}: {response.text[:200]}"


def parse_ticket_range(range_str):
    """Parse ticket range like PROJ-100:150 into list"""
    match = re.match(r'([A-Z]+-)?(\d+):(\d+)', range_str)
    if match:
        prefix = match.group(1) or os.getenv('JIRA_PROJECT', 'PROJ') + '-'
        start = int(match.group(2))
        end = int(match.group(3))
        return [f"{prefix}{i}" for i in range(start, end + 1)]
    return [range_str]


def main():
    parser = argparse.ArgumentParser(
        description='Add attachments to JIRA tickets',
        epilog='Examples:\n'
               '  # Add single file to ticket\n'
               '  %(prog)s --tickets PROJ-100 --file screenshot.png\n\n'
               '  # Add log to multiple tickets\n'
               '  %(prog)s --tickets PROJ-100:110 --file test.log\n\n'
               '  # Add multiple files\n'
               '  %(prog)s --tickets PROJ-100 --file log1.txt --file log2.txt',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--tickets', required=True, help='Ticket range or comma-separated list')
    parser.add_argument('--file', dest='files', action='append', required=True,
                        help='File to attach (can be specified multiple times)')

    args = parser.parse_args()

    # Get credentials
    creds = get_jira_credentials()
    if not all(creds.values()):
        print("❌ Error: Set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN environment variables")
        return

    # Validate files exist
    for file_path in args.files:
        if not os.path.exists(file_path):
            print(f"❌ Error: File not found: {file_path}")
            return

    # Parse tickets
    if ':' in args.tickets:
        tickets = parse_ticket_range(args.tickets)
    else:
        tickets = args.tickets.split(',')

    print(f"Adding {len(args.files)} file(s) to {len(tickets)} tickets...")
    print()

    success_count = 0
    failed_tickets = []

    for i, ticket_key in enumerate(tickets, 1):
        print(f"[{i}/{len(tickets)}] {ticket_key}:")

        ticket_success = True
        for file_path in args.files:
            filename = os.path.basename(file_path)
            print(f"  Attaching {filename}...", end=" ", flush=True)

            success, error = add_attachment(ticket_key, file_path, creds)

            if success:
                print("✅")
            else:
                print(f"❌ {error}")
                ticket_success = False

        if ticket_success:
            success_count += 1
        else:
            failed_tickets.append(ticket_key)

    # Summary
    print()
    print("=" * 80)
    print(f"Successfully updated: {success_count}/{len(tickets)}")
    if failed_tickets:
        print(f"Failed: {', '.join(failed_tickets)}")
    print("=" * 80)


if __name__ == '__main__':
    main()
