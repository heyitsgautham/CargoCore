# Sprint 2 Design: OpenAPI and Pytest Coverage Refresh

Date: 2026-04-17
Owner: API and QA
Status: Approved

## 1. Context

Sprint 2 requires:
1. Updated Swagger-compatible API documentation in tests/api-docs/openapi.swagger.yaml.
2. Backend API behavior alignment with documentation.
3. Updated pytest coverage for changed APIs in tests/contract, tests/integration, and tests/unit.
4. Meaningful error handling and user-story mapping coverage in documentation and tests.

User feedback indicates key updates from commits 16a286df and d2028ac9, with priority focus on:
- AI Support dashboard and support workflows.
- Damage claim and damage-review flows for customer and vendor.
- Dispatcher dashboard updates around route optimization, order clustering, and smart assignment positioning.

## 2. Goals and Non-Goals

### Goals
- Bring openapi.swagger.yaml in sync with current backend routes for changed and related endpoints.
- Preserve and improve user-story mapping, endpoint descriptions, and error-handling documentation.
- Add deep test coverage for changed APIs and smoke/parity checks for remaining backend endpoints.
- Keep tests in existing project structure and style.

### Non-Goals
- Full refactor of backend routing or service architecture.
- UI redesign or frontend-only behavior changes unrelated to API docs/tests.
- Replacing existing test harness patterns in conftest.py.

## 3. Recommended Approach

Use a hybrid update strategy:
1. Treat backend routers and schemas as source of truth.
2. Refresh API spec coverage for changed areas and ensure path/method parity against backend routes.
3. Preserve curated narrative sections (user stories, mapping summaries, and endpoint descriptions).
4. Expand pytest in three layers:
   - Contract tests for spec and declaration correctness.
   - Integration tests for endpoint behavior and error handling.
   - Unit tests for schema validation of changed request/response models.

Rationale:
- Avoids drift between code and docs.
- Keeps deliverable reviewer-friendly.
- Balances completeness with practical sprint scope.

## 4. API Scope for Sprint 2

### 4.1 AI Support and Support Dashboard APIs
Document and test support-oriented endpoints under /api/v1/ai, especially:
- /support/dashboard
- /support/settings (get, put)
- /support/analytics
- /support/analytics/insights/{insight_id}/execute
- /support/sessions and support session actions
- /tickets and related ticket actions
- /support/damage-reports and related support messaging/notes
- /support/refund-cases and urgent update

### 4.2 Damage Claim and Damage Review APIs
Document and test:
- Customer damage-report APIs.
- Vendor damage-report APIs.
- Damage review queue APIs under /api/v1/damage-reports.

### 4.3 Dispatcher-Oriented Updated APIs
Ensure docs and tests align with backend behavior for:
- /api/v1/orders/cluster
- /api/v1/orders/optimize-routes
- /api/v1/orders/batch-assign
- /api/v1/orders/assignment-preview
- /api/v1/orders/ai-driver-suggestions
- /api/v1/orders/return-suggestions
- /api/v1/orders/auto-balance (if active in backend)

Note: Documentation language in dispatcher sections should reflect smart assignment as the current operational framing while preserving active endpoints.

## 5. Documentation Design Rules

Each updated endpoint should include:
- Clear summary and purpose-driven description.
- User-role and security expectations.
- Request schema and parameter constraints.
- Success response schema.
- Error response coverage (401, 403, 404, 422 as relevant).
- Consistent operation naming and /api/v1 path style.

Top-level user-story and mapping sections must remain present and updated for changed areas.

## 6. Test Design

### 6.1 Contract Tests (tests/contract)
- Validate updated paths and methods exist in openapi.swagger.yaml.
- Validate key request/response schema references for changed APIs.
- Add route-to-spec parity smoke test to fail if backend routes are missing in YAML.

### 6.2 Integration Tests (tests/integration)
- Use existing async client and dependency override pattern.
- Monkeypatch service methods and assert:
  - Success codes and required response shape.
  - Negative paths and meaningful error behavior.
  - Role/auth restrictions where applicable.

### 6.3 Unit Tests (tests/unit)
- Add schema validation tests for changed model classes (valid and invalid payloads).
- Focus on support settings, support damage report schemas, damage review update, and dispatcher assignment/suggestion schemas.

## 7. Error Handling and Evidence Expectations

- Ensure changed API areas have explicit negative tests (401/403/404/422 at minimum where applicable).
- Continue evidence recording pattern from tests/conftest.py for expected vs actual output traceability.

## 8. Verification Gates

Gate 1: YAML validity and changed endpoint declarations complete.
Gate 2: Contract tests pass, including backend route to YAML parity check.
Gate 3: Integration tests for changed APIs pass (success and failure paths).
Gate 4: Unit schema tests for changed models pass.
Gate 5: No regression in existing core contract/integration tests.

## 9. Deliverables

- Updated tests/api-docs/openapi.swagger.yaml.
- New or updated tests in:
  - tests/contract
  - tests/integration
  - tests/unit
- Test execution evidence for updated API coverage and smoke parity.

## 10. Acceptance Criteria

- Swagger YAML reflects current backend changed APIs and documents error handling clearly.
- Changed API areas are deeply covered by pytest.
- Remaining backend API surface has parity/smoke guard against documentation drift.
- Sprint checklist requirements for Swagger-first, consistency, and testability are satisfied.
