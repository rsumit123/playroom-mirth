---
name: qa-check
description: Run a QA check on a specific game flow or feature -- traces through code paths, checks UI states, and identifies potential issues.
argument-hint: <feature or flow to check, e.g. "playoff flow" or "room joining">
user-invocable: true
---

# QA Check

Feature/flow to verify: `$ARGUMENTS`

## Step 1: Identify All Components

Search the codebase to find every file involved in this feature/flow:
- Backend route handlers and socket event handlers
- Frontend components and pages
- State management (context, stores)
- Shared types/constants

## Step 2: Trace the Full Flow

Walk through the feature step-by-step as a user would experience it:

1. What triggers the flow? (user action, socket event, timer)
2. What backend endpoints/socket events are called?
3. What data is sent/received?
4. What state transitions happen?
5. What UI updates should occur?
6. What are the edge cases? (disconnection, race conditions, multiple users)

## Step 3: Check for Known Pitfalls

Review against these common issues in this codebase:
- Socket listener duplication (missing `socket.off()` before `socket.on()`)
- selfPlayerId being overwritten by lobby_update broadcasts
- Socket reconnection using `once` instead of `on` for room:register
- Missing error handling for socket disconnection mid-flow
- Race conditions between REST calls and socket events

## Step 4: Run Related Tests

```bash
cd /Users/rsumit123/work/charade-chat/backend && .venv/bin/python -m pytest --tb=short -q -k "RELEVANT_TEST_PATTERN"
```

## Step 5: Report

```
QA Check: [feature name]
=========================
Components involved: [list files]
Flow steps verified: [numbered list]
Potential issues found: [list or "none"]
Test coverage: [which tests cover this flow]
Missing test coverage: [gaps identified]
Recommendations: [any suggested improvements]
```
