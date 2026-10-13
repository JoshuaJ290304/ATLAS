# ATLAS Governance Fix Package

Base repository: ATLAS v1.0.1

## Fixes included

1. **Project-level deletion**
   - Dashboard project cards now expose `Project Settings · Danger Zone → Delete Project`.
   - The UI requires the exact project name and a second confirmation.
   - The API independently verifies the exact project name.
   - Project-scoped database records are deleted through existing cascade relationships.
   - Project uploads and AI vector data are removed.
   - A platform-level `project.deleted` audit event is recorded outside the deleted project scope.

2. **Admin governance**
   - Last active administrator cannot be suspended or demoted.
   - Administrator cannot demote their own account.
   - Concurrent administrator lifecycle changes are serialized with row locking before the last-admin check.
   - Frontend requires explicit confirmation for promotion, demotion, and suspension.
   - Existing session-version invalidation and audit logging remain enabled.

3. **Single test-case Type**
   - Manual test cases already stored one `test_type`; the AI generator previously accepted several types at once.
   - AI generation now accepts exactly one `test_type` and creates exactly one test case per request.
   - Legacy `test_types` payloads are rejected instead of silently ignored.
   - UI now uses a single-select Type field.

4. **Demo data**
   - Added `docs/demo-data/ATLAS_SecureBank_Maximum_Requirements_for_AI_Extraction.docx` with 145 atomic requirements.
   - Added `docs/demo-data/ATLAS_SecureBank_Complete_Input_Data_and_Demo_Workflow.docx` with the complete SecureBank demonstration workflow.

## Verification

- `python -m compileall -q backend/app`: passed.
- Focused tests: `backend/tests/test_test_case_intelligence.py` + `backend/tests/test_project_governance.py`: **7 passed**.
- Frontend production build was not run because this environment has no installed `node_modules` and cannot reach the npm registry.
- Full backend suite was not run because the environment cannot download missing Python dependencies.
