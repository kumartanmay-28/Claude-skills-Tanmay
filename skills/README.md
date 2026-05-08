# JIRA Ticket Manager Skill

## What Makes This Skill Different?

Unlike generic JIRA automation or simple ticket creation tools, this skill provides **complete end-to-end JIRA lifecycle management** from ticket creation to closure, with specialized capabilities for test failure tracking at scale.

### 🎯 Purpose-Built for Test Failure Management

**The Problem:**
- 745+ test failures across 4 platforms
- Need to create tickets with detailed error context
- Must track regressions (closed tickets failing again)
- Bulk operations on 61+ tickets at once
- Manual work takes weeks

**This Skill's Solution:**
- ✅ Extracts **actual error messages** from logs (not just test names)
- ✅ Intelligently **clubs** tests by file/directory to reduce ticket noise
- ✅ Creates tickets with **full reproduction commands** and build metadata
- ✅ **Cross-references** existing tickets to avoid duplicates
- ✅ Detects **regressions** and reopens with recurrence details
- ✅ Handles **bulk updates** across hundreds of tickets

### 🔑 Key Differentiators

#### 1. **Intelligent Error Extraction**
```
Not just: "Test failed"
But: "RuntimeError: Calling torch.linalg.cholesky on a CPU tensor requires
      compiling PyTorch with LAPACK. Please use PyTorch built with LAPACK support."
```

#### 2. **Smart Clubbing Strategies**
- By file (37 tickets instead of 120)
- By directory (10 tickets for related tests)
- By error pattern (groups similar failures)

#### 3. **Coverage Verification**
Ensures 100% of failures have tickets - no test left behind.

#### 4. **Regression Intelligence**
Finds closed tickets still failing and reopens with:
- Build information
- Recurrence date
- New error messages
- Impact analysis

#### 5. **Production-Ready ADF Descriptions**
Creates JIRA tickets with Atlassian Document Format (ADF) including:
- Structured error tables
- Code blocks with syntax highlighting
- Reproduction steps
- Build metadata
- Clickable links

### 📊 Real-World Impact

**PyTorch Hermetic Build Testing (Actual Use Case):**

**Before this skill:**
- Manual ticket creation: ~2-3 hours per platform
- Error extraction: Copy-paste from logs
- Sprint assignment: One ticket at a time
- Regression checking: Manual comparison

**After this skill:**
```bash
# Create 61 tickets with full details in ~5 minutes
python scripts/create_tickets_hermetic.py --log test.log --sprint 32

# Update all 61 tickets with sprint in seconds
python scripts/bulk_update.py --tickets AIPCC-15363:15565 --sprint 32
```

**Time saved:** Weeks → Minutes

### 🆚 Comparison with Other Tools

| Feature | Generic JIRA API | This Skill |
|---------|------------------|------------|
| **Lifecycle Coverage** |
| Create tickets | ✅ | ✅ |
| Workflow transitions | ✅ Manual | ✅ Automated |
| Comments | ✅ Manual | ✅ Bulk |
| Ticket linking | ✅ Manual | ✅ Bulk |
| Attachments | ✅ Manual | ✅ Bulk |
| Assignment | ✅ Manual | ✅ Bulk + JQL |
| Watchers | ✅ Manual | ✅ Bulk |
| Close/resolve | ✅ Manual | ✅ Bulk with resolution |
| Advanced queries | ✅ Basic | ✅ JQL + formatting |
| **Test Failure Features** |
| Extract log errors | ❌ | ✅ Full error context |
| Intelligent clubbing | ❌ | ✅ Multiple strategies |
| Regression detection | ❌ | ✅ Cross-log analysis |
| Coverage verification | ❌ | ✅ 100% guarantee |
| ADF formatting | Manual | ✅ Automated |
| **Scale** |
| Bulk operations | ✅ Basic | ✅ Advanced (JQL, ranges) |
| Production-tested | - | ✅ 61 real tickets |
| **Lifecycle Coverage** | ~40% | **100%** ✅ |

### 🎓 When to Use This Skill

**Perfect for:**
- Test failure tracking (unit tests, integration tests, E2E)
- Hermetic build validation
- Regression analysis across builds
- Bulk ticket operations (100+ tickets)
- Maintaining ticket quality (detailed descriptions)

**Not designed for:**
- General project management
- User story creation
- Sprint planning
- Time tracking

### 📚 How It Works

1. **Analyze** - Parse logs, extract failures with error messages
2. **Club** - Group related tests to reduce ticket count
3. **Create** - Generate JIRA tickets with full ADF descriptions
4. **Verify** - Ensure all failures have tickets
5. **Update** - Bulk operations (sprint, points, labels)
6. **Regress** - Detect closed tickets failing again

### 🔧 Customization

The skill adapts to your workflow:
- Configurable clubbing strategies
- Custom JIRA field IDs
- Platform-specific commands
- Error pattern matching
- Flexible JQL queries

### 📖 Full Documentation

See [jira-ticket-manager.md](jira-ticket-manager.md) for complete usage guide.

---

**Bottom line:** This skill automates the tedious, error-prone parts of test failure tracking while maintaining high ticket quality. It's not just JIRA automation - it's **intelligent test failure management**.
