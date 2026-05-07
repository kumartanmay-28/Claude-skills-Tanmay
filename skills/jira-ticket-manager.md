# JIRA Ticket Manager Skill

## Metadata

```yaml
name: jira-ticket-manager
description: Automates JIRA ticket operations including bulk creation, updates, analysis, and linking. Handles test failure tickets, sprint management, and regression detection with detailed error extraction.
allowed-tools: Bash, Read, Write, Grep, WebFetch
version: 1.0.0
```

## Overview

This skill automates common JIRA ticket management workflows, particularly for test failure tracking and bulk ticket operations.

## Commands

### 1. Analyze Logs

Extract failures from test logs and determine ticket structure.

```bash
# Analyze test log
python scripts/analyze_logs.py --log-file /path/to/test.log --platform sGPU

# Output: analysis.json with ticket recommendations
```

**Output Structure:**
```json
{
  "total_failures": 120,
  "unique_files": 37,
  "recommended_tickets": 34,
  "clubbing_strategy": "by_file",
  "platforms": ["sGPU"],
  "tickets": [
    {
      "file": "test_ops.py",
      "classes": ["TestCommon", "TestMath"],
      "failure_count": 15
    }
  ]
}
```

### 2. Create Tickets

Create JIRA tickets with detailed descriptions.

```bash
# Create tickets from analysis
python scripts/create_tickets.py \
  --config analysis.json \
  --sprint "Sprint 32" \
  --story-points 3 \
  --labels pytorch_hermetic,test_failure
```

**Features:**
- Detailed error messages from logs
- Reproduction commands
- Build metadata
- Auto-assigns sprint and story points

### 3. Bulk Update

Update multiple tickets at once.

```bash
# Update sprint for ticket range
python scripts/bulk_update.py \
  --tickets AIPCC-15363:15565 \
  --sprint 32 \
  --story-points 3

# Update with JQL
python scripts/bulk_update.py \
  --jql "labels = pytorch_hermetic AND sprint is EMPTY" \
  --sprint 32
```

### 4. Link Tickets

Link tickets to parent issues.

```bash
# Link all tickets to parent
python scripts/link_tickets.py \
  --tickets AIPCC-15363:15565 \
  --parent AIPCC-14613 \
  --link-type "relates to"
```

### 5. Verify Coverage

Check if all failures have tickets.

```bash
# Verify ticket coverage
python scripts/verify_coverage.py \
  --log-file test.log \
  --tickets tickets.json

# Output: Coverage report
```

### 6. Detect Regressions

Find closed tickets still failing.

```bash
# Check for regressions
python scripts/detect_regressions.py \
  --log-file new_test.log \
  --existing-tickets hermetic_tickets.json

# Output: List of regression tickets to reopen
```

### 7. Reopen Regressions

Reopen closed tickets with recurrence info.

```bash
# Reopen regression tickets
python scripts/reopen_regressions.py \
  --tickets regression_list.json \
  --build "Builder 2.12-RC5" \
  --commit "46210d4"
```

## Configuration

Set environment variables:

```bash
export JIRA_URL="https://your-instance.atlassian.net"
export JIRA_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

Or use config file:

```json
{
  "jira": {
    "url": "https://your-instance.atlassian.net",
    "email": "your@example.com",
    "api_token": "token",
    "project": "PROJ"
  },
  "defaults": {
    "labels": ["automated"],
    "priority": "Normal",
    "issuetype": "Bug",
    "story_points_field": "customfield_10028",
    "sprint_field": "customfield_10020"
  }
}
```

## Usage Patterns

### Complete Workflow: New Test Run

```bash
# 1. Analyze logs
python scripts/analyze_logs.py --log-file tests.log --platform sGPU

# 2. Create tickets
python scripts/create_tickets.py --config analysis.json --sprint 32

# 3. Verify coverage
python scripts/verify_coverage.py --log-file tests.log --tickets created.json
```

### Bulk Sprint Assignment

```bash
# Update all hermetic tickets to Sprint 32
python scripts/bulk_update.py \
  --jql "labels = pytorch_hermetic AND sprint is EMPTY" \
  --sprint 32 \
  --story-points 3
```

### Regression Handling

```bash
# 1. Detect regressions
python scripts/detect_regressions.py \
  --log-file new_run.log \
  --existing-tickets all_tickets.json

# 2. Reopen with details
python scripts/reopen_regressions.py \
  --tickets regressions.json \
  --build "Builder 2.12-RC5"
```

## Error Handling

The skill provides clear error messages and confidence levels:

- **High Confidence**: Exact match found in logs
- **Medium Confidence**: Partial match or inferred
- **Low Confidence**: Manual verification needed

## Best Practices

1. **Always verify coverage** after creating tickets
2. **Use clubbing** to reduce ticket count (by file/directory)
3. **Include reproduction commands** in ticket descriptions
4. **Add build metadata** (commit, date, platform)
5. **Link to parent issues** for tracking
6. **Check for regressions** before creating duplicates

## Examples

See [examples/](../examples/) for complete workflows:

- PyTorch hermetic build testing (61 tickets)
- Sprint bulk update (34 tickets)
- Regression reopening (11 tickets)
- Coverage verification

## Output Format

All commands output structured JSON:

```json
{
  "success": true,
  "tickets_created": 27,
  "tickets_updated": 34,
  "failed": 0,
  "ticket_keys": ["AIPCC-15363", "..."],
  "errors": []
}
```

## Limitations

- Requires JIRA REST API v3
- Sprint field ID may vary by instance
- ADF (Atlassian Document Format) required for descriptions
- Rate limiting: ~100 requests/minute

## Support

For issues or questions, see [docs/troubleshooting.md](../docs/troubleshooting.md)
