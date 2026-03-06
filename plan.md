# Project Plan

## Project Overview
- **Project Name:** app-L5x
- **Goal:** Build a company-safe, offline-only local application that uploads Rockwell Studio5000 `.L5X` files, parses/validates them, visualizes structure and tag relationships, supports safe editing of engineering comments/notes, exports valid `.L5X`, and provides strict evidence-based local AI troubleshooting.
- **Start Date:** 2026-03-05
- **Target MVP Date:** TBD

## Product Direction (Updated)
- Offline-only by design: no cloud dependency for core features.
- Keep `.L5X` as source of truth and preserve formatting/order as much as possible during export.
- Build a grounded expert assistant that answers only from program evidence.
- Prioritize workstation usability and deterministic behavior for engineering workflows.

## Confirmed Product Decisions
- **Studio Compatibility Target:** v32–v36
- **App Type:** Local web app (browser UI + local backend)
- **Typical File Size Target:** Medium projects (5–50 MB)
- **Edit Scope (MVP):** Wide scope
  - Tags comments/descriptions
  - Routine comments/descriptions
  - AOI/UDT/program notes where represented in `.L5X`
- **Export Mode:** Manual export to new `.L5X`
- **Relationship Semantics Required:**
  - Read/Write usage
  - Same rung / same routine co-occurrence
  - Cross-program references
  - Alias ↔ base tag mapping
  - AOI I/O bindings
- **AI Answer Mode:** Strict evidence only (citation-required)
- **Offline Model Strategy:** Small local model only
- **Runtime Feedback Update Path:** Manual issue notes in app UI
- **AI Response Target:** < 15 seconds
- **Citation Granularity:** Must include rung-level references when available
- **Security Policy:** Local-only processing and storage (company-safe level)

## Notes from Attached Sample (`CM_RFID_Program.L5X`)
- XML declaration indicates `encoding="UTF-8"`.
- File uses `RSLogix5000Content` with `SoftwareRevision="35.00"` (inside target compatibility range).
- Comments/descriptions are frequently stored in `<![CDATA[...]]>` and may include line breaks and localized blocks (`LocalizedDescription`).
- Export options include decorated/context/dependencies, so serializer must preserve important metadata and structural order.
- Final character-limit/field constraints still TBD and must be validated against additional samples/vendor behavior.

## PM Recommendations (Mandatory in Plan)
1. **Safe Export Pre-check**
   - Validate structure/schema consistency before enabling export.
   - Block export if critical integrity issues are detected.
2. **Diff Preview Before Export**
   - Show a clear list of changed elements (path, field, old value, new value).
3. **Evidence Inspector in AI Panel**
   - Show exact source references for every answer (Program/Routine/Rung/Tag path).
4. **Uncertainty Behavior**
   - If evidence is insufficient, assistant responds with explicit gap statement and asks targeted follow-up questions.
5. **Change Audit Trail**
   - Track each edit (timestamp, target path, old/new values, action source).
6. **Performance Guardrails**
   - Virtualized rendering and batching limits for tree/graph views.

## Execution Defaults (PM Baseline - Approved)
- **Primary hierarchy UI:** Indented tree explorer as default; graph/treemap views are secondary tabs.
- **Offline AI stack (MVP recommendation):**
  - Local embeddings: `bge-small-en-v1.5` (CPU friendly)
  - Local vector store: `FAISS`
  - Local LLM: `Llama 3.2 3B Instruct` via local runtime (small model class)
- **Workstation baseline target:** 16 GB RAM, 4+ cores, SSD, Windows 10/11; lower specs may degrade response times.
- **Import policy:** Hybrid strict mode:
  - Block on critical XML/schema corruption
  - Allow partial read with warnings for non-critical unsupported blocks
- **Audit policy:** Local user profile required (`display_name`), immutable audit entries, exportable audit report (CSV/JSON).
- **Insufficient evidence response policy:**
  - Must state: `Insufficient evidence in current project knowledge.`
  - Must ask 2-5 targeted follow-up questions.
  - Must list missing context hints (tag/routine/rung/runtime symptom).
- **Pilot-ready gate:**
  - Test with at least 10 real L5X files across v32–v36
  - >=95% parse success on target sample set
  - 100% export round-trip pass for edited files in test set
  - 0 critical security-local violations

## Scope (MVP)
### In Scope
- Repository structure for frontend + backend
- Local run workflow for development and testing
- L5X parsing into normalized tree JSON + editable model
- Validation for malformed/unsupported L5X input
- Interactive hierarchy explorer (tree map/tree explorer) with search and details panel
- Scoped editing of comments/notes in supported elements
- Safe manual export of modified `.L5X`
- Diff preview and export integrity pre-check
- Interactive tag relationship graph with required semantics
- Local knowledge library (RAG-like index) for program understanding
- Offline strict-evidence AI troubleshooting assistant with citation inspector
- Manual feedback notes workflow to improve retrieval quality
- Basic automated tests for parser, edit/export, relationship extraction, and AI evidence flow

### Out of Scope (for now)
- Any cloud sync/inference/storage
- Multi-user collaboration
- Automatic online PLC data ingestion
- Advanced predictive analytics beyond grounded troubleshooting
- Formal digital signing of exported `.L5X` (future phase)

## Architecture (MVP)
- **Backend:** Python `FastAPI`
  - Upload + parse endpoints
  - Validation and integrity-check engine
  - Edit patch engine for scoped fields
  - Export builder (manual trigger)
  - Relationship extraction engine
  - Knowledge indexing + retrieval services
  - Strict evidence answer orchestration (local model)
- **Frontend:** React + TypeScript
  - Drag/drop upload + validation feedback
  - Tree explorer + search/filter + node details
  - Comment/note editing UI
  - Diff preview + export workflow
  - Relationship graph view with filters and drill-down
  - AI panel with evidence inspector and follow-up prompts
- **Local Storage:**
  - Project workspace cache
  - Knowledge index store
  - Audit trail and manual note records
- **Security Constraints:**
  - No external API calls for core app functions
  - Local file-only data retention
  - Explicit user-controlled import/export actions

## Data Contracts (Draft)
- **Tree Node:** `id`, `name`, `type`, `path`, `attributes`, `children`
- **Editable Field:** `target_path`, `field_type`, `locale`, `original_value`, `updated_value`, `validation_state`
- **Relationship Edge:** `source_tag`, `target_tag`, `relation_type`, `program`, `routine`, `rung_ref`
- **Knowledge Chunk:** `chunk_id`, `source_path`, `scope_type`, `text`, `metadata`, `embedding_ref`
- **AI Evidence Item:** `evidence_id`, `source_path`, `program`, `routine`, `rung_ref`, `excerpt`, `confidence`

## Milestones
- [ ] **M1: Project Setup**
  - [ ] Define architecture and folder structure
  - [ ] Configure tooling (lint/format/build/test)
  - [ ] Confirm local run instructions and offline constraints

- [ ] **M2: Parser & Validation Foundation**
  - [ ] Implement core L5X parser for v32–v36 target
  - [ ] Define normalized schema and mapping
  - [ ] Add validation + integrity rules

- [ ] **M3: Hierarchy Explorer UI**
  - [ ] Implement upload flow (drag/drop)
  - [ ] Implement searchable expandable tree
  - [ ] Implement node details panel + performance guardrails

- [ ] **M4: Edit, Diff & Safe Export**
  - [ ] Implement wide-scope comment/note editing
  - [ ] Implement diff preview and audit trail
  - [ ] Implement manual export with pre-check gate

- [ ] **M5: Tag Relationship Intelligence**
  - [ ] Build relationship extraction for required semantics
  - [ ] Build interactive graph visualization and filters
  - [ ] Link graph evidence back to rung/routine/program context

- [ ] **M6: Offline Knowledge Library + Expert AI**
  - [ ] Build local index from program structure + logic context
  - [ ] Implement strict evidence Q&A orchestration (<15s target)
  - [ ] Implement insufficient-evidence prompting behavior
  - [ ] Implement manual feedback note update flow

- [ ] **M7: Quality & Release Readiness**
  - [ ] Add regression tests for parser/edit/export/AI evidence chain
  - [ ] Validate security-local requirements and offline operation
  - [ ] Finalize docs, limitations, and MVP release checklist

## Work Breakdown (Task Backlog)
| ID | Task | Priority | Owner | Estimate | Status |
|----|------|----------|-------|----------|--------|
| T-001 | Initialize frontend/backend project structure | High | TBD | 0.5d | Planned |
| T-002 | Add baseline tooling (lint, format, test, run scripts) | High | TBD | 0.5d | Planned |
| T-003 | Implement v32–v36 parser and normalized node schema | High | TBD | 1-2d | Planned |
| T-004 | Implement validation + integrity checks | High | TBD | 0.5-1d | Planned |
| T-005 | Build hierarchy explorer UI (upload/search/expand/details) | High | TBD | 1-2d | Planned |
| T-006 | Implement wide-scope comment/note editing workflow | High | TBD | 1-2d | Planned |
| T-007 | Implement diff preview + change audit trail | High | TBD | 1d | Planned |
| T-008 | Implement safe manual `.L5X` export gate | High | TBD | 1d | Planned |
| T-009 | Implement tag relationship extraction engine | High | TBD | 1-2d | Planned |
| T-010 | Build interactive relationship graph UI | High | TBD | 1-2d | Planned |
| T-011 | Build local knowledge library (index + retrieval) | High | TBD | 1-2d | Planned |
| T-012 | Implement strict-evidence offline AI troubleshooting | High | TBD | 1-2d | Planned |
| T-013 | Implement manual note feedback loop for knowledge updates | Medium | TBD | 0.5-1d | Planned |
| T-014 | Add tests and finalize MVP docs | Medium | TBD | 1d | Planned |

## Risks & Mitigations
- **Risk:** L5X structure variance across projects and versions
  **Mitigation:** Version-aware parsing rules and broad sample regression tests.
- **Risk:** Export corruption after edits
  **Mitigation:** Pre-export integrity gate + round-trip validation + diff preview.
- **Risk:** Dense graph complexity impacts usability/performance
  **Mitigation:** Filtering, clustering/grouping, incremental rendering.
- **Risk:** Offline AI answers become speculative
  **Mitigation:** Strict citation-required policy and insufficient-evidence fallback.
- **Risk:** Unknown field size/encoding constraints for all editable elements
  **Mitigation:** Progressive rule discovery from additional samples and validation limits.

## Compliance & Safety Boundaries
- **GDPR/Data Protection:**
  - Process only data necessary for app function (data minimization).
  - Keep all processing/storage local by default.
  - Provide user controls for deleting local projects, notes, and indexes.
  - Keep audit logs for engineering traceability while avoiding unnecessary personal data.
- **Security Baseline:**
  - No outbound network calls for core app features.
  - Explicit import/export actions only.
  - Document local data locations and retention behavior.
- **Functional Safety Positioning:**
  - app-L5x is a decision-support engineering tool, not a certified safety controller.
  - AI troubleshooting outputs are advisory and must be validated by qualified engineers before operational changes.
  - Add product disclaimer in UI and documentation.

## Definition of Done (DoD)
A task is considered done when:
- Code is implemented and reviewed
- Lint/tests pass (where applicable)
- Offline/local constraints are respected
- Documentation updated
- `status.md` is updated with result marked as **Done** or **Completed**

## Update Rules
- Keep this file focused on plan and roadmap.
- Update milestone/task statuses at least once per completed work session.
- Log completion details in `status.md` immediately after finishing each task.
