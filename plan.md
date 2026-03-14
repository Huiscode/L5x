# Execution Plan (PLAN)

## Milestones
1. Project discovery and UX wireframes
2. L5X parsing + IR model
3. Dependency graph + station grouping
4. Core UI views (Navigator, Station, Trace)
5. AOI/UDT docs + Impact Lens
6. Learning Mode + export
7. Performance tuning + beta readiness

## Task List
- [ ] Confirm UI stack and packaging (WinUI 3)
- [ ] Define IR schema and graph edges
- [ ] Build streaming L5X parser and entity indexer
- [ ] Implement tag read/write extraction (ladder + ST)
- [ ] Build dependency graph and station grouping
- [ ] Implement Program Navigator + dependency map
- [ ] Implement Station-Centric View with summaries
- [ ] Implement Signal Trace / I/O Explorer
- [ ] Implement AOI/UDT Explainer and usage lists
- [ ] Implement Change Impact Lens
- [ ] Implement Learning Mode walkthrough generator
- [ ] Add export/reporting (if required)
- [ ] Performance profiling and optimizations

## Dependencies
- L5X schema samples for multiple Studio 5000 versions
- Windows App SDK (WinUI 3)

## Acceptance Criteria
- Import and parse a 200MB L5X within 2 minutes on reference machine
- Dependency map is navigable and accurate for tasks/programs/routines/AOIs/UDTs
- Station definitions correctly group logic by naming patterns
- Tag trace shows read/write locations with forward/backward traversal
- AOI/UDT docs generated with instances and summary
- Change Impact Lens highlights affected tags and stations
- Learning Mode can generate at least 3 walkthrough templates
