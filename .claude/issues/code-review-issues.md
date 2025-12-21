# SchoolConnect Code Review Issues

**Generated**: 2025-12-20
**Status**: Tracking

## Issue Summary

| Priority | Count | Status |
|----------|-------|--------|
| CRITICAL | 5 | Pending |
| HIGH | 5 | Pending |
| MEDIUM | 4 | Pending |

---

## CRITICAL Issues

### CRIT-1: Add authentication/authorization system
- **File**: `streamlit-chat/app.py`, new `streamlit-chat/auth.py`
- **Impact**: FERPA violation - any user can access all student data
- **Solution**: Implement parent authentication with student-to-parent relationship validation
- **Status**: [ ] Pending

### CRIT-2: Remove API key from session state
- **File**: `streamlit-chat/app.py`, `streamlit-chat/ai_assistant.py`
- **Impact**: API keys extractable via browser DevTools, financial liability
- **Solution**: Use server-side secrets only (Streamlit Secrets or env vars)
- **Status**: [ ] Pending

### CRIT-3: Refactor data_queries.py to use existing Repository pattern
- **File**: `streamlit-chat/data_queries.py`
- **Impact**: Code duplication, maintenance burden, inconsistent behavior
- **Solution**: Create adapter that delegates to existing `src/database/repository.py`
- **Status**: [ ] Pending

### CRIT-4: Fix SQL injection risk with input validation
- **File**: `streamlit-chat/data_queries.py`
- **Impact**: Potential data exfiltration through LIKE pattern manipulation
- **Solution**: Add input validation/sanitization for student names
- **Status**: [ ] Pending

### CRIT-5: Implement connection pooling
- **File**: `streamlit-chat/data_queries.py`
- **Impact**: Resource exhaustion, file descriptor leaks under load
- **Solution**: Use context managers and existing `src/database/connection.py` pool
- **Status**: [ ] Pending

---

## HIGH Priority Issues

### HIGH-1: Add session timeout and logout functionality
- **File**: `streamlit-chat/app.py`, new `streamlit-chat/session_manager.py`
- **Impact**: Sessions persist indefinitely, risk on shared computers
- **Solution**: Implement 30-minute timeout and logout button
- **Status**: [ ] Pending

### HIGH-2: Add exponential backoff retry logic for AI API calls
- **File**: `streamlit-chat/ai_assistant.py`
- **Impact**: User-facing errors on temporary API failures
- **Solution**: Add retry with exponential backoff for rate limits and 5xx errors
- **Status**: [ ] Pending

### HIGH-3: Implement message history circular buffer (max 10)
- **File**: `streamlit-chat/app.py`
- **Impact**: Unbounded memory growth in long sessions
- **Solution**: Limit stored messages to 50, send only last 10 to AI
- **Status**: [ ] Pending

### HIGH-4: Replace hardcoded "Delilah" with configurable student selection
- **File**: `streamlit-chat/app.py`
- **Impact**: Demo code leaking into production, privacy concern
- **Solution**: Dynamic student selection from database
- **Status**: [ ] Pending

### HIGH-5: Add proper test fixtures and mocking for AI API
- **File**: `streamlit-chat/test_app.py`
- **Impact**: Tests depend on real data, not portable
- **Solution**: Use pytest fixtures with test database, mock AI calls
- **Status**: [ ] Pending

---

## MEDIUM Priority Issues

### MED-1: Add caching for student summary with @st.cache_data
- **File**: `streamlit-chat/app.py`
- **Impact**: Unnecessary database query on every Streamlit rerun
- **Solution**: Add @st.cache_data decorator with TTL
- **Status**: [ ] Pending

### MED-2: Move inline CSS to external file
- **File**: `streamlit-chat/app.py`, new `streamlit-chat/.streamlit/custom.css`
- **Impact**: 200+ lines of CSS mixed with Python, hard to maintain
- **Solution**: Extract CSS to external file, load dynamically
- **Status**: [ ] Pending

### MED-3: Add missing docstrings to app.py
- **File**: `streamlit-chat/app.py`
- **Impact**: Low documentation coverage (20%)
- **Solution**: Add Google-style docstrings to all functions
- **Status**: [ ] Pending

### MED-4: Add Streamlit setup documentation to README
- **File**: `README.md`
- **Impact**: New developers cannot run the Streamlit app
- **Solution**: Add installation and configuration section
- **Status**: [ ] Pending

---

## Acceptance Criteria

All issues must:
1. Pass `ruff check` with no errors
2. Pass all existing tests
3. Include new tests for modified functionality
4. Pass CI pipeline validation

---

## Progress Log

| Date | Issue | Status | Notes |
|------|-------|--------|-------|
| 2025-12-20 | All | Created | Initial issue tracking |
