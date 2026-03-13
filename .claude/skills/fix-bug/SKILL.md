---
name: fix-bug
description: Fix a bug with full regression tracing -- analyzes all affected code paths before and after the fix to prevent cascading issues.
argument-hint: <description of the bug>
user-invocable: true
---

# Bug Fix with Regression Tracing

Bug to fix: `$ARGUMENTS`

Follow this protocol strictly. Past sessions have shown that fixing bugs without tracing related code paths leads to cascading issues.

## Step 1: Establish Baseline

Run the full test suite first to know what's currently passing:
```bash
cd /Users/rsumit123/work/charade-chat/backend && .venv/bin/python -m pytest --tb=short -q
```

## Step 2: Locate and Understand the Bug

1. Search the codebase to find all code related to the bug
2. Read the relevant files completely -- don't just look at the function with the bug
3. Identify the root cause

## Step 3: Impact Analysis (CRITICAL)

Before writing any fix, trace ALL code paths that could be affected:

1. **Callers**: What functions/handlers call the buggy code?
2. **Callees**: What does the buggy code call that might behave differently after the fix?
3. **Socket events**: Are there socket event handlers that depend on this behavior?
4. **UI states**: What frontend components render based on the data this code produces?
5. **Related flows**: What game flows (lobby, turns, scoring, playoffs, season-end) interact with this code?

List every affected path explicitly before proceeding.

## Step 4: Fix the Bug

Apply the minimal fix needed. Do NOT refactor surrounding code or add unrelated improvements.

## Step 5: Verify No Regressions

1. Run the full test suite:
```bash
cd /Users/rsumit123/work/charade-chat/backend && .venv/bin/python -m pytest --tb=short -q
```

2. For each affected code path identified in Step 3, manually trace through the logic to confirm it still works correctly with the fix applied.

3. If the fix touches frontend code, verify the build:
```bash
cd /Users/rsumit123/work/charade-chat/frontend && npm run build
```

## Step 6: Report

```
Bug Fix Summary
===============
Root cause:  [explanation]
Fix applied: [what was changed]
Files modified: [list]
Code paths verified: [list of paths checked]
Test results: [X/X passing]
Regressions found: [none / list]
```
