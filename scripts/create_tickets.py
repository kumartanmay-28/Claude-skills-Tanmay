#!/usr/bin/env python3
"""
Generic JIRA ticket creation from test log analysis
Works for any project, any ticket type, any labels
"""

import os
import re
import json
import argparse
import requests
from requests.auth import HTTPBasicAuth
from collections import defaultdict


def get_env_or_fail(var_name):
    """Get environment variable or exit"""
    value = os.getenv(var_name)
    if not value:
        print(f"❌ Error: Environment variable {var_name} not set")
        print(f"   Set it with: export {var_name}=<value>")
        exit(1)
    return value


def extract_detailed_failures(log_file, file_path, test_classes, max_per_class=10):
    """Extract detailed error messages from FAILED lines"""
    class_failures = defaultdict(list)

    with open(log_file, 'r', errors='ignore') as f:
        for line in f:
            match = re.match(r'FAILED\s+\[[\d\.]+s\]\s+(\S+?)::(\w+)::(\w+)(?:\s+-\s+(.+))?$', line)
            if match:
                fail_path = match.group(1)
                fail_class = match.group(2)
                fail_method = match.group(3)
                error_msg = match.group(4) if match.group(4) else "No error message captured"

                normalized_path = fail_path.replace('test/', '')

                if normalized_path == file_path and fail_class in test_classes:
                    key = f"{file_path}::{fail_class}"
                    if len(class_failures[key]) < max_per_class:
                        class_failures[key].append({
                            'method': fail_method,
                            'error': error_msg,
                            'full_path': f"{fail_path}::{fail_class}::{fail_method}"
                        })

    return dict(class_failures)


def build_ticket_description(file_path, test_classes, class_failures, build_info, platform, test_command):
    """Build generic ADF description"""

    total_failures = sum(len(failures) for failures in class_failures.values())

    content = [
        {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "Test Failure Report", "marks": [{"type": "strong"}]}
            ]
        },
        {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": f"This ticket tracks {total_failures} failure(s) across {len(test_classes)} test class(es)."}
            ]
        },
        {
            "type": "rule"
        },
        {
            "type": "heading",
            "attrs": {"level": 3},
            "content": [{"type": "text", "text": "Test Information"}]
        },
        {
            "type": "bulletList",
            "content": [
                {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Platform: ", "marks": [{"type": "strong"}]}, {"type": "text", "text": platform}]}]},
                {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Build: ", "marks": [{"type": "strong"}]}, {"type": "text", "text": build_info.get("build", "N/A")}]}]},
                {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Test File: ", "marks": [{"type": "strong"}]}, {"type": "text", "text": file_path, "marks": [{"type": "code"}]}]}]},
            ]
        },
        {
            "type": "rule"
        },
        {
            "type": "heading",
            "attrs": {"level": 3},
            "content": [{"type": "text", "text": f"Failure Details ({total_failures} failures)"}]
        }
    ]

    # Add failures by class
    for test_class in sorted(test_classes):
        key = f"{file_path}::{test_class}"
        failures = class_failures.get(key, [])

        if failures:
            content.append({
                "type": "heading",
                "attrs": {"level": 4},
                "content": [{"type": "text", "text": f"{test_class} ({len(failures)} failures)"}]
            })

            for f in sorted(failures, key=lambda x: x['method'])[:10]:
                content.extend([
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": "Test: ", "marks": [{"type": "strong"}]},
                            {"type": "text", "text": f['method'], "marks": [{"type": "code"}]}
                        ]
                    },
                    {
                        "type": "codeBlock",
                        "attrs": {"language": "text"},
                        "content": [{"type": "text", "text": f['error'][:250]}]
                    }
                ])

    # Add reproduction
    if test_command:
        content.extend([
            {
                "type": "rule"
            },
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "Reproduction:", "marks": [{"type": "strong"}]}]
            },
            {
                "type": "codeBlock",
                "attrs": {"language": "bash"},
                "content": [{"type": "text", "text": test_command.format(test_file=file_path.replace('.py', ''))}]
            }
        ])

    return {"version": 1, "type": "doc", "content": content}


def create_ticket(summary, description, jira_config, labels=None, sprint=None, story_points=None):
    """Create JIRA ticket with provided configuration"""

    url = f"{jira_config['url']}/rest/api/3/issue"
    auth = HTTPBasicAuth(jira_config['email'], jira_config['token'])
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "fields": {
            "project": {"key": jira_config['project']},
            "summary": summary,
            "description": description,
            "issuetype": {"name": jira_config.get('issuetype', 'Bug')},
            "priority": {"name": jira_config.get('priority', 'Normal')},
        }
    }

    # Optional fields
    if labels:
        payload["fields"]["labels"] = labels

    if jira_config.get('component'):
        payload["fields"]["components"] = [{"name": jira_config['component']}]

    if story_points and jira_config.get('story_points_field'):
        payload["fields"][jira_config['story_points_field']] = story_points

    if sprint and jira_config.get('sprint_field'):
        payload["fields"][jira_config['sprint_field']] = sprint

    response = requests.post(url, json=payload, headers=headers, auth=auth)

    if response.status_code in [200, 201]:
        data = response.json()
        return True, data.get("key"), None
    else:
        return False, None, f"Error {response.status_code}: {response.text[:200]}"


def main():
    parser = argparse.ArgumentParser(description='Generic JIRA ticket creation from test logs')
    parser.add_argument('--log-file', required=True, help='Path to test log file')
    parser.add_argument('--config', required=True, help='Analysis config JSON from analyze_logs.py')
    parser.add_argument('--platform', required=True, help='Test platform name')
    parser.add_argument('--project', help='JIRA project key (default: from JIRA_PROJECT env)')
    parser.add_argument('--labels', help='Comma-separated labels')
    parser.add_argument('--sprint', type=int, help='Sprint ID')
    parser.add_argument('--story-points', type=float, help='Story points')
    parser.add_argument('--test-command', help='Reproduction command template (use {test_file})')
    parser.add_argument('--build-info', help='JSON with build metadata {"build": "...", "commit": "...", "date": "..."}')

    args = parser.parse_args()

    # Get JIRA config from environment
    jira_config = {
        'url': get_env_or_fail('JIRA_URL'),
        'email': get_env_or_fail('JIRA_EMAIL'),
        'token': get_env_or_fail('JIRA_API_TOKEN'),
        'project': args.project or get_env_or_fail('JIRA_PROJECT'),
        'issuetype': os.getenv('JIRA_ISSUETYPE', 'Bug'),
        'priority': os.getenv('JIRA_PRIORITY', 'Normal'),
        'component': os.getenv('JIRA_COMPONENT'),
        'story_points_field': os.getenv('JIRA_STORY_POINTS_FIELD', 'customfield_10028'),
        'sprint_field': os.getenv('JIRA_SPRINT_FIELD', 'customfield_10020')
    }

    # Load analysis config
    with open(args.config, 'r') as f:
        analysis = json.load(f)

    # Parse optional fields
    labels = args.labels.split(',') if args.labels else []
    build_info = json.loads(args.build_info) if args.build_info else {}

    print(f"Creating {len(analysis['tickets'])} tickets...")
    print()

    created_tickets = []
    failed_tickets = []

    for i, ticket_info in enumerate(analysis['tickets'], 1):
        file_path = ticket_info['file_path']
        test_classes = ticket_info['test_classes']

        print(f"[{i}/{len(analysis['tickets'])}] {file_path}...")

        # Extract detailed failures
        class_failures = extract_detailed_failures(args.log_file, file_path, test_classes)

        # Build summary
        classes_str = ', '.join(test_classes[:3])
        if len(test_classes) > 3:
            classes_str += f" + {len(test_classes) - 3} more"

        summary = f"[{args.platform}] {os.path.basename(file_path)} - {classes_str} failure(s)"
        if len(summary) > 255:
            summary = f"[{args.platform}] {os.path.basename(file_path)} - {len(test_classes)} test class(es) failure(s)"

        # Build description
        description = build_ticket_description(
            file_path, test_classes, class_failures,
            build_info, args.platform, args.test_command
        )

        # Create ticket
        success, ticket_key, error = create_ticket(
            summary, description, jira_config,
            labels, args.sprint, args.story_points
        )

        if success:
            print(f"  ✅ {ticket_key}")
            created_tickets.append(ticket_key)
        else:
            print(f"  ❌ {error}")
            failed_tickets.append((file_path, error))

    # Summary
    print()
    print("=" * 80)
    print(f"Successfully created: {len(created_tickets)}/{len(analysis['tickets'])}")
    if failed_tickets:
        print(f"Failed: {len(failed_tickets)}")
    print("=" * 80)


if __name__ == '__main__':
    main()
