# app-L5x Technical Specification (MVP)

## 1) Purpose
Define implementation-ready technical requirements for the offline `app-L5x` system.

This spec converts the project plan into concrete architecture, contracts, and acceptance criteria for MVP delivery.

---

## 2) Scope
### In Scope (MVP)
- Local upload of `.L5X`
- Parse/validate `.L5X` (target Studio5000 revisions v32–v36)
- Interactive hierarchy explorer (tree)
- Wide-scope comment/note editing
- Diff preview and change audit trail
- Safe manual export to `.L5X`
- Tag relationship extraction + interactive graph
- Offline knowledge indexing + retrieval
- Strict evidence-only troubleshooting assistant

### Out of Scope (MVP)
- Cloud services/APIs
- Multi-user collaboration
- Online PLC runtime ingestion
- Advanced prediction/optimization features

---

## 3) System Constraints
- **Security:** local-only processing/storage; no outbound network calls for core app.
- **Performance target:** AI response under **15 seconds** on supported workstation.
- **Compatibility:** `.L5X` from Studio5000 v32–v36.
- **Export fidelity:** preserve original order/formatting as much as technically possible.
- **Evidence policy:** no citation -> no answer.

## 3.1 PM Default Decisions (Locked)
- **Primary hierarchy UI:** indented tree explorer (default); graph/treemap are secondary views.
- **Offline model stack (MVP):**
  - Embeddings: `bge-small-en-v1.5`
  - Vector store: `FAISS`
  - Local LLM class: small local instruct model (baseline: `Llama 3.2 3B Instruct` class runtime)
- **Workstation baseline:** 16 GB RAM, 4+ CPU cores, SSD, Windows 10/11.
- **Import policy:** block on critical corruption; allow partial read with warnings for non-critical unsupported structures.
- **Audit policy:** immutable local audit entries + exportable report.
- **Insufficient-evidence policy:** fixed phrase + targeted follow-ups + missing-context hints.

## 3.2 GDPR & Compliance Controls
- **Data minimization:** store only data needed for parse/edit/export/index/audit workflows.
- **Purpose limitation:** troubleshooting data is used only for project support inside this app.
- **Local-only retention:** all project files, notes, embeddings, and logs remain on local workstation.
- **Deletion control:** provide explicit UI actions to delete local project data and knowledge artifacts.
- **Transparency:** document local storage paths and retention behavior in user documentation.
- **No outbound telemetry:** no cloud calls for core functions and no automatic external data transfer.
- **Safety disclaimer:** assistant outputs are advisory and must be validated by qualified engineers.

---

## 4) High-Level Architecture
## 4.1 Frontend (React + TypeScript)
Modules:
- Upload workspace
- Tree explorer (virtualized)
- Node details/edit panel
- Diff preview modal
- Relationship graph view
- AI assistant panel + evidence inspector
- Audit trail panel

## 4.2 Backend (Python + FastAPI)
Services:
- L5X parse service
- Validation/integrity service
- Edit patch service
- Export serialization service
- Relationship extraction service
- Knowledge index service
- Retrieval + answer orchestration service
- Audit log service

## 4.3 Local Storage
- Uploaded project artifacts (workspace)
- Parsed normalized cache
- Knowledge index files
- Audit trail records
- Manual feedback notes

---

## 5) Data Model Contracts (MVP Draft)

## 5.1 Tree Node
```json
{
  "id": "string",
  "name": "string",
  "type": "Controller|Program|Routine|Rung|Tag|AOI|UDT|Other",
  "path": "string",
  "attributes": {},
  "children": []
}
```

## 5.2 Editable Field
```json
{
  "target_path": "string",
  "field_type": "comment|description|note",
  "locale": "en-US|null",
  "original_value": "string",
  "updated_value": "string",
  "validation_state": "valid|warning|error"
}
```

## 5.3 Diff Item
```json
{
  "target_path": "string",
  "field_type": "string",
  "old_value": "string",
  "new_value": "string",
  "change_type": "update"
}
```

## 5.4 Relationship Edge
```json
{
  "source_tag": "string",
  "target_tag": "string",
  "relation_type": "read|write|co_occurrence|cross_program|alias_map|aoi_binding",
  "program": "string|null",
  "routine": "string|null",
  "rung_ref": "string|null"
}
```

## 5.5 Knowledge Chunk
```json
{
  "chunk_id": "string",
  "source_path": "string",
  "scope_type": "routine|rung|tag|aoi|udt|note|other",
  "text": "string",
  "metadata": {},
  "embedding_ref": "string"
}
```

## 5.6 AI Evidence Item
```json
{
  "evidence_id": "string",
  "source_path": "string",
  "program": "string|null",
  "routine": "string|null",
  "rung_ref": "string|null",
  "excerpt": "string",
  "confidence": 0.0
}
```

---

## 6) API Endpoints (MVP)
Base: `/api/v1`

## 6.1 Upload + Parse
- `POST /projects/upload`
  - Input: multipart `.l5x`
  - Output: `{ project_id, revision, validation_summary }`

- `GET /projects/{project_id}/tree`
  - Output: hierarchy tree nodes

## 6.2 Validation
- `GET /projects/{project_id}/validation`
  - Output: list of errors/warnings, blocking flags

## 6.3 Edit Workflow
- `POST /projects/{project_id}/edits`
  - Input: one or more `Editable Field` patches
  - Output: patch results + updated dirty-state

- `GET /projects/{project_id}/diff`
  - Output: array of `Diff Item`

- `GET /projects/{project_id}/audit`
  - Output: audit entries (timestamp, target, old/new, actor)

## 6.4 Export
- `POST /projects/{project_id}/export/precheck`
  - Output: `{ pass: boolean, blockers: [], warnings: [] }`

- `POST /projects/{project_id}/export`
  - Behavior: manual export only
  - Output: downloadable `.L5X`

## 6.5 Relationships
- `GET /projects/{project_id}/relationships`
  - Query: filters for program/routine/tag/relation_type
  - Output: graph nodes + `Relationship Edge[]`

## 6.6 Knowledge + AI
- `POST /projects/{project_id}/knowledge/rebuild`
  - Output: chunk and index summary

- `POST /projects/{project_id}/knowledge/notes`
  - Input: manual issue note
  - Output: stored note + incremental reindex status

- `POST /projects/{project_id}/assistant/ask`
  - Input: `{ question, context_filters? }`
  - Output:
    - If sufficient evidence: answer + evidence list + confidence
    - If insufficient evidence: explicit gap + follow-up questions + missing context hints

---

## 7) Validation & Export Rules
## 7.1 Validation Layers
1. XML well-formedness (UTF-8 support)
2. Expected L5X structure presence (controller/program/routine/tag containers)
3. Editable target existence + field constraints
4. Export integrity checks (required metadata preserved)

## 7.2 Pre-export Gate (must pass)
- No unresolved blocking validation errors
- No invalid edit payload states
- Serializer output passes round-trip parse check

## 7.3 Export Fidelity Requirements
- Preserve element ordering where feasible
- Preserve CDATA/comment blocks where present
- Preserve localized description structures
- Preserve core metadata fields and revision-compatible structure

---

## 8) Relationship Extraction Rules (MVP)
Required relation types:
1. `read`: instruction/rung consumes tag value
2. `write`: instruction/rung assigns/updates tag
3. `co_occurrence`: tags used together in same rung/routine
4. `cross_program`: reference spans program boundaries
5. `alias_map`: alias-to-base mapping
6. `aoi_binding`: AOI parameter/tag bindings

Each edge should include best available source location (`program`, `routine`, `rung_ref`).

---

## 9) AI Assistant Behavior (Strict Evidence)
## 9.1 Answer Policy
- Answer only from retrieved project evidence.
- Provide citation entries for each key claim.
- If evidence is missing/weak, refuse final diagnosis and ask for specific missing context.

## 9.2 Required Output Shape
- `answer`
- `evidence[]`
- `confidence`
- `limitations`
- `follow_up_questions[]` (mandatory when evidence insufficient)

## 9.3 Target UX
- Evidence inspector shows clickable path to source node.
- Rung-level evidence shown when available.
- User can submit manual notes to improve future retrieval.

---

## 10) Non-Functional Requirements
- UI remains responsive for medium files (5–50 MB)
- Tree/graph rendering uses virtualization/batching
- Full app functionality with network disconnected
- Deterministic export outputs from same input + same edit set
- Clear error messaging for validation and export blockers

---

## 11) Testing Strategy
## 11.1 Backend
- Parser tests with v32–v36 samples
- Validation rule tests (positive/negative)
- Edit patch tests (all supported field types)
- Export round-trip tests (parse -> edit -> export -> parse)
- Relationship extraction correctness tests
- Assistant contract tests (citation-required behavior)

## 11.2 Frontend
- Upload + validation feedback flow
- Tree search/expand/detail interactions
- Edit + diff preview flow
- Export precheck blocking behavior
- Relationship graph filtering behavior
- AI panel evidence rendering + insufficient-evidence UX

---

## 12) Acceptance Criteria (MVP)
1. User can upload valid `.L5X` and navigate hierarchy.
2. User can edit supported comments/notes and see diff.
3. Export is blocked on integrity failures and allowed on valid state.
4. Exported `.L5X` reopens successfully in parser (round-trip check pass).
5. Relationship graph displays all required relation categories.
6. AI answers include citations; without evidence, system asks targeted follow-up questions.
7. App runs fully offline with no dependency on external services.

---

## 13) Open Items
- Exact field length/encoding constraints per editable element (to be finalized using additional real samples + Studio behavior validation).
- Workstation minimum hardware profile for guaranteed <15s AI responses.
- Final choice of local embedding/model package based on benchmark during implementation.
