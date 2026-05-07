#!/usr/bin/env python3
"""
Generic bulk update script for JIRA tickets
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


def parse_ticket_range(range_str):
    """Parse ticket range like PROJ-100:150 into list"""
    match = re.match(r'([A-Z]+-)?(\d+):(\d+)', range_str)
    if match:
        prefix = match.group(1) or os.getenv('JIRA_PROJECT', 'PROJ') + '-'
        start = int(match.group(2))
        end = int(match.group(3))
        return [f"{prefix}{i}" for i in range(start, end + 1)]
    return [range_str]


def update_ticket(ticket_key, updates, creds):
    """Update a single ticket"""
    url = f"{creds['url']}/rest/api/3/issue/{ticket_key}"
    auth = HTTPBasicAuth(creds['email'], creds['token'])
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {"fields": updates}

    response = requests.put(url, json=payload, headers=headers, auth=auth)
    return response.status_code in [200, 204]


def main():
    parser = argparse.ArgumentParser(description='Bulk update JIRA tickets')
    parser.add_argument('--tickets', help='Ticket range (e.g., PROJ-100:150) or comma-separated list')
    parser.add_argument('--jql', help='JQL query to select tickets')
    parser.add_argument('--sprint', type=int, help='Sprint ID to assign')
    parser.add_argument('--story-points', type=float, help='Story points to add')
    parser.add_argument('--labels', help='Labels to add (comma-separated)')
    parser.add_argument('--sprint-field', default='customfield_10020', help='Sprint custom field ID')
    parser.add_argument('--points-field', default='customfield_10028', help='Story points custom field ID')

    args = parser.parse_args()

    # Get credentials
    creds = get_jira_credentials()
    if not all(creds.values()):
        print("❌ Error: Set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN environment variables")
        return

    # Get ticket list
    tickets = []
    if args.tickets:
        if ':' in args.tickets:
            tickets = parse_ticket_range(args.tickets)
        else:
            tickets = args.tickets.split(',')
    elif args.jql:
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
        print("❌ Error: Provide --tickets or --jql")
        return

    print(f"Updating {len(tickets)} tickets...")
    print()

    # Build updates
    updates = {}
    if args.sprint:
        updates[args.sprint_field] = args.sprint
    if args.story_points:
        updates[args.points_field] = args.story_points
    if args.labels:
        updates['labels'] = args.labels.split(',')

    if not updates:
        print("❌ Error: Provide at least one update (--sprint, --story-points, --labels)")
        return

    # Update tickets
    success_count = 0
    failed_tickets = []

    for i, ticket_key in enumerate(tickets, 1):
        print(f"[{i}/{len(tickets)}] {ticket_key}...", end=" ", flush=True)

        if update_ticket(ticket_key, updates, creds):
            print("✅")
            success_count += 1
        else:
            print("❌")
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
