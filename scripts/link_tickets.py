#!/usr/bin/env python3
"""
Create links between JIRA tickets
"""

import os
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


def get_link_types(creds):
    """Get available link types"""
    url = f"{creds['url']}/rest/api/3/issueLinkType"
    auth = HTTPBasicAuth(creds['email'], creds['token'])
    headers = {"Accept": "application/json"}

    response = requests.get(url, headers=headers, auth=auth)

    if response.status_code == 200:
        return response.json()['issueLinkTypes']
    return []


def link_tickets(from_ticket, to_ticket, link_type, creds):
    """Create a link between two tickets"""
    url = f"{creds['url']}/rest/api/3/issueLink"
    auth = HTTPBasicAuth(creds['email'], creds['token'])
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "type": {"name": link_type},
        "inwardIssue": {"key": to_ticket},
        "outwardIssue": {"key": from_ticket}
    }

    response = requests.post(url, json=payload, headers=headers, auth=auth)

    if response.status_code in [200, 201]:
        return True, None
    else:
        return False, f"Error {response.status_code}: {response.text[:200]}"


def main():
    parser = argparse.ArgumentParser(
        description='Link JIRA tickets together',
        epilog='Examples:\n'
               '  # Create "blocks" relationship\n'
               '  %(prog)s --from PROJ-100 --to PROJ-101 --type Blocks\n\n'
               '  # Create "relates to" relationship\n'
               '  %(prog)s --from PROJ-100 --to PROJ-102 --type Relates\n\n'
               '  # Mark as duplicate\n'
               '  %(prog)s --from PROJ-103 --to PROJ-100 --type Duplicate\n\n'
               '  # Bulk link to parent\n'
               '  %(prog)s --from-file tickets.txt --to PROJ-100 --type Blocks\n\n'
               '  # Show available link types\n'
               '  %(prog)s --show-types',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--from', dest='from_ticket', help='Source ticket(s), comma-separated')
    parser.add_argument('--from-file', help='Read source tickets from file (one per line)')
    parser.add_argument('--to', dest='to_ticket', help='Target ticket')
    parser.add_argument('--type', help='Link type (e.g., Blocks, Relates, Duplicate, Clones)')
    parser.add_argument('--show-types', action='store_true', help='Show available link types')

    args = parser.parse_args()

    # Get credentials
    creds = get_jira_credentials()
    if not all(creds.values()):
        print("❌ Error: Set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN environment variables")
        return

    # Show link types mode
    if args.show_types:
        print("=" * 80)
        print("AVAILABLE LINK TYPES")
        print("=" * 80)
        print()

        link_types = get_link_types(creds)
        if link_types:
            for link in link_types:
                print(f"  {link['name']}")
                print(f"    Outward: {link['outward']}")
                print(f"    Inward: {link['inward']}")
                print()
        else:
            print("  No link types found")
        return

    # Validate required args
    if not args.to_ticket or not args.type:
        print("❌ Error: Provide --to and --type, or use --show-types")
        return

    if not args.from_ticket and not args.from_file:
        print("❌ Error: Provide --from or --from-file")
        return

    # Get from tickets
    from_tickets = []
    if args.from_file:
        with open(args.from_file, 'r') as f:
            from_tickets = [line.strip() for line in f if line.strip()]
    else:
        from_tickets = args.from_ticket.split(',')

    print(f"Linking {len(from_tickets)} tickets to {args.to_ticket} ({args.type})...")
    print()

    success_count = 0
    failed_tickets = []

    for i, from_key in enumerate(from_tickets, 1):
        print(f"[{i}/{len(from_tickets)}] {from_key} → {args.to_ticket}...", end=" ", flush=True)

        success, error = link_tickets(from_key, args.to_ticket, args.type, creds)

        if success:
            print("✅")
            success_count += 1
        else:
            print(f"❌ {error}")
            failed_tickets.append((from_key, error))

    # Summary
    print()
    print("=" * 80)
    print(f"Successfully linked: {success_count}/{len(from_tickets)}")
    if failed_tickets:
        print("\nFailed:")
        for ticket, error in failed_tickets:
            print(f"  {ticket}: {error}")
    print("=" * 80)


if __name__ == '__main__':
    main()
