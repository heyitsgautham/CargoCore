# Cargo-Core - AI Usage & System Overview
## (Backend)

### Overview

This document explains how AI is used inside the Cargo-Core backend system.

The backend is built around FastAPI services, PostgreSQL, SQLAlchemy, Alembic, Redis, and structured middleware-driven request handling. AI is integrated only in controlled backend features and is not responsible for the main business logic of the platform.

To be clear:

- The API architecture, database schema, authentication, validation, workflow rules, and role-based access are manually designed and implemented.
- AI is not used to run the platform automatically.
- AI is only used in limited backend areas such as:
  - natural-language query support
  - structured data summarization
  - image-based moving estimate assistance
  - escalation support for human follow-up

Think of AI here as a controlled service layer, not the core backend engine.

## 1. System Architecture & Development Approach

### Core Philosophy

- 100% manually built backend logic
All routing, request validation, authentication, database access, and service-layer rules are written directly in the backend codebase.

- AI used only as an assistive capability
AI helps convert user questions into backend-friendly responses, but it does not own business rules or make irreversible decisions.

- Full developer and system control
Every AI interaction is wrapped by backend validation, access control, error handling, and persistence rules.

### Backend Stack

- FastAPI for API routing and service exposure
- PostgreSQL 16 for transactional and operational data
- SQLAlchemy 2.0 async for ORM and database sessions
- Alembic for schema migrations
- Redis for cache/support infrastructure
- Gemini integration for controlled AI responses
- Loguru-based middleware logging for observability

### Integration Pattern

AI is plugged into the backend like a guarded external service:

- no tight coupling with core backend modules
- invoked only on AI-specific endpoints
- never trusted without validation
- always surrounded by authorization, schema rules, and fallback handling

The backend continues to function even if the AI layer is unavailable.

## 2. Backend Workflows + AI Assist

### How the Backend Is Built

The backend follows a layered structure:

- `app/main.py` wires middleware and domain routers
- `app/routers/` exposes API endpoints
- `app/services/` contains business logic
- `app/models/` and `app/schemas/` handle persistence and validation
- middleware logs request/response details for traceability
- tests mock AI calls and verify failure/safety scenarios

Everything above is manually implemented and remains deterministic.

### Where AI Is Used

AI is currently used in a few controlled backend workflows:

#### 1. AI Chat Query Support

Endpoint:
`POST /api/v1/ai/chat`

Backend flow:

- authenticated user sends a natural-language question
- backend loads recent conversation context
- AI may answer directly, or request a read-only SQL query
- generated SQL is validated before execution
- query runs only on a read-only database session
- backend stores the conversation, intent, and generated SQL for auditability
- final response is returned to the user

Typical use cases:

- "How many users are registered?"
- "Show top warehouses by delivered orders"
- "What is the current driver performance summary?"

#### 2. Vision-Based Estimate Support

Endpoint:
`POST /api/v1/ai/estimate-image`

Backend flow:

- user uploads a room or goods image
- backend validates file type and size
- AI analyzes visible items and suggests:
  - detected space
  - item list
  - packaging needs
  - labour estimate
  - vehicle recommendation
  - rough cost estimate

Important note:
the response is advisory only. The platform still controls how estimates are displayed or acted upon.

#### 3. Escalation Support

Endpoints:

- `POST /api/v1/ai/escalate/{conversation_id}`
- `GET /api/v1/ai/escalations`
- `PUT /api/v1/ai/escalations/{escalation_id}/resolve`

AI-related conversations can be escalated for human review. Human agents and authorized managers remain responsible for resolution.

### Important Note

Even when AI is active:

- AI does not update operational records directly
- AI does not bypass authentication or role checks
- AI does not execute write queries
- AI does not replace human review in escalation handling

The backend remains rule-driven and controlled.

## 3. Realistic Backend AI Flow

### Operational Query Example

User asks:
"How many active users are currently in the system?"

System flow:

1. Backend authenticates the request.
2. AI receives the user question plus backend-defined system instructions.
3. AI proposes a SQL `SELECT` query.
4. Backend SQL validator checks that the query is safe.
5. Query executes only on the read-only database session.
6. Result is transformed into a user-friendly reply.
7. Conversation history and generated SQL are stored for traceability.

### Image Estimate Example

User uploads a room photo.

System flow:

1. Backend validates MIME type and file size.
2. AI receives the image and a strict JSON output prompt.
3. AI returns a structured estimate payload.
4. Backend parses the JSON and rejects malformed responses.
5. Final result is returned as API data, not as uncontrolled free text.

## 4. Prompt Design (How AI Is Actually Used)

Prompts are manually designed in code and are not generated dynamically without control.

Typical structure:

`System Instruction + Schema Context + User Message + Tool Rules`

For image analysis:

`Image Input + Strict JSON Output Format + Estimation Rules`

### Response Expectations

AI responses are expected to be:

- short
- clear
- data-backed
- safe to validate
- optional from a product perspective

Typical backend expectations include:

- use read-only SQL only
- avoid sensitive columns like `password_hash`
- operate only on allowed tables
- return concise summaries instead of raw hallucinated data

## 5. Control, Safety & Transparency

This backend is intentionally designed to avoid unsafe AI behavior.

### Safety Controls

- AI chat is protected by authentication
- missing Gemini configuration returns a controlled error
- only `SELECT` queries are allowed
- multiple statements are blocked
- dangerous system tables and patterns are blocked
- sensitive columns are blocked
- result size is limited
- escalations require explicit human action

### Observability

The backend keeps AI usage observable through:

- request/response logging middleware
- stored conversation sessions
- stored message roles and intent labels
- generated SQL audit trail
- stored query results for debugging
- escalation status tracking

This ensures AI remains inspectable rather than opaque.

## 6. Key Backend Examples

### Database Analytics Query

- user asks for delivery, inventory, warehouse, or user metrics
- AI generates a safe read-only query
- backend validates and executes it
- backend returns summarized results

### AI Conversation Persistence

- each AI interaction is tied to a session ID
- conversation messages are stored in `ai_conversations`
- intent values such as `greeting`, `general`, `db_query`, and `error` are tracked

### Human Escalation

- conversation can be flagged for review
- human agents or managers can inspect and resolve it
- no automatic escalation closure happens without backend action

### Failure Handling

- if AI is unavailable, the backend responds with controlled error messaging
- backend tests explicitly verify unconfigured AI and unsafe SQL scenarios

## 7. Sample AI Activity Log Snapshot

The following entries are illustrative sample logs prepared in report format for documentation/demo purposes.

| Timestamp | Endpoint | User Action | AI Behavior | Safety Layer | Final Outcome |
|---|---|---|---|---|---|
| 2026-03-24 10:14 | `/api/v1/ai/chat` | Asked for total registered users | Generated count query | SQL validator added safe limit | Returned user count summary |
| 2026-03-24 10:18 | `/api/v1/ai/chat` | Asked for top performing drivers | Generated aggregate read-only query | Allowed-table validation passed | Returned ranked driver overview |
| 2026-03-24 10:25 | `/api/v1/ai/chat` | Asked for passwords | Attempted sensitive access | `password_hash` access blocked | Returned safe refusal/error |
| 2026-03-24 10:41 | `/api/v1/ai/estimate-image` | Uploaded room photo | Produced packing and vehicle estimate | File type and size validated | Returned structured JSON estimate |
| 2026-03-24 11:03 | `/api/v1/ai/chat` | Asked warehouse load summary | Generated summary query | Read-only DB session enforced | Returned warehouse metrics |
| 2026-03-24 11:16 | `/api/v1/ai/escalate/{id}` | Requested human review | AI conversation marked for follow-up | Ownership check applied | Escalation created |
| 2026-03-24 11:34 | `/api/v1/ai/chat` | Submitted malformed request context | AI produced unusable response | Fallback error handler triggered | Returned retry message |
| 2026-03-24 11:52 | `/api/v1/ai/chat` | Asked order delivery statistics | Generated aggregate SQL | Query limit and whitelist applied | Returned delivery summary |

## 8. Final Summary

Cargo-Core backend is a backend-first system, not an AI-first backend.

- All core business logic is manually implemented
- Authentication, authorization, validation, and persistence remain fully owned by the backend
- AI is used only for:
  - query assistance
  - summarization
  - estimate support
  - escalation assistance

In short:

The backend works as a normal logistics platform without AI.

AI only improves usability and response quality in a few controlled service flows.
