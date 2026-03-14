# Technical Specification (SPEC)

## Architecture Overview
- Windows desktop app (WPF or WinUI 3) with a local analysis engine.
- Ingestion pipeline: L5X parser → normalized IR (intermediate representation) → graph index.
- Core services:
  - Project Indexer: tasks/programs/routines/AOIs/UDTs/tags
  - Dependency Graph Builder: call hierarchy, read/write edges, station groupings
  - Trace Engine: forward/backward tag traversal
  - Doc Generator: AOI/UDT summaries and learning mode narratives
- UI modules: Navigator, Station View, Trace Explorer, AOI/UDT docs, Impact Lens, Learning Mode.

## Key Flows
- Import L5X → parse XML → build IR → index entities → build graphs → render navigator.
- Station definition: user provides naming patterns → station groups computed → summaries built.
- Tag trace: select tag → compute read/write locations → traverse graph forward/backward.
- Change impact: select routine or AOI → compute affected tags → downstream station map.
- Learning mode: choose template → gather key routines + tags → generate walkthrough.

## Data Models / Schemas
- Project
  - Tasks, Programs, Routines, AOIs, UDTs, Tags
- Routine
  - Name, Type, LogicText, ReadTags[], WriteTags[], CalledAOIs[], CalledRoutines[]
- TagRef
  - TagName, Direction(Read/Write), Location(Routine/Line)
- Graph
  - Nodes: Task/Program/Routine/AOI/UDT/Tag/Station
  - Edges: Calls, Reads, Writes, Contains, BelongsToStation
- Station
  - Name, PatternRules[], Routines[], TagsIn[], TagsOut[]

## APIs / Endpoints
- Local service interfaces (in-process), no external endpoints in v1.
- Optional: export endpoints for HTML/PDF/CSV if requested.

## Dependencies
- XML parsing library (e.g., System.Xml or fast SAX-style parser for huge files)
- Graph library for traversal (custom adjacency lists or QuickGraph)
- UI toolkit (WPF + MVVM or WinUI 3)

## Security / Compliance
- Offline local processing; no data leaves workstation.
- Support redaction of tag names for export if needed.

## Risk Areas
- Performance on very large L5X files
- L5X schema variability between Studio 5000 versions
- Accurate read/write detection in complex ladder/structured text

## Open Questions
- UI stack preference (WPF vs WinUI 3)?
- Should learning mode use deterministic templates or optional AI summaries?
- Do we need incremental re-indexing when L5X changes?
