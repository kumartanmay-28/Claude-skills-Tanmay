#!/usr/bin/env python3
"""
Assign JIRA tickets to users
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


def assign_ticket(ticket_key, assignee, creds):
    """Assign a ticket to a user"""
    url = f"{creds['url']}/rest/api/3/issue/{ticket_key}/assignee"
    auth = HTTPBasicAuth(creds['email'], creds['token'])
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Use accountId or email depending on what's provided
    payload = {}
    if assignee.lower() == 'unassigned':
        payload = {"accountId": None}
    elif '@' in assignee:
        # For email, we need to look up accountId first
        # For simplicity, assume it's accountId if no @
        payload = {"accountId": assignee}
    else:
        payload = {"accountId": assignee}

    response = requests.put(url, json=payload, headers=headers, auth=auth)

    if response.status_code in [200, 204]:
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
        description='Assign JIRA tickets to users',
        epilog='Examples:\n'
               '  # Assign to user by account ID\n'
               '  %(prog)s --tickets PROJ-100 --assignee 5d123abc456def789\n\n'
               '  # Assign range to user\n'
               '  %(prog)s --tickets PROJ-100:110 --assignee 5d123abc456def789\n\n'
               '  # Unassign tickets\n'
               '  %(prog)s --tickets PROJ-100:110 --assignee unassigned',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--tickets', required=True, help='Ticket range or comma-separated list')
    parser.add_argument('--assignee', required=True, help='User account ID (or "unassigned")')
    parser.add_argument('--jql', help='JQL query to select tickets')

    args = parser.parse_args()

    # Get credentials
    creds = get_jira_credentials()
    if not all(creds.values()):
        print("❌ Error: Set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN environment variables")
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

    assignee_display = "Unassigned" if args.assignee.lower() == 'unassigned' else args.assignee
    print(f"Assigning {len(tickets)} tickets to {assignee_display}...")
    print()

    success_count = 0
    failed_tickets = []

    for i, ticket_key in enumerate(tickets, 1):
        print(f"[{i}/{len(tickets)}] {ticket_key}...", end=" ", flush=True)

        success, error = assign_ticket(ticket_key, args.assignee, creds)

        if success:
            print("✅")
            success_count += 1
        else:
            print(f"❌ {error}")
            failed_tickets.append((ticket_key, error))

    # Summary
    print()
    print("=" * 80)
    print(f"Successfully assigned: {success_count}/{len(tickets)}")
    if failed_tickets:
        print("\nFailed:")
        for ticket, error in failed_tickets:
            print(f"  {ticket}: {error}")
    print("=" * 80)


if __name__ == '__main__':
    main()
