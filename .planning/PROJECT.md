# PROJECT

## 1) Product
- **Name:** app-L5x
- **Type:** app (local web app: frontend + backend)
- **Goal:** Offline-only engineering workspace for Rockwell Studio5000 `.L5X` files.
- **Primary Outcomes (MVP):**
  1. Parse/validate `.L5X` (v32–v36 target)
  2. Explore project hierarchy
  3. Edit approved comment/description fields safely
  4. Show diff + pre-export integrity gate
  5. Export valid edited `.L5X`
  6. Extract and inspect tag relationships

## 2) Constraints
- Local-only processing/storage (no cloud dependency for core flows)
- Deterministic behavior for engineering workflows
- `.L5X` remains source of truth
- Export must be blocked on critical integrity issues

## 3) Scope
### In Scope (MVP)
- Upload + parse + validation report
- Normalized tree model + searchable explorer
- Scoped editing for supported comment/description nodes
- Diff preview + audit-ready change list
- Safe export pre-check and export action
- Relationship extraction and relationship inspection view

### Out of Scope (MVP)
- Cloud sync/inference/storage
- Multi-user collaboration
- Online PLC runtime ingestion
- Predictive analytics beyond grounded evidence

## 4) Architecture (MVP)
- **Backend:** Python FastAPI
  - Parse, validate, edit session, diff, pre-check, export, relationships APIs
- **Frontend:** React + TypeScript
  - Upload, tree explorer, details panel, edit/diff/export UI, relationship view
- **Storage:** Local workspace/session data only

## 5) Data Contracts (Core)
- **TreeNode:** `id`, `name`, `type`, `path`, `attributes`, `children`
- **ValidationIssue:** `code`, `severity`, `message`, `path`, `details`
- **EditableField:** `target_path`, `field_type`, `locale`, `original_value`, `updated_value`, `validation_state`
- **DiffItem:** `target_path`, `field_type`, `old_value`, `new_value`
- **RelationshipEdge:** `source_tag`, `target_tag`, `relation_type`, `program`, `routine`, `rung_ref`, `evidence_excerpt`

## 6) Milestones
- [x] **M1** Project Setup
- [x] **M2** Parser & Validation Foundation
- [x] **M3** Hierarchy Explorer UI
- [x] **M4** Edit, Diff & Safe Export
- [x] **M5** Tag Relationship Intelligence
- [ ] **M6** Offline Knowledge Library + Expert AI
- [ ] **M7** Quality & Release Readiness

## 7) Backlog (Current)
| ID | Task | Priority | Status |
|----|------|----------|--------|
| T-012 | Build local knowledge library (index + retrieval) | High | Planned |
| T-013 | Implement strict-evidence offline AI troubleshooting | High | Planned |
| T-014 | Implement manual note feedback loop for knowledge updates | Medium | Planned |
| T-015 | Add tests and finalize MVP docs | Medium | Planned |

## 8) Acceptance Rules
- Export blocked when critical validation errors exist
- Diff preview must show changed path/field/old/new values
- Relationship view must link to Program/Routine/Rung context when available
- Offline/local constraints must be preserved

## 9) Next Action
- Start **M6**: local knowledge index + strict evidence answer flow
