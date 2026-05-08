#!/usr/bin/env python3
"""
Add comments to JIRA tickets
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


def add_comment(ticket_key, comment_text, creds):
    """Add a comment to a ticket"""
    url = f"{creds['url']}/rest/api/3/issue/{ticket_key}/comment"
    auth = HTTPBasicAuth(creds['email'], creds['token'])
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Build ADF comment
    payload = {
        "body": {
            "version": 1,
            "type": "doc",
            "content": [{
                "type": "paragraph",
                "content": [{"type": "text", "text": comment_text}]
            }]
        }
    }

    response = requests.post(url, json=payload, headers=headers, auth=auth)

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
        description='Add comments to JIRA tickets',
        epilog='Examples:\n'
               '  # Add comment to single ticket\n'
               '  %(prog)s --tickets PROJ-100 --comment "Fixed in v2.0"\n\n'
               '  # Add comment to range\n'
               '  %(prog)s --tickets PROJ-100:110 --comment "Verified on staging"\n\n'
               '  # Add comment from file\n'
               '  %(prog)s --tickets PROJ-100 --comment-file message.txt',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--tickets', required=True, help='Ticket range or comma-separated list')
    parser.add_argument('--comment', help='Comment text')
    parser.add_argument('--comment-file', help='Read comment from file')
    parser.add_argument('--jql', help='JQL query to select tickets')

    args = parser.parse_args()

    # Get credentials
    creds = get_jira_credentials()
    if not all(creds.values()):
        print("❌ Error: Set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN environment variables")
        return

    # Get comment text
    comment_text = args.comment
    if args.comment_file:
        with open(args.comment_file, 'r') as f:
            comment_text = f.read().strip()

    if not comment_text:
        print("❌ Error: Provide --comment or --comment-file")
        return

    # Get ticket list
    tickets = []
    if args.jql:
        # Query JIRA with JQL
        url = f"{creds['url']}/rest/api/3/search"
        auth = HTTPBasicAuth(creds['email'], creds['token'])
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        payload = {"jql": args.jql, "maxResults": 1000, "fields": ["key"]}
        response = requests.post(url, json=payload, headers=headers, auth=auth)
        if response.status_code == 200:
            tickets = [issue['key'] for issue in response.json()['issues']]
        else:
            print(f"❌ JQL query failed: {response.status_code}")
            return
    else:
        # Parse tickets
        if ':' in args.tickets:
            tickets = parse_ticket_range(args.tickets)
        else:
            tickets = args.tickets.split(',')

    print(f"Adding comment to {len(tickets)} tickets...")
    print()

    success_count = 0
    failed_tickets = []

    for i, ticket_key in enumerate(tickets, 1):
        print(f"[{i}/{len(tickets)}] {ticket_key}...", end=" ", flush=True)

        success, error = add_comment(ticket_key, comment_text, creds)

        if success:
            print("✅")
            success_count += 1
        else:
            print(f"❌ {error}")
            failed_tickets.append((ticket_key, error))

    # Summary
    print()
    print("=" * 80)
    print(f"Successfully added comments: {success_count}/{len(tickets)}")
    if failed_tickets:
        print("\nFailed:")
        for ticket, error in failed_tickets:
            print(f"  {ticket}: {error}")
    print("=" * 80)


if __name__ == '__main__':
    main()
