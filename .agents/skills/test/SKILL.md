---
name: test
description: Run the full test suite (backend pytest + frontend build/vitest). Specify "backend", "frontend", or "all" (default).
argument-hint: <backend|frontend|all>
user-invocable: true
---

# Run Tests

Run the test suite for: `$ARGUMENTS` (default: "all").

## Backend Tests (if target is "backend" or "all")

```bash
cd /Users/rsumit123/work/charade-chat/backend && .venv/bin/python -m pytest --tb=short -q
```

If tests fail, show the failures with verbose output:
```bash
cd /Users/rsumit123/work/charade-chat/backend && .venv/bin/python -m pytest --tb=long -v -x
```

## Frontend Tests (if target is "frontend" or "all")

### Build check:
```bash
cd /Users/rsumit123/work/charade-chat/frontend && npm run build 2>&1 | tail -20
```

### Unit tests (if vitest is configured):
```bash
cd /Users/rsumit123/work/charade-chat/frontend && npx vitest run 2>&1 | tail -30
```

## Report

Print a summary:
```
Test Results
============
Backend:  [X/X passed | FAILED]
Frontend Build: [OK | FAILED]
Frontend Tests: [X/X passed | FAILED | N/A]
```

If any tests failed, briefly explain what broke and suggest a fix.
