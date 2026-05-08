#!/usr/bin/env python3
"""
Manage watchers on JIRA tickets
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


def add_watcher(ticket_key, account_id, creds):
    """Add a watcher to a ticket"""
    url = f"{creds['url']}/rest/api/3/issue/{ticket_key}/watchers"
    auth = HTTPBasicAuth(creds['email'], creds['token'])
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Body is just the accountId as a string
    response = requests.post(url, json=account_id, headers=headers, auth=auth)

    if response.status_code in [200, 204]:
        return True, None
    else:
        return False, f"Error {response.status_code}: {response.text[:200]}"


def remove_watcher(ticket_key, account_id, creds):
    """Remove a watcher from a ticket"""
    url = f"{creds['url']}/rest/api/3/issue/{ticket_key}/watchers"
    auth = HTTPBasicAuth(creds['email'], creds['token'])
    headers = {"Accept": "application/json"}

    params = {"accountId": account_id}

    response = requests.delete(url, params=params, headers=headers, auth=auth)

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
        description='Manage watchers on JIRA tickets',
        epilog='Examples:\n'
               '  # Add watcher\n'
               '  %(prog)s --tickets PROJ-100 --add 5d123abc456def789\n\n'
               '  # Add watcher to range\n'
               '  %(prog)s --tickets PROJ-100:110 --add 5d123abc456def789\n\n'
               '  # Remove watcher\n'
               '  %(prog)s --tickets PROJ-100 --remove 5d123abc456def789',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--tickets', required=True, help='Ticket range or comma-separated list')
    parser.add_argument('--add', dest='add_watcher', help='Add watcher by account ID')
    parser.add_argument('--remove', dest='remove_watcher', help='Remove watcher by account ID')

    args = parser.parse_args()

    # Get credentials
    creds = get_jira_credentials()
    if not all(creds.values()):
        print("❌ Error: Set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN environment variables")
        return

    # Validate action
    if not args.add_watcher and not args.remove_watcher:
        print("❌ Error: Provide --add or --remove")
        return

    if args.add_watcher and args.remove_watcher:
        print("❌ Error: Cannot add and remove in same operation")
        return

    # Parse tickets
    if ':' in args.tickets:
        tickets = parse_ticket_range(args.tickets)
    else:
        tickets = args.tickets.split(',')

    action = "Adding" if args.add_watcher else "Removing"
    account_id = args.add_watcher or args.remove_watcher

    print(f"{action} watcher {account_id} on {len(tickets)} tickets...")
    print()

    success_count = 0
    failed_tickets = []

    for i, ticket_key in enumerate(tickets, 1):
        print(f"[{i}/{len(tickets)}] {ticket_key}...", end=" ", flush=True)

        if args.add_watcher:
            success, error = add_watcher(ticket_key, account_id, creds)
        else:
            success, error = remove_watcher(ticket_key, account_id, creds)

        if success:
            print("✅")
            success_count += 1
        else:
            print(f"❌ {error}")
            failed_tickets.append((ticket_key, error))

    # Summary
    print()
    print("=" * 80)
    print(f"Successfully updated: {success_count}/{len(tickets)}")
    if failed_tickets:
        print("\nFailed:")
        for ticket, error in failed_tickets:
            print(f"  {ticket}: {error}")
    print("=" * 80)


if __name__ == '__main__':
    main()
