#!/usr/bin/env python3
"""
Transition JIRA tickets through workflow states
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


def transition_ticket(ticket_key, transition_name_or_id, comment, creds):
    """Transition a ticket to a new state"""
    # First, get available transitions
    transitions = get_available_transitions(ticket_key, creds)

    # Find matching transition
    transition_id = None
    for trans in transitions:
        if (trans['name'].lower() == transition_name_or_id.lower() or
            trans['id'] == str(transition_name_or_id)):
            transition_id = trans['id']
            break

    if not transition_id:
        return False, f"Transition '{transition_name_or_id}' not available"

    # Perform transition
    url = f"{creds['url']}/rest/api/3/issue/{ticket_key}/transitions"
    auth = HTTPBasicAuth(creds['email'], creds['token'])
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "transition": {"id": transition_id}
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
        description='Transition JIRA tickets through workflow',
        epilog='Examples:\n'
               '  # Move to In Progress\n'
               '  %(prog)s --tickets PROJ-100 --to "In Progress"\n\n'
               '  # Move range to Done with comment\n'
               '  %(prog)s --tickets PROJ-100:110 --to Done --comment "Fixed in v2.0"\n\n'
               '  # Show available transitions\n'
               '  %(prog)s --tickets PROJ-100 --show-transitions',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--tickets', required=True, help='Ticket range or comma-separated list')
    parser.add_argument('--to', help='Target transition name or ID')
    parser.add_argument('--comment', help='Optional comment to add during transition')
    parser.add_argument('--show-transitions', action='store_true', help='Show available transitions')

    args = parser.parse_args()

    # Get credentials
    creds = get_jira_credentials()
    if not all(creds.values()):
        print("❌ Error: Set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN environment variables")
        return

    # Parse tickets
    if ':' in args.tickets:
        tickets = parse_ticket_range(args.tickets)
    else:
        tickets = args.tickets.split(',')

    # Show transitions mode
    if args.show_transitions:
        print("=" * 80)
        print("AVAILABLE TRANSITIONS")
        print("=" * 80)
        print()

        for ticket_key in tickets:
            transitions = get_available_transitions(ticket_key, creds)
            print(f"{ticket_key}:")
            if transitions:
                for trans in transitions:
                    print(f"  - {trans['name']} (ID: {trans['id']})")
            else:
                print("  No transitions available")
            print()
        return

    # Validate --to is provided
    if not args.to:
        print("❌ Error: Provide --to with target transition name or --show-transitions")
        return

    print(f"Transitioning {len(tickets)} tickets to '{args.to}'...")
    print()

    success_count = 0
    failed_tickets = []

    for i, ticket_key in enumerate(tickets, 1):
        print(f"[{i}/{len(tickets)}] {ticket_key}...", end=" ", flush=True)

        success, error = transition_ticket(ticket_key, args.to, args.comment, creds)

        if success:
            print("✅")
            success_count += 1
        else:
            print(f"❌ {error}")
            failed_tickets.append((ticket_key, error))

    # Summary
    print()
    print("=" * 80)
    print(f"Successfully transitioned: {success_count}/{len(tickets)}")
    if failed_tickets:
        print("\nFailed:")
        for ticket, error in failed_tickets:
            print(f"  {ticket}: {error}")
    print("=" * 80)


if __name__ == '__main__':
    main()
