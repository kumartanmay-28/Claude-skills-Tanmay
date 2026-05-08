#!/usr/bin/env python3
"""
Close/resolve JIRA tickets with proper resolution
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


def get_available_transitions(ticket_key, creds):
    """Get available transitions for a ticket"""
    url = f"{creds['url']}/rest/api/3/issue/{ticket_key}/transitions"
    auth = HTTPBasicAuth(creds['email'], creds['token'])
    headers = {"Accept": "application/json"}

    response = requests.get(url, headers=headers, auth=auth)

    if response.status_code == 200:
        return response.json()['transitions']
    return []


def close_ticket(ticket_key, resolution, comment, creds):
    """Close a ticket with resolution"""
    # Get available transitions
    transitions = get_available_transitions(ticket_key, creds)

    # Find "Done" or "Close" transition
    transition_id = None
    for trans in transitions:
        if trans['name'].lower() in ['done', 'close', 'closed', 'resolve', 'resolved']:
            transition_id = trans['id']
            break

    if not transition_id:
        return False, "No 'Done' or 'Close' transition available"

    # Perform transition with resolution
    url = f"{creds['url']}/rest/api/3/issue/{ticket_key}/transitions"
    auth = HTTPBasicAuth(creds['email'], creds['token'])
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "transition": {"id": transition_id},
        "fields": {
            "resolution": {"name": resolution}
        }
    }

    # Add comment if provided
    if comment:
        payload["update"] = {
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

    response = requests.post(url, json=payload, headers=headers, auth=auth)

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
        description='Close/resolve JIRA tickets',
        epilog='Examples:\n'
               '  # Close as Done\n'
               '  %(prog)s --tickets PROJ-100 --resolution Done\n\n'
               '  # Close as Fixed with comment\n'
               '  %(prog)s --tickets PROJ-100:110 --resolution Fixed --comment "Fixed in v2.0"\n\n'
               '  # Close as Won\'t Do\n'
               '  %(prog)s --tickets PROJ-111 --resolution "Won\'t Do" --comment "Not applicable"\n\n'
               'Common resolutions:\n'
               '  - Done\n'
               '  - Fixed\n'
               '  - Won\'t Do\n'
               '  - Duplicate\n'
               '  - Cannot Reproduce',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--tickets', required=True, help='Ticket range or comma-separated list')
    parser.add_argument('--resolution', required=True, help='Resolution (Done, Fixed, Won\'t Do, etc.)')
    parser.add_argument('--comment', help='Optional comment to add when closing')
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

    print(f"Closing {len(tickets)} tickets with resolution: {args.resolution}...")
    print()

    success_count = 0
    failed_tickets = []

    for i, ticket_key in enumerate(tickets, 1):
        print(f"[{i}/{len(tickets)}] {ticket_key}...", end=" ", flush=True)

        success, error = close_ticket(ticket_key, args.resolution, args.comment, creds)

        if success:
            print("✅")
            success_count += 1
        else:
            print(f"❌ {error}")
            failed_tickets.append((ticket_key, error))

    # Summary
    print()
    print("=" * 80)
    print(f"Successfully closed: {success_count}/{len(tickets)}")
    if failed_tickets:
        print("\nFailed:")
        for ticket, error in failed_tickets:
            print(f"  {ticket}: {error}")
    print("=" * 80)


if __name__ == '__main__':
    main()
