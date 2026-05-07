# JIRA Automation Toolkit

Completely generic scripts for automating JIRA ticket management. No hardcoding - everything configurable via environment variables and parameters.

## Scripts (4 Generic Tools)

1. **`analyze_logs.py`** - Extract test failures from any log format
2. **`create_tickets.py`** - Create JIRA tickets (any project, any labels, any workflow)
3. **`bulk_update.py`** - Bulk update tickets (sprint, points, labels, any fields)
4. **`reopen_regressions.py`** - Reopen regression tickets with build info

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

## Real-World Impact

**PyTorch Hermetic Testing:**
- 61 tickets across 4 platforms
- 745+ detailed error extractions
- Weeks of manual work → 5 minutes

## License

MIT
