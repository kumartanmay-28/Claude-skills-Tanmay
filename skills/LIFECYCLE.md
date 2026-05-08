<!-- --># Complete JIRA Lifecycle Management

This document shows how to use the toolkit for **end-to-end JIRA ticket lifecycle management**, from creation to closure.

## Lifecycle Stages

```
Create → Triage → Assign → Work → Review → Close
  ↓        ↓        ↓        ↓       ↓       ↓
Scripts: create → transition → assign → comment → transition → close
         link                 attach            query
```

## Full Workflow Example

### Stage 1: Create Tickets

```bash
# Create tickets from test failures
python scripts/create_tickets.py \
  --log-file test.log \
  --platform API \
  --labels test_failure,sprint_32 \
  --sprint 64581 \
  --story-points 3
```

**Output:** PROJ-200 to PROJ-250 created

---

### Stage 2: Triage and Organize

```bash
# Link related tickets
python scripts/link_tickets.py \
  --from PROJ-201,PROJ-202,PROJ-203 \
  --to PROJ-200 \
  --type Blocks

# Mark duplicates
python scripts/link_tickets.py \
  --from PROJ-210 \
  --to PROJ-200 \
  --type Duplicate

# Close duplicate
python scripts/close_tickets.py \
  --tickets PROJ-210 \
  --resolution Duplicate \
  --comment "Duplicate of PROJ-200"

# Add watchers to critical tickets
python scripts/manage_watchers.py \
  --tickets PROJ-200 \
  --add 5d123abc456def789
```

---

### Stage 3: Assign Work

```bash
# Query unassigned tickets
python scripts/query_tickets.py \
  --jql "sprint = 64581 AND assignee is EMPTY" \
  --format keys > unassigned.txt

# Assign to team members
python scripts/assign_tickets.py \
  --tickets PROJ-200:210 \
  --assignee 5d123abc456def789

python scripts/assign_tickets.py \
  --tickets PROJ-211:220 \
  --assignee 5d987fed654cba321

# Move to In Progress
python scripts/transition_tickets.py \
  --tickets PROJ-200:220 \
  --to "In Progress" \
  --comment "Started work"
```

---

### Stage 4: Work and Update

```bash
# Add progress comments
python scripts/add_comments.py \
  --tickets PROJ-200 \
  --comment "Root cause identified: config issue in API endpoint"

# Attach debug logs
python scripts/add_attachments.py \
  --tickets PROJ-200 \
  --file debug.log \
  --file stacktrace.txt

# Update story points if needed
python scripts/bulk_update.py \
  --tickets PROJ-200 \
  --story-points 5
```

---

### Stage 5: Review

```bash
# Move to code review
python scripts/transition_tickets.py \
  --tickets PROJ-200:205 \
  --to "In Review" \
  --comment "PR created: https://github.com/org/repo/pull/123"

# Add reviewers as watchers
python scripts/manage_watchers.py \
  --tickets PROJ-200:205 \
  --add 5d111aaa222bbb333

# Query tickets in review
python scripts/query_tickets.py \
  --jql "status = 'In Review' AND sprint = 64581" \
  --fields summary,assignee,updated
```

---

### Stage 6: Close

```bash
# Move to Done
python scripts/transition_tickets.py \
  --tickets PROJ-200:205 \
  --to Done \
  --comment "Merged to main"

# Close with resolution
python scripts/close_tickets.py \
  --tickets PROJ-200:205 \
  --resolution Fixed \
  --comment "Fixed in release 2.0.1"

# Close won't fix items
python scripts/close_tickets.py \
  --tickets PROJ-206 \
  --resolution "Won't Do" \
  --comment "Working as designed"
```

---

### Stage 7: Reporting and Analysis

```bash
# Sprint summary
python scripts/query_tickets.py \
  --jql "sprint = 64581 AND status = Done" \
  --format json > sprint_completed.json

# Closed this week
python scripts/query_tickets.py \
  --jql "status changed to Done DURING (-7d, now())" \
  --fields summary,assignee,resolution

# Still open
python scripts/query_tickets.py \
  --jql "sprint = 64581 AND status != Done"

# Unassigned tickets
python scripts/query_tickets.py \
  --jql "sprint = 64581 AND assignee is EMPTY" \
  --format keys
```

---

## Common Workflow Patterns

### Pattern 1: Daily Standup Prep

```bash
# What I'm working on
python scripts/query_tickets.py \
  --jql "assignee = currentUser() AND status = 'In Progress'"

# What I completed yesterday
python scripts/query_tickets.py \
  --jql "assignee = currentUser() AND status changed to Done DURING (-1d, now())"

# Blockers
python scripts/query_tickets.py \
  --jql "assignee = currentUser() AND labels = blocked"
```

### Pattern 2: Sprint Planning

```bash
# Get backlog items
python scripts/query_tickets.py \
  --jql "project = PROJ AND status = Open AND sprint is EMPTY" \
  --fields summary,priority,labels \
  --max-results 50

# Assign to sprint
python scripts/bulk_update.py \
  --tickets PROJ-300:350 \
  --sprint 64582

# Estimate story points
python scripts/bulk_update.py \
  --tickets PROJ-300:310 \
  --story-points 3

python scripts/bulk_update.py \
  --tickets PROJ-311:320 \
  --story-points 5
```

### Pattern 3: Release Management

```bash
# Query all tickets for release
python scripts/query_tickets.py \
  --jql "fixVersion = '2.0' AND status != Done" \
  --format keys > pending_release.txt

# Add release notes comment
python scripts/add_comments.py \
  --jql "fixVersion = '2.0' AND status = Done" \
  --comment "Included in release 2.0 - deployed 2024-05-07"

# Link to release epic
python scripts/link_tickets.py \
  --from-file pending_release.txt \
  --to PROJ-1000 \
  --type Relates
```

### Pattern 4: Bug Triage

```bash
# Find new bugs
python scripts/query_tickets.py \
  --jql "type = Bug AND created >= -7d AND priority is EMPTY"

# Prioritize critical bugs
python scripts/bulk_update.py \
  --jql "type = Bug AND labels = production_issue" \
  --labels critical,sprint_32

# Assign to on-call engineer
python scripts/assign_tickets.py \
  --jql "type = Bug AND labels = critical AND assignee is EMPTY" \
  --assignee 5d123abc456def789

# Notify team
python scripts/add_comments.py \
  --jql "type = Bug AND labels = critical" \
  --comment "Assigned to on-call team for immediate triage"
```

### Pattern 5: Regression Handling

```bash
# Find regressions (closed tickets failing again)
python scripts/reopen_regressions.py \
  --tickets PROJ-100,PROJ-150,PROJ-200 \
  --build "Release 2.1" \
  --commit "def456" \
  --date "2024-05-07"

# Label as regression
python scripts/bulk_update.py \
  --tickets PROJ-100,PROJ-150,PROJ-200 \
  --labels regression,urgent

# Escalate
python scripts/add_comments.py \
  --tickets PROJ-100,PROJ-150,PROJ-200 \
  --comment "REGRESSION: Previously fixed but failing again in 2.1"

# Add stakeholders as watchers
python scripts/manage_watchers.py \
  --tickets PROJ-100,PROJ-150,PROJ-200 \
  --add 5d999eee888fff777
```

---

## JQL Query Library

### Status Queries

```jql
# Open items
status = Open

# In progress items
status = "In Progress"

# Recently closed
status changed to Done DURING (-7d, now())

# Stuck items (in progress >14 days)
status = "In Progress" AND updated <= -14d
```

### Assignment Queries

```jql
# My open tickets
assignee = currentUser() AND status != Done

# Unassigned in current sprint
sprint = 64581 AND assignee is EMPTY

# Team workload
assignee in (user1, user2, user3) AND status != Done
```

### Sprint Queries

```jql
# Current sprint
sprint in openSprints()

# Sprint completion
sprint = 64581 AND status = Done

# Sprint velocity
sprint = 64581 AND resolved is not EMPTY
```

### Date Queries

```jql
# Created this week
created >= -7d

# Updated today
updated >= startOfDay()

# Overdue (due date passed)
dueDate < now() AND status != Done
```

### Label Queries

```jql
# Test failures
labels = test_failure

# Critical bugs
type = Bug AND labels = critical

# Multiple labels (AND)
labels = test_failure AND labels = regression

# Multiple labels (OR)
labels in (bug, regression, critical)
```

---

## Best Practices

### 1. Always Validate Queries First

```bash
# Test query with format=keys
python scripts/query_tickets.py \
  --jql "sprint = 64581" \
  --format keys

# Review count
python scripts/query_tickets.py \
  --jql "sprint = 64581"
```

### 2. Use Bulk Operations Efficiently

```bash
# Instead of individual updates, use ranges
python scripts/bulk_update.py \
  --tickets PROJ-100:200 \
  --sprint 64581

# Or use JQL for complex selections
python scripts/bulk_update.py \
  --jql "labels = test_failure AND sprint is EMPTY" \
  --sprint 64581
```

### 3. Document Important Actions

```bash
# Always add comments for major changes
python scripts/transition_tickets.py \
  --tickets PROJ-100 \
  --to Done \
  --comment "Fixed in PR #123, deployed to production"

python scripts/bulk_update.py \
  --tickets PROJ-100:110 \
  --sprint 64582 \
  --comment "Moving to next sprint due to scope increase"
```

### 4. Verify Before Closing

```bash
# Check ticket status before bulk close
python scripts/query_tickets.py \
  --jql "key in (PROJ-100, PROJ-101, PROJ-102)" \
  --fields status,assignee,resolution

# Then close
python scripts/close_tickets.py \
  --tickets PROJ-100,PROJ-101,PROJ-102 \
  --resolution Fixed \
  --comment "Verified in staging and production"
```

---

## Complete Lifecycle Coverage

| Stage | Tools | Covered? |
|-------|-------|----------|
| **Creation** | create_tickets.py | ✅ |
| **Triage** | link_tickets.py, query_tickets.py | ✅ |
| **Assignment** | assign_tickets.py, manage_watchers.py | ✅ |
| **Work** | transition_tickets.py, add_comments.py, add_attachments.py | ✅ |
| **Review** | transition_tickets.py, add_comments.py | ✅ |
| **Closure** | close_tickets.py, transition_tickets.py | ✅ |
| **Reporting** | query_tickets.py | ✅ |
| **Updates** | bulk_update.py | ✅ |
| **Regressions** | reopen_regressions.py | ✅ |

**100% lifecycle coverage achieved! 🎉**
