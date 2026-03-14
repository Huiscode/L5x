# Product Requirements Document (PRD)

## Problem Statement
- PLC L5X projects are large and opaque; engineers lose time navigating tasks, programs, AOIs, and tag usage to understand behavior or change impact.

## Target Users
- Controls engineers maintaining large Logix PLC codebases
- Commissioning and troubleshooting teams
- Automation developers onboarding to existing plants

## Goals
- Provide fast navigation and dependency understanding across tasks, programs, routines, AOIs, and UDTs.
- Enable station-centric reasoning with clear boundaries and impact analysis.
- Make signal tracing and AOI/UDT documentation self-service and fast.
- Offer guided learning walkthroughs for common sequences.

## Non-Goals
- Editing or deploying PLC code in v1
- Replacing RSLogix/Studio 5000 programming features
- Real-time PLC monitoring or online diagnostics

## Core Features (v1)
- Program Navigator + Dependency Map
  - Auto-builds call hierarchy and cross-references for tasks/programs/routines/AOIs/UDTs
  - Click a station tag to filter related logic
- Station-Centric View
  - User-defined station boundaries via name patterns
  - Per-station summaries and “what changes this station” flow (inputs → logic → outputs)
- Signal Trace / I/O Explorer
  - Select a tag to view read/write locations and trace forward/backward across routines
- AOI/UDT Explainer
  - Parse AOIs/UDTs into human-readable docs, list instances, and summarize behavior
- Change Impact Lens
  - Show affected tags/stations and downstream paths for edited routines
- Learning Mode
  - Auto-generated walkthroughs for sequences (start/stop, safety, station cycle)

## Success Metrics
- 50% reduction in time to locate tag usage compared to manual search
- 30% reduction in onboarding time for new engineers
- < 2 minutes to generate full dependency map for a large L5X
- User-reported clarity score ≥ 4/5 on station understanding

## Constraints
- Must handle very large L5X files (hundreds of MB)
- Windows desktop app requirement
- Offline operation preferred; no cloud dependency

## Open Questions
- Should v1 support L5X import only, or also ACD export conversion?
- Minimum supported Studio 5000 version and L5X schema variations?
- Desired export formats for reports (PDF, HTML, CSV)?
- How should learning mode narratives be configured (templates vs. AI summaries)?
