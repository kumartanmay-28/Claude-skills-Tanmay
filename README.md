# JIRA Automation Toolkit

Completely generic scripts for automating JIRA ticket management. No hardcoding - everything configurable via environment variables and parameters.

## Scripts

### Test Failure Management (4 tools)

1. **`analyze_logs.py`** - Extract test failures from any log format
2. **`create_tickets.py`** - Create JIRA tickets (any project, any labels, any workflow)
3. **`bulk_update.py`** - Bulk update tickets (sprint, points, labels, any fields)
4. **`reopen_regressions.py`** - Reopen regression tickets with build info

### Full Lifecycle Management (8 tools)

5. **`transition_tickets.py`** - Move tickets through workflow states (Open → In Progress → Done)
6. **`add_comments.py`** - Add comments to tickets (bulk or individual)
7. **`link_tickets.py`** - Create ticket relationships (blocks, relates, duplicates)
8. **`add_attachments.py`** - Attach files (logs, screenshots) to tickets
9. **`assign_tickets.py`** - Assign tickets to users or unassign
10. **`manage_watchers.py`** - Add/remove watchers from tickets
11. **`close_tickets.py`** - Close/resolve tickets with proper resolution
12. **`query_tickets.py`** - Advanced JQL queries with detailed output

## Skills

**`jira-ticket-manager`** - Claude Code skill for JIRA automation workflows

See [skills/README.md](skills/README.md) for details.

## Setup

### Required Environment Variables

```bash
export JIRA_URL="https://your-instance.atlassian.net"
export JIRA_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
export JIRA_PROJECT="PROJ"  # Your project key
```

### Optional Environment Variables

```bash
# Customize defaults
export JIRA_ISSUETYPE="Bug"                      # Default: Bug
export JIRA_PRIORITY="Normal"                    # Default: Normal  
export JIRA_COMPONENT="YourComponent"            # Optional
export JIRA_SPRINT_FIELD="customfield_10020"    # Default: customfield_10020
export JIRA_STORY_POINTS_FIELD="customfield_10028"  # Default: customfield_10028
```

## Usage

### 1. Analyze Logs

```bash
python scripts/analyze_logs.py \
  --log-file test.log \
  --platform sGPU
```

Output: `analysis.json` with ticket recommendations

### 2. Create Tickets

```bash
python scripts/create_tickets.py \
  --log-file test.log \
  --config analysis.json \
  --platform sGPU \
  --labels test_failure,automated \
  --sprint 64581 \
  --story-points 3 \
  --test-command "pytest {test_file}" \
  --build-info '{"build":"v2.0","commit":"abc123","date":"2024-05-07"}'
```

### 3. Bulk Update

```bash
# Update by ticket range
python scripts/bulk_update.py \
  --tickets PROJ-100:150 \
  --sprint 64581 \
  --story-points 3

# Update by JQL query  
python scripts/bulk_update.py \
  --jql "labels = test_failure AND sprint is EMPTY" \
  --sprint 64581
```

### 4. Reopen Regressions

```bash
# From ticket list
python scripts/reopen_regressions.py \
  --tickets PROJ-100,PROJ-101,PROJ-102 \
  --build "Release 2.0" \
  --commit "abc123" \
  --date "2024-05-07"

# From JSON file
python scripts/reopen_regressions.py \
  --tickets regressions.json \
  --build "Release 2.0"
```

### 5. Transition Tickets Through Workflow

```bash
# Move to In Progress
python scripts/transition_tickets.py \
  --tickets PROJ-100:110 \
  --to "In Progress"

# Move to Done with comment
python scripts/transition_tickets.py \
  --tickets PROJ-100 \
  --to Done \
  --comment "Fixed in v2.0"

# Show available transitions
python scripts/transition_tickets.py \
  --tickets PROJ-100 \
  --show-transitions
```

### 6. Add Comments

```bash
# Add comment to single ticket
python scripts/add_comments.py \
  --tickets PROJ-100 \
  --comment "Verified on staging environment"

# Add comment to range
python scripts/add_comments.py \
  --tickets PROJ-100:110 \
  --comment "Fixed in build 2.0"

# Add comment from file
python scripts/add_comments.py \
  --tickets PROJ-100 \
  --comment-file release_notes.txt

# Add comment via JQL
python scripts/add_comments.py \
  --jql "labels = needs_update" \
  --comment "Updated in Sprint 32"
```

### 7. Link Tickets

```bash
# Create "blocks" relationship
python scripts/link_tickets.py \
  --from PROJ-100 \
  --to PROJ-101 \
  --type Blocks

# Mark as duplicate
python scripts/link_tickets.py \
  --from PROJ-103 \
  --to PROJ-100 \
  --type Duplicate

# Bulk link to parent ticket
python scripts/link_tickets.py \
  --from PROJ-200,PROJ-201,PROJ-202 \
  --to PROJ-100 \
  --type Relates

# Show available link types
python scripts/link_tickets.py --show-types
```

### 8. Add Attachments

```bash
# Attach single file
python scripts/add_attachments.py \
  --tickets PROJ-100 \
  --file screenshot.png

# Attach multiple files
python scripts/add_attachments.py \
  --tickets PROJ-100 \
  --file test.log \
  --file debug.log

# Attach to range
python scripts/add_attachments.py \
  --tickets PROJ-100:110 \
  --file build.log
```

### 9. Assign Tickets

```bash
# Assign to user (by account ID)
python scripts/assign_tickets.py \
  --tickets PROJ-100:110 \
  --assignee 5d123abc456def789

# Unassign tickets
python scripts/assign_tickets.py \
  --tickets PROJ-100:110 \
  --assignee unassigned

# Assign via JQL
python scripts/assign_tickets.py \
  --jql "status = 'In Progress' AND assignee is EMPTY" \
  --assignee 5d123abc456def789
```

### 10. Manage Watchers

```bash
# Add watcher
python scripts/manage_watchers.py \
  --tickets PROJ-100:110 \
  --add 5d123abc456def789

# Remove watcher
python scripts/manage_watchers.py \
  --tickets PROJ-100 \
  --remove 5d123abc456def789
```

### 11. Close/Resolve Tickets

```bash
# Close as Done
python scripts/close_tickets.py \
  --tickets PROJ-100:110 \
  --resolution Done

# Close as Fixed with comment
python scripts/close_tickets.py \
  --tickets PROJ-100 \
  --resolution Fixed \
  --comment "Fixed in release 2.0"

# Close as Won't Do
python scripts/close_tickets.py \
  --tickets PROJ-111 \
  --resolution "Won't Do" \
  --comment "Not applicable to current scope"

# Close via JQL
python scripts/close_tickets.py \
  --jql "labels = duplicate" \
  --resolution Duplicate
```

### 12. Query Tickets (Advanced JQL)

```bash
# Basic query
python scripts/query_tickets.py \
  --jql "project = PROJ AND status = Open"

# Query with specific fields
python scripts/query_tickets.py \
  --jql "labels = test_failure AND sprint is EMPTY" \
  --fields summary,status,assignee,priority

# Export to JSON
python scripts/query_tickets.py \
  --jql "sprint = 64581" \
  --format json > sprint_tickets.json

# Get just ticket keys
python scripts/query_tickets.py \
  --jql "status = Done AND updated >= -7d" \
  --format keys

# Recent updates
python scripts/query_tickets.py \
  --jql "updated >= -1d AND status changed to Done"
```

## Example: Hermetic Build Workflow

This is a **workflow** (how you use the scripts), not hardcoded behavior:

```bash
# 1. Setup for hermetic workflow
export JIRA_PROJECT="AIPCC"
LABELS="pytorch_hermetic,pytorch_qa"
SPRINT=64581
COMMAND="TEST_CONFIG=default python3 test/run_test.py -i {test_file}"

# 2. Analyze logs
python scripts/analyze_logs.py --log-file hermetic.log --platform sGPU

# 3. Create tickets
python scripts/create_tickets.py \
  --log-file hermetic.log \
  --config analysis.json \
  --platform sGPU \
  --labels $LABELS \
  --sprint $SPRINT \
  --story-points 3 \
  --test-command "$COMMAND" \
  --build-info '{"build":"Builder 2.12-RC5","commit":"46210d4","date":"2024-04-30"}'

# 4. Bulk operations
python scripts/bulk_update.py --tickets AIPCC-15363:15565 --sprint $SPRINT
```

**Key Point:** "Hermetic" is just labels + command template. The scripts work for ANY workflow.

## Complete Lifecycle Management

See **[LIFECYCLE.md](LIFECYCLE.md)** for comprehensive end-to-end workflows covering:

- **Full ticket lifecycle**: Create → Triage → Assign → Work → Review → Close
- **Common patterns**: Daily standups, sprint planning, release management, bug triage
- **JQL query library**: Status, assignment, sprint, date, and label queries
- **Best practices**: Validation, bulk operations, documentation, verification

**100% lifecycle coverage** - from ticket creation to closure with full automation.

## Real-World Impact

**PyTorch Hermetic Testing:**
- 61 tickets across 4 platforms
- 745+ detailed error extractions
- Weeks of manual work → 5 minutes

## License

MIT
