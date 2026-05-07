#!/usr/bin/env python3
"""
Generic regression ticket reopening script
Reopens closed tickets that are still failing with recurrence information
"""

import os
import re
import json
import argparse
import requests
from requests.auth import HTTPBasicAuth


def get_env_or_fail(var_name):
    """Get environment variable or exit"""
    value = os.getenv(var_name)
    if not value:
        print(f"❌ Error: Environment variable {var_name} not set")
        exit(1)
    return value


def get_available_transitions(ticket_key, jira_config):
    """Get available transitions for a ticket"""
    url = f"{jira_config['url']}/rest/api/3/issue/{ticket_key}/transitions"
    auth = HTTPBasicAuth(jira_config['email'], jira_config['token'])
    headers = {"Accept": "application/json"}

    response = requests.get(url, headers=headers, auth=auth)
    if response.status_code == 200:
        return response.json().get("transitions", [])
    return []


def reopen_ticket(ticket_key, jira_config):
    """Reopen a closed ticket"""
    transitions = get_available_transitions(ticket_key, jira_config)

    # Look for reopen transition
    reopen_transition = None
    for t in transitions:
        name = t.get("name", "").lower()
        if "reopen" in name or "refinement" in name or "open" in name:
            reopen_transition = t
            break

    if not reopen_transition and transitions:
        reopen_transition = transitions[0]

    if not reopen_transition:
        return False, "No transitions available"

    # Perform transition
    url = f"{jira_config['url']}/rest/api/3/issue/{ticket_key}/transitions"
    auth = HTTPBasicAuth(jira_config['email'], jira_config['token'])
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {"transition": {"id": reopen_transition["id"]}}
    response = requests.post(url, json=payload, headers=headers, auth=auth)

    if response.status_code in [200, 204]:
        return True, reopen_transition.get("name")
    else:
        return False, f"Error {response.status_code}"


def add_recurrence_comment(ticket_key, build_info, jira_config):
    """Add comment about recurrence"""
    url = f"{jira_config['url']}/rest/api/3/issue/{ticket_key}/comment"
    auth = HTTPBasicAuth(jira_config['email'], jira_config['token'])
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    content = [
        {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "Failure Recurrence", "marks": [{"type": "strong"}]}
            ]
        },
        {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "This issue has "},
                {"type": "text", "text": "recurred", "marks": [{"type": "strong"}]},
                {"type": "text", "text": f" in {build_info.get('build', 'latest build')}."}
            ]
        }
    ]

    # Add build info if provided
    if build_info:
        bullet_items = []
        if build_info.get('build'):
            bullet_items.append({
                "type": "listItem",
                "content": [{
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Build: ", "marks": [{"type": "strong"}]},
                        {"type": "text", "text": build_info['build']}
                    ]
                }]
            })
        if build_info.get('commit'):
            bullet_items.append({
                "type": "listItem",
                "content": [{
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Commit: ", "marks": [{"type": "strong"}]},
                        {"type": "text", "text": build_info['commit']}
                    ]
                }]
            })
        if build_info.get('date'):
            bullet_items.append({
                "type": "listItem",
                "content": [{
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Test Date: ", "marks": [{"type": "strong"}]},
                        {"type": "text", "text": build_info['date']}
                    ]
                }]
            })

        if bullet_items:
            content.append({
                "type": "bulletList",
                "content": bullet_items
            })

    comment = {
        "body": {
            "version": 1,
            "type": "doc",
            "content": content
        }
    }

    response = requests.post(url, json=comment, headers=headers, auth=auth)
    return response.status_code in [200, 201]


def main():
    parser = argparse.ArgumentParser(description='Reopen regression tickets')
    parser.add_argument('--tickets', required=True, help='Comma-separated ticket keys or JSON file with ticket list')
    parser.add_argument('--build', help='Build identifier')
    parser.add_argument('--commit', help='Commit hash')
    parser.add_argument('--date', help='Test date')

    args = parser.parse_args()

    # Get JIRA config
    jira_config = {
        'url': get_env_or_fail('JIRA_URL'),
        'email': get_env_or_fail('JIRA_EMAIL'),
        'token': get_env_or_fail('JIRA_API_TOKEN')
    }

    # Parse tickets
    if args.tickets.endswith('.json'):
        with open(args.tickets, 'r') as f:
            data = json.load(f)
            tickets = data if isinstance(data, list) else data.get('tickets', [])
    else:
        tickets = args.tickets.split(',')

    # Build info
    build_info = {}
    if args.build:
        build_info['build'] = args.build
    if args.commit:
        build_info['commit'] = args.commit
    if args.date:
        build_info['date'] = args.date

    print(f"Reopening {len(tickets)} tickets...")
    print()

    success_count = 0
    for i, ticket_key in enumerate(tickets, 1):
        print(f"[{i}/{len(tickets)}] {ticket_key}...", end=" ", flush=True)

        # Reopen
        success, result = reopen_ticket(ticket_key, jira_config)
        if success:
            print(f"✅ Reopened")
        else:
            print(f"⚠️  {result}")

        # Add comment
        if add_recurrence_comment(ticket_key, build_info, jira_config):
            success_count += 1
        else:
            print(f"  ⚠️  Failed to add comment")

    print()
    print("=" * 80)
    print(f"Successfully updated: {success_count}/{len(tickets)}")
    print("=" * 80)


if __name__ == '__main__':
    main()
