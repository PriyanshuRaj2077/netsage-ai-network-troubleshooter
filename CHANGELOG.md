# Changelog

## 1.0.1 — 2026-08-22

### Fixed
- Removed the unsupported `temperature` parameter from Claude Sonnet 5 API calls.
- Added Anthropic Structured Outputs with a strict JSON schema for LLM diagnoses.
- Added application-level validation for required LLM fields and confidence range.
- Added the configured `min_confidence_for_auto_flag` gate to the HITL approval flow.
- Low-confidence LLM diagnoses can no longer be approved from the dashboard until further investigation is performed.
- Clarified that NetSage AI logs approval but does not execute Cisco commands because direct deployment is disabled.
- Renamed the dashboard metric from "Human Audit Agreement Rate" to "Human Approval Rate" to match what the metric actually measures.
- Updated the Anthropic dependency floor for the current Structured Outputs API.

### Tests
- Added offline tests for all 30 dataset routing paths.
- Added tests for confidence gating and LLM request construction.
- Verified Python compilation and all tests pass.
