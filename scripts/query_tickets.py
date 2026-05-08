#!/usr/bin/env python3
"""
Query JIRA tickets using JQL with detailed output
"""

import os
import json
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


def query_jira(jql, fields, max_results, creds):
    """Query JIRA with JQL"""
    url = f"{creds['url']}/rest/api/3/search"
    auth = HTTPBasicAuth(creds['email'], creds['token'])
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "jql": jql,
        "maxResults": max_results,
        "fields": fields
    }

    response = requests.post(url, json=payload, headers=headers, auth=auth)

    if response.status_code == 200:
        return True, response.json()
    else:
        return False, f"Error {response.status_code}: {response.text[:200]}"


def display_results(results, output_format):
    """Display query results"""
    issues = results.get('issues', [])
    total = results.get('total', 0)

    if output_format == 'json':
        print(json.dumps(results, indent=2))
        return

    if output_format == 'keys':
        for issue in issues:
            print(issue['key'])
        return

    # Table format
    print("=" * 120)
    print(f"QUERY RESULTS ({len(issues)} of {total} total)")
    print("=" * 120)
    print()

    for issue in issues:
        key = issue['key']
        fields = issue.get('fields', {})

        summary = fields.get('summary', 'N/A')
        status = fields.get('status', {}).get('name', 'N/A')
        assignee = fields.get('assignee', {})
        assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
        priority = fields.get('priority', {}).get('name', 'N/A')
        labels = fields.get('labels', [])

        print(f"[{key}] {summary}")
        print(f"  Status: {status} | Priority: {priority} | Assignee: {assignee_name}")
        if labels:
            print(f"  Labels: {', '.join(labels)}")
        print()

    print("=" * 120)
    print(f"Showing {len(issues)} of {total} total results")
    print("=" * 120)


def main():
    parser = argparse.ArgumentParser(
        description='Query JIRA tickets using JQL',
        epilog='Examples:\n'
               '  # Basic query\n'
               '  %(prog)s --jql "project = PROJ AND status = Open"\n\n'
               '  # Query with specific fields\n'
               '  %(prog)s --jql "labels = bug" --fields summary,status,assignee\n\n'
               '  # Export to JSON\n'
               '  %(prog)s --jql "sprint = 64581" --format json > results.json\n\n'
               '  # Just get ticket keys\n'
               '  %(prog)s --jql "status = Done" --format keys\n\n'
               'Common JQL queries:\n'
               '  - project = PROJ AND status = Open\n'
               '  - labels = test_failure AND sprint is EMPTY\n'
               '  - assignee = currentUser() AND status != Done\n'
               '  - created >= -7d\n'
               '  - updated >= -1d AND status changed to Done',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--jql', required=True, help='JQL query')
    parser.add_argument('--fields', default='summary,status,assignee,priority,labels',
                        help='Comma-separated field list (default: summary,status,assignee,priority,labels)')
    parser.add_argument('--max-results', type=int, default=100, help='Maximum results (default: 100)')
    parser.add_argument('--format', choices=['table', 'json', 'keys'], default='table',
                        help='Output format (default: table)')

    args = parser.parse_args()

    # Get credentials
    creds = get_jira_credentials()
    if not all(creds.values()):
        print("❌ Error: Set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN environment variables")
        return

    # Parse fields
    fields = args.fields.split(',') if args.fields != '*' else ['*all']

    # Query JIRA
    success, result = query_jira(args.jql, fields, args.max_results, creds)

    if not success:
        print(f"❌ Query failed: {result}")
        return

    # Display results
    display_results(result, args.format)


if __name__ == '__main__':
    main()
